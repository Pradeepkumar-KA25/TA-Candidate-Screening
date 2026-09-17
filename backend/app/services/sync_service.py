from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
from uuid import UUID

from app.core.crypto import decrypt_value, encrypt_value
from app.core.config import settings
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient, ZohoRecruitClientError, ZohoRecruitPermanentError
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.normalization_service import NormalizationService
from app.schemas.sync import (
    CandidateSyncHistoryItemResponse,
    CandidateSyncHistoryResponse,
    CandidateSyncStatusResponse,
    CandidateSyncSummaryResponse,
    CandidateSyncTriggerResponse,
    NormalizationExampleResponse,
)


class SyncError(Exception):
    status_code = 400
    code = "SYNC_ERROR"
    detail = "Sync request could not be processed"


class SyncConflictError(SyncError):
    status_code = 409
    code = "SYNC_ALREADY_RUNNING"
    detail = "A candidate sync is already running"


class SyncNotFoundError(SyncError):
    status_code = 404
    code = "SYNC_NOT_FOUND"
    detail = "Sync operation not found"


@dataclass(slots=True)
class SyncService:
    sync_log_repository: SyncLogRepository
    candidate_repository: CandidateRepository
    integration_repository: IntegrationSettingsRepository
    activity_log_repository: ActivityLogRepository
    duplicate_detection_service: DuplicateDetectionService
    normalization_service: NormalizationService
    zoho_oauth_client: ZohoOAuthClient
    zoho_recruit_client: ZohoRecruitClient

    provider_name: str = "zoho_recruit"
    progress_commit_interval: int = 200
    max_normalization_examples: int = 12
    stale_sync_timeout: timedelta = timedelta(hours=2)

    def _rollback_session(self) -> None:
        try:
            self.candidate_repository.session.rollback()
        except Exception:
            # Best-effort rollback to recover from flush/commit failures.
            pass

    def start_sync(self, recruiter_id: UUID) -> CandidateSyncTriggerResponse:
        stale_before = datetime.now(UTC) - self.stale_sync_timeout
        self.sync_log_repository.mark_stale_running_syncs_failed(
            started_before=stale_before,
            reason="automatic reset: stale running sync",
        )

        if self.sync_log_repository.has_running_sync():
            raise SyncConflictError()

        sync_log = self.sync_log_repository.create_running(triggered_by=recruiter_id)
        self.activity_log_repository.create(
            actor_id=recruiter_id,
            action_type="sync_started",
            description=f"Candidate sync started (sync_id={sync_log.id})",
        )
        return CandidateSyncTriggerResponse(sync_id=sync_log.id, status=sync_log.status)

    def run_sync(self, sync_id: UUID) -> None:
        sync_log = self.sync_log_repository.get_by_id(sync_id)
        if sync_log is None:
            raise SyncNotFoundError()

        integration = self.integration_repository.get_or_create(self.provider_name)

        fetched = 0
        created = 0
        updated = 0
        failed = 0
        normalized_records = 0
        normalization_examples: list[dict] = []

        try:
            access_token = self._resolve_valid_access_token(integration)
            max_records = max(1, settings.zoho_sync_max_records)
            current_page = max(1, integration.next_candidate_sync_page)
            has_more_records = True

            while created < max_records and has_more_records:
                page_size = 200
                candidate_page = self.zoho_recruit_client.fetch_candidates_page(
                    access_token=access_token,
                    page=current_page,
                    per_page=page_size,
                )
                has_more_records = candidate_page.has_more

                for raw_candidate in candidate_page.candidates:
                    fetched += 1
                    validation_error = self._validate_candidate_payload(raw_candidate)
                    if validation_error is not None:
                        failed += 1
                        self.activity_log_repository.create(
                            actor_id=sync_log.triggered_by,
                            action_type="sync_candidate_skipped",
                            description=(
                                f"Candidate skipped during sync (sync_id={sync_id}): {validation_error}; "
                                f"candidate_id={raw_candidate.get('id')!r}"
                            ),
                        )
                        continue

                    normalized = self._normalize_candidate(raw_candidate)
                    normalized_records += self._count_normalization_changes(raw_candidate, normalized)
                    normalization_examples = self._merge_normalization_examples(
                        current=normalization_examples,
                        discovered=self._extract_normalization_examples(raw_candidate, normalized),
                    )
                    existing = self.candidate_repository.find_existing_by_zoho_ids(
                        normalized["zoho_record_id"],
                        normalized.get("zoho_candidate_id"),
                    )
                    if existing is not None:
                        continue

                    self.candidate_repository.create_or_update(normalized, commit=False)
                    created += 1

                    if fetched % self.progress_commit_interval == 0:
                        self.sync_log_repository.mark_running_progress(
                            sync_id=sync_id,
                            records_fetched=fetched,
                            records_new=created,
                            records_updated=updated,
                            normalized_records=normalized_records,
                            normalization_examples=normalization_examples,
                        )

                    if created >= max_records:
                        break

                if created >= max_records or not candidate_page.candidates:
                    break

                current_page += 1

            if fetched and fetched % self.progress_commit_interval != 0:
                self.sync_log_repository.mark_running_progress(
                    sync_id=sync_id,
                    records_fetched=fetched,
                    records_new=created,
                    records_updated=updated,
                    normalized_records=normalized_records,
                    normalization_examples=normalization_examples,
                )

            duplicate_matches = 0
            try:
                duplicate_result = self.duplicate_detection_service.detect()
                duplicate_matches = duplicate_result.potential_duplicates
                self.activity_log_repository.create(
                    actor_id=sync_log.triggered_by,
                    action_type="duplicate_detection_completed",
                    description=(
                        "Duplicate detection completed "
                        f"(sync_id={sync_id}, scanned={duplicate_result.scanned}, "
                        f"potential={duplicate_result.potential_duplicates}, "
                        f"created={duplicate_result.created}, updated={duplicate_result.updated})"
                    ),
                )
            except Exception as exc:
                # Duplicate detection should not mark an otherwise successful sync as failed.
                self.activity_log_repository.create(
                    actor_id=sync_log.triggered_by,
                    action_type="duplicate_detection_failed",
                    description=f"Duplicate detection failed after sync (sync_id={sync_id}): {exc}",
                )

            self.sync_log_repository.set_outcome_counts(
                sync_id=sync_id,
                records_failed=failed,
                duplicate_matches=duplicate_matches,
            )
            completed_log = self.sync_log_repository.mark_completed(
                sync_id=sync_id,
                records_fetched=fetched,
                records_new=created,
                records_updated=updated,
                normalized_records=normalized_records,
                normalization_examples=normalization_examples,
            )
            integration.last_successful_sync_at = completed_log.completed_at
            integration.last_error = None
            integration.status = "healthy"
            integration.connection_state = "connected"
            integration.last_checked_at = datetime.now(UTC)
            integration.next_candidate_sync_page = current_page + 1 if has_more_records else 1
            self.integration_repository.save(integration)

            self.activity_log_repository.create(
                actor_id=sync_log.triggered_by,
                action_type="sync_completed",
                description=(
                    f"Candidate sync completed (sync_id={sync_id}, fetched={fetched}, "
                    f"new={created}, updated={updated})"
                ),
            )
        except SyncError as exc:
            self._rollback_session()
            self.sync_log_repository.mark_failed(sync_id=sync_id, error_message=exc.detail)
            self.activity_log_repository.create(
                actor_id=sync_log.triggered_by,
                action_type="sync_failed",
                description=f"Candidate sync failed (sync_id={sync_id}): {exc.detail}",
            )
            raise
        except ZohoRecruitClientError as exc:
            self._rollback_session()
            self.sync_log_repository.mark_failed(sync_id=sync_id, error_message=str(exc))
            integration.last_error = str(exc)
            integration.status = "sync_failed"
            integration.connection_state = "disconnected"
            integration.last_checked_at = datetime.now(UTC)
            self.integration_repository.save(integration)
            self.activity_log_repository.create(
                actor_id=sync_log.triggered_by,
                action_type="sync_failed",
                description=f"Candidate sync failed (sync_id={sync_id}): {exc}",
            )
        except Exception as exc:
            self._rollback_session()
            self.sync_log_repository.mark_failed(sync_id=sync_id, error_message="Internal sync error")
            integration.last_error = str(exc)
            integration.status = "sync_failed"
            integration.connection_state = "disconnected"
            integration.last_checked_at = datetime.now(UTC)
            self.integration_repository.save(integration)
            self.activity_log_repository.create(
                actor_id=sync_log.triggered_by,
                action_type="sync_failed",
                description=f"Candidate sync failed (sync_id={sync_id}): {exc}",
            )

    def get_sync_status(self, sync_id: UUID) -> CandidateSyncStatusResponse:
        sync_log = self.sync_log_repository.get_by_id(sync_id)
        if sync_log is None:
            raise SyncNotFoundError()

        return CandidateSyncStatusResponse(
            sync_id=sync_log.id,
            status=sync_log.status,
            started_at=sync_log.started_at,
            completed_at=sync_log.completed_at,
            records_fetched=sync_log.records_fetched,
            records_new=sync_log.records_new,
            records_updated=sync_log.records_updated,
            records_failed=sync_log.records_failed,
            duplicate_matches=sync_log.duplicate_matches,
            error_message=sync_log.error_message,
        )

    def get_sync_summary(self, sync_id: UUID) -> CandidateSyncSummaryResponse:
        sync_log = self.sync_log_repository.get_by_id(sync_id)
        if sync_log is None:
            raise SyncNotFoundError()

        examples = sync_log.normalization_examples or []
        summary_examples = [
            NormalizationExampleResponse(
                field=str(item.get("field") or ""),
                raw_value=str(item.get("raw_value") or ""),
                normalized_value=str(item.get("normalized_value") or ""),
            )
            for item in examples
            if isinstance(item, dict)
            and item.get("field")
            and item.get("raw_value")
            and item.get("normalized_value")
        ]

        return CandidateSyncSummaryResponse(
            sync_id=sync_log.id,
            status=sync_log.status,
            started_at=sync_log.started_at,
            completed_at=sync_log.completed_at,
            records_fetched=sync_log.records_fetched,
            records_new=sync_log.records_new,
            records_updated=sync_log.records_updated,
            records_failed=sync_log.records_failed,
            duplicate_matches=sync_log.duplicate_matches,
            normalized_records=sync_log.normalized_records,
            normalization_examples=summary_examples,
            error_message=sync_log.error_message,
        )

    def get_sync_history(self, recruiter_id: UUID, limit: int = 8) -> CandidateSyncHistoryResponse:
        return CandidateSyncHistoryResponse(
            items=[
                CandidateSyncHistoryItemResponse(
                    sync_id=log.id,
                    status=log.status,
                    started_at=log.started_at,
                    completed_at=log.completed_at,
                    records_fetched=log.records_fetched,
                    records_new=log.records_new,
                    records_updated=log.records_updated,
                    records_failed=log.records_failed,
                    duplicate_matches=log.duplicate_matches,
                    error_message=log.error_message,
                )
                for log in self.sync_log_repository.list_for_user(recruiter_id, limit)
            ]
        )

    def run_auto_sync(self) -> UUID | None:
        """Run automatic sync if conditions are met.
        
        Returns:
            Sync ID if auto-sync was triggered, None otherwise.
        """
        integration = self.integration_repository.get_or_create(self.provider_name)
        
        # Check if auto-sync is enabled
        if not integration.auto_sync_enabled:
            return None
        
        # Check if enough time has passed since last auto-sync
        now = datetime.now(UTC)
        if integration.last_auto_sync_at is not None:
            time_since_last_sync = (now - self._as_utc(integration.last_auto_sync_at)).total_seconds() / 60
            if time_since_last_sync < integration.auto_sync_interval_minutes:
                return None
        
        # Check if a sync is already running
        if self.sync_log_repository.has_running_sync():
            return None
        
        # Create system auto-sync (use None for actor_id on system-triggered syncs)
        try:
            sync_log = self.sync_log_repository.create_running(triggered_by=None)
            integration.last_auto_sync_at = now
            self.integration_repository.save(integration)
            
            self.activity_log_repository.create(
                actor_id=None,
                action_type="sync_started",
                description=f"Automatic candidate sync started (sync_id={sync_log.id})",
            )
            return sync_log.id
        except SyncConflictError:
            # Another sync is already running
            return None

    def _resolve_valid_access_token(self, integration) -> str:
        access_token = decrypt_value(integration.access_token_encrypted)
        refresh_token = decrypt_value(integration.refresh_token_encrypted)
        now = datetime.now(UTC)

        token_expired = integration.token_expires_at is not None and self._as_utc(integration.token_expires_at) <= now

        if access_token and not token_expired:
            return access_token

        if not refresh_token:
            raise ZohoRecruitPermanentError("Zoho refresh token is not configured")

        refreshed = self.zoho_oauth_client.refresh_access_token(refresh_token)
        if refreshed is None:
            raise ZohoRecruitPermanentError("Zoho access token refresh failed")

        integration.access_token_encrypted = encrypt_value(refreshed.access_token)
        integration.token_expires_at = now + timedelta(seconds=refreshed.expires_in)
        if refreshed.scope:
            integration.scope = refreshed.scope
        integration.last_checked_at = now
        integration.connection_state = "connected"
        integration.status = "healthy"
        integration.last_error = None
        self.integration_repository.save(integration)

        return refreshed.access_token

    @staticmethod
    def _as_utc(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)
        return timestamp.astimezone(UTC)

    def _normalize_candidate(self, raw_candidate: dict) -> dict:
        zoho_record_id = str(raw_candidate.get("id")).strip()
        zoho_candidate_id = self._extract_first_from_keys(raw_candidate, "Candidate_ID", "Candidate_Id")
        full_name = self._join_name_parts(raw_candidate)
        email = self._extract_first(raw_candidate.get("Email"))
        phone = self._extract_first(raw_candidate.get("Phone"))
        current_location = self.normalization_service.normalize_location(
            self._resolve_current_location(raw_candidate)
        )
        preferred_location = self.normalization_service.normalize_location(
            self._extract_first_from_keys(
                raw_candidate,
                "Preferred_Location",
                "Preferred_Work_Location",
            )
        )
        degree = self._extract_first_from_keys(
            raw_candidate,
            "Highest_Qualification",
            "Highest_Qualification_Held",
        )
        normalized_degree = self.normalization_service.normalize_degree(degree) if degree is not None else None
        notice_period_raw = self._extract_first(raw_candidate.get("Notice_Period"))
        notice_period = self.normalization_service.normalize_notice_period(notice_period_raw)
        skills_raw = raw_candidate.get("Skill_Set") or raw_candidate.get("Skills")

        skills: list[str] | None = None
        if isinstance(skills_raw, str):
            skills = [
                self.normalization_service.normalize_skill(item)
                for item in skills_raw.split(",")
                if item.strip()
            ]
        elif isinstance(skills_raw, list):
            skills = [
                self.normalization_service.normalize_skill(str(item))
                for item in skills_raw
                if str(item).strip()
            ]

        current_ctc = self._resolve_salary_value(
            raw_candidate,
            explicit_keys=("Current_Salary", "Current_CTC", "CurrentCTC", "CTC"),
            combined_keys=("Current_CTC_Expected_CTC", "Current_Expected_CTC", "CTC_Details"),
            pair_index=0,
        )
        expected_ctc = self._resolve_salary_value(
            raw_candidate,
            explicit_keys=("Expected_Salary", "Expected_CTC", "ExpectedCTC"),
            combined_keys=("Current_CTC_Expected_CTC", "Current_Expected_CTC", "CTC_Details"),
            pair_index=1,
        )

        return {
            "zoho_record_id": zoho_record_id,
            "zoho_candidate_id": zoho_candidate_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "total_experience_years": self._as_float(
                self._first_value_from_keys(
                    raw_candidate,
                    "Experience_in_Years",
                    "Experience_in_Yrs",
                    "Overall_IT_Experince",
                )
            ),
            "relevant_experience_years": self._as_float(
                self._first_value_from_keys(
                    raw_candidate,
                    "Relevant_Experience",
                    "Relevant_Exp",
                )
            ),
            "current_company": self._extract_first_from_keys(
                raw_candidate,
                "Current_Employer",
                "Employer_Details",
            ),
            "current_location": current_location,
            "preferred_location": preferred_location,
            "notice_period_days": self._as_int(notice_period),
            "skills": skills,
            "degree": degree,
            "normalized_degree": normalized_degree,
            "current_ctc": current_ctc,
            "expected_ctc": expected_ctc,
            "status": self._extract_first_from_keys(raw_candidate, "Candidate_Status", "Status"),
            "match_metadata": {"synced_at": datetime.now(UTC).isoformat()},
            "source": self._extract_first_from_keys(
                raw_candidate,
                "Source",
                "Candidate_Source",
                "Source_of_Candidate",
                "Lead_Source",
            ),
            "raw_payload": raw_candidate,
        }

    def _extract_normalization_examples(self, raw_candidate: dict, normalized_payload: dict) -> list[dict]:
        examples: list[dict] = []

        def add_example(field: str, raw_value: str | None, normalized_value: str | None) -> None:
            if raw_value is None or normalized_value is None:
                return
            if raw_value.strip() == normalized_value.strip():
                return
            examples.append(
                {
                    "field": field,
                    "raw_value": raw_value.strip(),
                    "normalized_value": normalized_value.strip(),
                }
            )

        add_example(
            "current_location",
            self._resolve_current_location(raw_candidate),
            normalized_payload.get("current_location"),
        )
        add_example(
            "preferred_location",
            self._extract_first_from_keys(raw_candidate, "Preferred_Location", "Preferred_Work_Location"),
            normalized_payload.get("preferred_location"),
        )
        add_example(
            "degree",
            self._extract_first_from_keys(raw_candidate, "Highest_Qualification", "Highest_Qualification_Held"),
            normalized_payload.get("normalized_degree"),
        )
        add_example(
            "notice_period",
            self._extract_first(raw_candidate.get("Notice_Period")),
            self._format_notice_period(normalized_payload.get("notice_period_days")),
        )

        raw_skills = self._extract_skills(raw_candidate)
        normalized_skills = normalized_payload.get("skills")
        if isinstance(normalized_skills, list):
            for index, raw_skill in enumerate(raw_skills):
                if index >= len(normalized_skills):
                    break
                normalized_skill = str(normalized_skills[index]).strip()
                add_example("skill", raw_skill, normalized_skill)

        return examples

    def _count_normalization_changes(self, raw_candidate: dict, normalized_payload: dict) -> int:
        return len(self._extract_normalization_examples(raw_candidate, normalized_payload))

    def _merge_normalization_examples(self, *, current: list[dict], discovered: list[dict]) -> list[dict]:
        merged = [*current]
        seen = {
            (str(item.get("field")), str(item.get("raw_value")), str(item.get("normalized_value")))
            for item in merged
            if isinstance(item, dict)
        }

        for item in discovered:
            key = (str(item.get("field")), str(item.get("raw_value")), str(item.get("normalized_value")))
            if key in seen:
                continue
            merged.append(item)
            seen.add(key)
            if len(merged) >= self.max_normalization_examples:
                break

        return merged

    @staticmethod
    def _extract_skills(raw_candidate: dict) -> list[str]:
        skills_raw = raw_candidate.get("Skill_Set") or raw_candidate.get("Skills")
        if isinstance(skills_raw, str):
            return [item.strip() for item in skills_raw.split(",") if item.strip()]
        if isinstance(skills_raw, list):
            return [str(item).strip() for item in skills_raw if str(item).strip()]
        return []

    @staticmethod
    def _format_notice_period(value: int | None) -> str | None:
        if value is None:
            return None
        return f"{value} Days"

    def _validate_candidate_payload(self, raw_candidate: dict) -> str | None:
        zoho_record_id = raw_candidate.get("id")
        if not isinstance(zoho_record_id, str) or not zoho_record_id.strip():
            return "missing required field: id"

        full_name = self._join_name_parts(raw_candidate)
        if full_name == "Unknown Candidate":
            return "missing required field: candidate name"

        email = self._extract_first(raw_candidate.get("Email"))
        phone = self._extract_first(raw_candidate.get("Phone"))
        if email is None and phone is None:
            return "missing required contact method: email or phone"

        return None

    @staticmethod
    def _extract_first(value):
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        if isinstance(value, list) and value:
            first = str(value[0]).strip()
            return first or None
        return None

    @classmethod
    def _extract_first_from_keys(cls, raw_candidate: dict, *keys: str) -> str | None:
        for key in keys:
            value = cls._extract_first(raw_candidate.get(key))
            if value is not None:
                return value
        return None

    @staticmethod
    def _first_value_from_keys(raw_candidate: dict, *keys: str):
        for key in keys:
            value = raw_candidate.get(key)
            if value not in (None, "", [], {}):
                return value
        return None

    @classmethod
    def _resolve_current_location(cls, raw_candidate: dict) -> str | None:
        explicit_location = cls._extract_first_from_keys(
            raw_candidate,
            "Current_Location",
            "Current_Work_Location",
            "Current_Location_of_Candidate_KANINI_Work_Locati",
        )
        if explicit_location is not None:
            return explicit_location

        parts = [
            cls._extract_first(raw_candidate.get("City")),
            cls._extract_first(raw_candidate.get("State")),
            cls._extract_first(raw_candidate.get("Country")),
        ]
        location = ", ".join(part for part in parts if part)
        return location or None

    @classmethod
    def _resolve_salary_value(
        cls,
        raw_candidate: dict,
        *,
        explicit_keys: tuple[str, ...],
        combined_keys: tuple[str, ...],
        pair_index: int,
    ) -> float | None:
        explicit_value = cls._first_value_from_keys(raw_candidate, *explicit_keys)
        parsed_explicit = cls._as_float(explicit_value)
        if parsed_explicit is not None:
            return parsed_explicit

        combined_value = cls._first_value_from_keys(raw_candidate, *combined_keys)
        if combined_value is None:
            return None

        return cls._extract_salary_from_combined_value(combined_value, pair_index)

    @classmethod
    def _extract_salary_from_combined_value(cls, value, pair_index: int) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        number_matches = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
        if not number_matches:
            return None

        if pair_index < len(number_matches):
            return cls._as_float(number_matches[pair_index])

        if len(number_matches) == 1:
            return cls._as_float(number_matches[0])

        return None

    @staticmethod
    def _as_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value) -> int | None:
        if value is None:
            return None
        text = str(value).strip().lower().replace("days", "").replace("day", "")
        try:
            parsed = int(float(text))
            # Notice period is expected in days; reject unrealistic values (often phone-number noise from source mapping).
            if parsed < 0 or parsed > 3650:
                return None
            return parsed
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_degree(value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @staticmethod
    def _join_name_parts(raw_candidate: dict) -> str:
        full_name = raw_candidate.get("Full_Name")
        if isinstance(full_name, str) and full_name.strip():
            return full_name.strip()

        first_name = raw_candidate.get("First_Name")
        last_name = raw_candidate.get("Last_Name")
        parts = [part.strip() for part in [str(first_name or ""), str(last_name or "")] if part and str(part).strip()]
        if parts:
            return " ".join(parts)

        return "Unknown Candidate"
