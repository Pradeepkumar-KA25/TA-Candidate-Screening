from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.models.candidate import Candidate
from app.models.candidate_review import CandidateReview
from app.models.review_batch import ReviewBatch
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_sync_ledger_repository import CandidateSyncLedgerRepository
from app.repositories.candidate_review_repository import CandidateReviewRepository
from app.repositories.proposed_field_change_repository import ProposedFieldChangeRepository
from app.repositories.review_batch_repository import ReviewBatchRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.zoho_field_metadata_repository import ZohoFieldMetadataRepository
from app.services.resume_fetch_service import ResumeFetchService
from app.services.integration_service import IntegrationService
from app.services.zoho_candidate_version import candidate_payload_hash, parse_zoho_modified_time

logger = logging.getLogger("resume_enrichment")


class ResumeEnrichmentError(Exception):
    """Base exception for resume enrichment errors."""

    pass


class ResumeEnrichmentWriteBackDisabledError(ResumeEnrichmentError):
    """Raised when a write-back operation is requested while writes are disabled."""

    pass


class ResumeEnrichmentService:
    """Service for Phase 1: Resume extraction, comparison, and review batch management."""

    # Resume sources are stable; Zoho field names are resolved from each raw payload.
    RESUME_FIELD_MAPPING = {
        "email": ("contact.email", "Email Address", ("Email", "Email_Optional")),
        "phone": ("contact.phone", "Phone Number", ("Phone", "Mobile")),
        "designation": (
            "experience[0].title",
            "Designation / Job Title",
            ("Designation", "Job_Title_as_per_KANINI", "Job_Title_as_per_Kanini_Function", "Job_Role_as_per_Kanini", "Final_Job_Role"),
        ),
        "current_company": (
            "experience[0].company",
            "Current Company",
            ("Current_Employer", "Employer_Details", "Current_Company"),
        ),
        "degree": (
            "education[0].degree",
            "Degree",
            ("Highest_Qualification", "Highest_Qualification_Held", "Degree", "Education"),
        ),
        "institution": (
            "education[0].institution",
            "Institution / University",
            ("Institution", "University", "Institute"),
        ),
        "skills": ("skills", "Technical Skills", ("Skill_Set", "Skills")),
        "summary": (
            "summary",
            "Professional Summary",
            ("Summary", "Professional_Summary", "Profile_Summary"),
        ),
    }

    def __init__(
        self,
        review_batch_repository: ReviewBatchRepository,
        candidate_review_repository: CandidateReviewRepository,
        proposed_field_change_repository: ProposedFieldChangeRepository,
        candidate_repository: CandidateRepository,
        zoho_recruit_client: ZohoRecruitClient,
        resume_fetch_service: ResumeFetchService,
        activity_log_repository: ActivityLogRepository | None = None,
        zoho_field_metadata_repository: ZohoFieldMetadataRepository | None = None,
        integration_service: IntegrationService | None = None,
        candidate_sync_ledger_repository: CandidateSyncLedgerRepository | None = None,
    ):
        self.review_batch_repository = review_batch_repository
        self.candidate_review_repository = candidate_review_repository
        self.proposed_field_change_repository = proposed_field_change_repository
        self.candidate_repository = candidate_repository
        self.zoho_recruit_client = zoho_recruit_client
        self.resume_fetch_service = resume_fetch_service
        self.activity_log_repository = activity_log_repository
        self.zoho_field_metadata_repository = zoho_field_metadata_repository
        self.integration_service = integration_service
        self.candidate_sync_ledger_repository = candidate_sync_ledger_repository

    def create_review_batch(
        self, batch_size: int | None = None, access_token: str | None = None, created_by_user_id: UUID | None = None
    ) -> ReviewBatch:
        """
        Create a new review batch and process candidates.

        1. Select batch_size candidates (or from config)
        2. For each candidate, fetch Zoho data + resume
        3. Extract structured resume data
        4. Compare Zoho vs extracted values
        5. Create proposed changes (only for empty Zoho fields with resume data)
        6. Save to database

        Args:
            batch_size: Number of candidates to process (uses REVIEW_BATCH_SIZE config if None)
            access_token: Zoho API access token (optional for testing)
            created_by_user_id: User who created the batch

        Returns:
            ReviewBatch with status and counts

        Raises:
            ResumeEnrichmentError: If batch creation fails
        """
        if batch_size is None:
            batch_size = settings.review_batch_size

        try:
            # Generate batch number
            batch_number = self.review_batch_repository.get_next_batch_number()
            logger.info(f"Creating review batch: {batch_number}, size: {batch_size}")

            # Create batch record
            batch = self.review_batch_repository.create(
                batch_number=batch_number,
                batch_size=batch_size,
                total_candidates=batch_size,
                created_by_user_id=created_by_user_id,
            )

            # Get candidates without review yet (select up to batch_size)
            candidates_to_review = self.candidate_repository.get_unreviewed_candidates(limit=batch_size)

            if not candidates_to_review:
                logger.warning(f"No unreviewed candidates found for batch {batch_number}")
                batch.status = "COMPLETED"
                batch.total_candidates = 0
                return batch

            batch.total_candidates = len(candidates_to_review)

            logger.info(f"Processing {len(candidates_to_review)} candidates in batch {batch_number}")

            # Update batch status
            batch.status = "PROCESSING"
            batch.processing_started_at = datetime.now(timezone.utc)
            self.review_batch_repository.session.flush()

            # Process each candidate
            successful_count = 0
            error_count = 0
            writable_fields = self._get_writable_fields(access_token)

            for candidate in candidates_to_review:
                try:
                    self._process_candidate(batch.id, candidate, access_token, writable_fields)
                    successful_count += 1
                except Exception as exc:
                    logger.error(f"Error processing candidate {candidate.full_name} ({candidate.id}): {str(exc)}")
                    error_count += 1
                    # Continue processing other candidates instead of stopping

            # Update batch counts
            batch.processed_candidates = successful_count
            batch.status = "COMPLETED"
            batch.processing_completed_at = datetime.now(timezone.utc)
            self.review_batch_repository.session.flush()

            logger.info(
                f"Batch {batch_number} completed: {successful_count} processed, {error_count} errors"
            )
            self._log_activity(
                actor_id=created_by_user_id,
                action_type="resume_enrichment_batch_created",
                description=f"Created resume enrichment batch {batch_number} for {len(candidates_to_review)} candidates",
                entity_type="review_batch",
                entity_id=batch.id,
                result="warning" if error_count else "success",
                metadata={"processed": successful_count, "errors": error_count},
            )

            return batch

        except Exception as exc:
            logger.error(f"Failed to create review batch: {str(exc)}")
            raise ResumeEnrichmentError(f"Failed to create review batch: {str(exc)}") from exc

    def get_review_batch(self, batch_id: UUID) -> ReviewBatch | None:
        """Get batch by ID."""
        return self.review_batch_repository.get_by_id(batch_id)

    def get_candidate_review(self, candidate_review_id: UUID) -> CandidateReview | None:
        """Get candidate review with all proposed changes."""
        return self.candidate_review_repository.get_by_id(candidate_review_id)

    def approve_proposed_changes(
        self,
        candidate_review_id: UUID,
        field_ids: list[UUID] | None = None,
        user_id: UUID | None = None,
        notes: str | None = None,
    ) -> int:
        """
        Approve proposed changes for a candidate.

        Args:
            candidate_review_id: The candidate review ID
            field_ids: Specific field IDs to approve (None = approve all PENDING)
            user_id: User approving the changes
            notes: Optional approval notes

        Returns:
            Number of fields approved
        """
        if field_ids is None:
            # Approve all PENDING fields
            pending_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
                candidate_review_id, "PENDING"
            )
            field_ids = [change.id for change in pending_changes]

        if not field_ids:
            return 0

        count = self.proposed_field_change_repository.bulk_update_status(field_ids, "APPROVED", notes)

        self._update_review_decision_status(candidate_review_id, user_id, notes)

        logger.info(f"Approved {count} proposed changes for candidate review {candidate_review_id}")
        self._log_activity(
            actor_id=user_id,
            action_type="resume_enrichment_changes_approved",
            description=f"Approved {count} resume enrichment changes",
            entity_type="candidate_review",
            entity_id=candidate_review_id,
            metadata={"field_ids": [str(field_id) for field_id in field_ids]},
        )
        return count

    def reject_proposed_changes(
        self,
        candidate_review_id: UUID,
        field_ids: list[UUID] | None = None,
        user_id: UUID | None = None,
        notes: str | None = None,
    ) -> int:
        """
        Reject proposed changes for a candidate.

        Args:
            candidate_review_id: The candidate review ID
            field_ids: Specific field IDs to reject (None = reject all PENDING)
            user_id: User rejecting the changes
            notes: Optional rejection notes

        Returns:
            Number of fields rejected
        """
        if field_ids is None:
            # Reject all PENDING fields
            pending_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
                candidate_review_id, "PENDING"
            )
            field_ids = [change.id for change in pending_changes]

        if not field_ids:
            return 0

        count = self.proposed_field_change_repository.bulk_update_status(field_ids, "REJECTED", notes)

        self._update_review_decision_status(candidate_review_id, user_id, notes)

        logger.info(f"Rejected {count} proposed changes for candidate review {candidate_review_id}")
        self._log_activity(
            actor_id=user_id,
            action_type="resume_enrichment_changes_rejected",
            description=f"Rejected {count} resume enrichment changes",
            entity_type="candidate_review",
            entity_id=candidate_review_id,
            metadata={"field_ids": [str(field_id) for field_id in field_ids]},
        )
        return count

    def prepare_approved_write_back(self, candidate_review_id: UUID) -> dict[str, Any]:
        """Build, but never send, the payload for approved candidate changes.

        This is intentionally preparation-only. It performs no Zoho write request.
        """
        candidate_review = self.candidate_review_repository.get_by_id(candidate_review_id)
        if candidate_review is None:
            raise ResumeEnrichmentError(f"Candidate review {candidate_review_id} not found")

        candidate = self.candidate_repository.get_by_id(candidate_review.candidate_id)
        if candidate is None:
            raise ResumeEnrichmentError(f"Candidate {candidate_review.candidate_id} not found")

        approved_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
            candidate_review_id, "APPROVED"
        )
        writable_fields = self._get_writable_fields(None)
        payload, skipped = self._build_candidate_update_payload(
            raw_payload=self._get_zoho_candidate_data(candidate),
            approved_changes=approved_changes,
            writable_fields=writable_fields,
        )

        return {
            "candidate_review_id": str(candidate_review_id),
            "zoho_record_id": candidate.zoho_record_id,
            "payload": payload,
            "skipped": skipped,
            "sent_to_zoho": settings.zoho_write_enabled,
        }

    def send_approved_changes(self, candidate_review_id: UUID) -> dict[str, Any]:
        """Send approved changes only when write-back is explicitly enabled.

        With the default safety setting this method returns without making any
        external request, which keeps development and test environments read-only.
        """
        preview = self.prepare_approved_write_back(candidate_review_id)
        candidate_review = self.candidate_review_repository.get_by_id(candidate_review_id)
        live_preview = self._prepare_live_write_back(candidate_review_id, preview)
        if not settings.zoho_write_enabled:
            if candidate_review:
                candidate_review.write_back_status = "DISABLED"
                candidate_review.write_back_error = "Zoho write-back is disabled"
                candidate_review.write_back_at = datetime.now(timezone.utc)
                self.review_batch_repository.session.flush()
            self._log_activity(
                actor_id=None,
                action_type="resume_enrichment_write_back_blocked",
                description="Write-back request blocked because Zoho writes are disabled",
                entity_type="candidate_review",
                entity_id=candidate_review_id,
                result="warning",
            )
            return {
                **live_preview,
                "status": "WRITE_BACK_DISABLED",
                "sent_to_zoho": settings.zoho_write_enabled,
            }

        if not live_preview["payload"]:
            return {**preview, "status": "NO_WRITABLE_CHANGES"}
        if self.integration_service is None:
            raise ResumeEnrichmentError("Zoho integration service is not configured")

        token = self.integration_service.get_active_access_token()
        if token is None:
            raise ResumeEnrichmentError("Zoho access token is unavailable")

        result = self.zoho_recruit_client.update_candidate(
            access_token=token,
            candidate_id=live_preview["zoho_record_id"],
            fields=live_preview["payload"],
        )
        if self.candidate_sync_ledger_repository is not None:
            updated_candidate = self.zoho_recruit_client.fetch_candidate(
                token,
                live_preview["zoho_record_id"],
            )
            self.candidate_sync_ledger_repository.record_completed(
                zoho_record_id=live_preview["zoho_record_id"],
                modified_time=parse_zoho_modified_time(updated_candidate.get("Modified_Time")),
                payload_hash=candidate_payload_hash(updated_candidate),
            )
        return {
            **live_preview,
            "status": "SENT",
            "sent_to_zoho": settings.zoho_write_enabled,
            "zoho_response": result,
        }

    def send_approved_batch(self, batch_id: UUID, actor_id: UUID | None = None) -> dict[str, Any]:
        """Process approved reviews in a batch through the guarded candidate flow."""
        batch = self.review_batch_repository.get_by_id(batch_id)
        if batch is None:
            raise ResumeEnrichmentError(f"Review batch {batch_id} not found")

        reviews = self.candidate_review_repository.get_by_batch_id(batch_id)
        approved_reviews = [
            review
            for review in reviews
            if self.proposed_field_change_repository.get_by_candidate_review_id_and_status(review.id, "APPROVED")
        ]
        results = [self.send_approved_changes(review.id) for review in approved_reviews]
        statuses = [str(result.get("status")) for result in results]
        summary = {
            "batch_id": str(batch_id),
            "total_approved": len(approved_reviews),
            "processed": len(results),
            "statuses": statuses,
            "sent_to_zoho": any(result.get("sent_to_zoho") is True for result in results),
            "results": results,
        }
        self._log_activity(
            actor_id=actor_id,
            action_type="resume_enrichment_batch_write_back_blocked" if not settings.zoho_write_enabled else "resume_enrichment_batch_write_back",
            description=f"Processed {len(results)} approved reviews for batch write-back",
            entity_type="review_batch",
            entity_id=batch_id,
            result="warning" if not settings.zoho_write_enabled else "success",
            metadata={"processed": len(results), "statuses": statuses},
        )
        return summary

    def _prepare_live_write_back(
        self, candidate_review_id: UUID, preview: dict[str, Any]
    ) -> dict[str, Any]:
        """Re-fetch Zoho data and rebuild the payload immediately before sending."""
        if self.integration_service is None:
            raise ResumeEnrichmentError("Zoho integration service is not configured")
        token = self.integration_service.get_active_access_token()
        if token is None:
            raise ResumeEnrichmentError("Zoho access token is unavailable")

        live_payload = self.zoho_recruit_client.fetch_candidate(token, preview["zoho_record_id"])
        approved_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
            candidate_review_id, "APPROVED"
        )
        writable_fields = self._get_writable_fields(token)
        payload, skipped = self._build_candidate_update_payload(
            raw_payload=live_payload,
            approved_changes=approved_changes,
            writable_fields=writable_fields,
        )
        return {**preview, "payload": payload, "skipped": skipped}

    def _update_review_decision_status(
        self, candidate_review_id: UUID, user_id: UUID | None, notes: str | None
    ) -> None:
        changes = self.proposed_field_change_repository.get_by_candidate_review_id(candidate_review_id)
        status = self._approval_status_for_changes(changes)
        review = self.candidate_review_repository.get_by_id(candidate_review_id)
        if review:
            self.candidate_review_repository.update_approval_status(
                candidate_review_id, status, user_id, notes
            )
            review.write_back_status = "READY_TO_SEND" if any(
                change.change_status == "APPROVED" for change in changes
            ) else "NOT_SENT"
            self.review_batch_repository.session.flush()

    @staticmethod
    def _approval_status_for_changes(changes: list[Any]) -> str:
        statuses = [change.change_status for change in changes]
        approved = statuses.count("APPROVED")
        rejected = statuses.count("REJECTED")
        pending = statuses.count("PENDING")
        if approved and not rejected and not pending:
            return "APPROVED"
        if rejected and not approved and not pending:
            return "REJECTED"
        if approved or rejected:
            return "PARTIALLY_APPROVED"
        return "PENDING"

    @classmethod
    def _build_candidate_update_payload(
        cls,
        *,
        raw_payload: dict[str, Any],
        approved_changes: list[Any],
        writable_fields: set[str] | None,
    ) -> tuple[dict[str, Any], list[dict[str, str]]]:
        """Build a guarded update payload without performing network I/O."""
        payload: dict[str, Any] = {}
        skipped: list[dict[str, str]] = []

        for change in approved_changes:
            field_name = change.zoho_field_api_name
            if writable_fields is not None and field_name not in writable_fields:
                skipped.append({"field": field_name, "reason": "field_not_writable"})
                continue
            if field_name not in raw_payload:
                skipped.append({"field": field_name, "reason": "field_not_in_raw_payload"})
                continue
            if cls._has_value(raw_payload[field_name]):
                skipped.append({"field": field_name, "reason": "zoho_field_no_longer_empty"})
                continue
            if not cls._has_value(change.proposed_value):
                skipped.append({"field": field_name, "reason": "approved_value_empty"})
                continue
            payload[field_name] = change.proposed_value

        return payload, skipped

    # Private helper methods

    def _process_candidate(
        self,
        batch_id: UUID,
        candidate: Candidate,
        access_token: str | None = None,
        writable_fields: set[str] | None = None,
    ) -> None:
        """
        Process a single candidate:
        1. Create candidate_review record
        2. Extract data from resume
        3. Get Zoho candidate data
        4. Compare values
        5. Create proposed changes
        """
        logger.info(f"Processing candidate: {candidate.full_name} ({candidate.id})")

        # Create candidate review record
        candidate_review = self.candidate_review_repository.create(
            batch_id=batch_id,
            candidate_id=candidate.id,
            candidate_name=candidate.full_name,
            zoho_candidate_id=candidate.zoho_candidate_id,
        )

        # Get candidate's resume file
        if not candidate.resume_url:
            logger.warning(f"No resume available for {candidate.full_name}")
            return

        # Extract structured resume data
        try:
            extracted_data = self._extract_resume_data(candidate.resume_url)
            logger.debug(f"Extracted resume data for {candidate.full_name}: {extracted_data}")
        except Exception as exc:
            logger.error(f"Failed to extract resume data for {candidate.full_name}: {str(exc)}")
            return

        # Get current Zoho candidate data
        zoho_candidate_data = self._get_zoho_candidate_data(candidate)

        # Compare values and create proposed changes
        for _, (extracted_field_path, display_name, zoho_aliases) in self.RESUME_FIELD_MAPPING.items():
            resolved_field = self._resolve_zoho_field(zoho_candidate_data, zoho_aliases)
            if resolved_field is None:
                continue

            zoho_field_name, existing_zoho_value = resolved_field
            if writable_fields is not None and zoho_field_name not in writable_fields:
                continue
            extracted_value = self._get_extracted_value(extracted_data, extracted_field_path)

            # Apply business rule: only propose change if Zoho is empty and resume has value
            comparison = self._compare_values(existing_zoho_value, extracted_value)

            if comparison["action"] == "PROPOSE_UPDATE":
                self.proposed_field_change_repository.create(
                    candidate_review_id=candidate_review.id,
                    zoho_field_api_name=zoho_field_name,
                    zoho_field_display_name=display_name,
                    existing_zoho_value=existing_zoho_value,
                    extracted_resume_value=extracted_value,
                    proposed_value=extracted_value,
                )
                logger.debug(f"Created proposed change for {display_name}: {extracted_value}")

    def _extract_resume_data(self, resume_reference: str) -> dict[str, Any]:
        """Extract structured data from a stored resume."""
        try:
            file_ext = "." + resume_reference.rsplit(".", 1)[-1].lower()
            file_type_map = {
                ".pdf": "pdf",
                ".docx": "docx",
                ".doc": "doc",
            }
            file_type = file_type_map.get(file_ext, "pdf")

            # Use existing Kanini parser
            from app.services.kanini_resume_parser import parse_resume

            with self.resume_fetch_service.storage.materialize(resume_reference) as resume_path:
                extracted = parse_resume(str(resume_path), file_type)

            return extracted if isinstance(extracted, dict) else extracted.__dict__

        except Exception as exc:
            raise ResumeEnrichmentError(f"Resume extraction failed: {str(exc)}") from exc

    def _get_zoho_candidate_data(self, candidate: Candidate) -> dict[str, Any]:
        """Return all fields captured in the synchronized Zoho payload."""
        return dict(candidate.raw_payload) if isinstance(candidate.raw_payload, dict) else {}

    def _get_writable_fields(self, access_token: str | None) -> set[str] | None:
        """Load writable Zoho fields from fresh or cached metadata."""
        repository = self.zoho_field_metadata_repository
        if repository is None:
            return None

        provider = "zoho_recruit"
        module = "Candidates"
        if not repository.is_fresh(provider, module, timedelta(hours=24)):
            token = access_token
            if token is None and self.integration_service is not None:
                token = self.integration_service.get_active_access_token()
            if token is None:
                logger.warning("Zoho metadata unavailable; skipping enrichment proposals")
                return set()

            metadata = self.zoho_recruit_client.fetch_candidate_field_metadata(token)
            repository.replace_fields(
                provider,
                module,
                [
                    {
                        "api_name": item.api_name,
                        "display_label": item.display_label,
                        "data_type": item.data_type,
                        "read_only": item.read_only,
                        "raw_metadata": item.raw_metadata or {},
                    }
                    for item in metadata
                ],
            )

        unsupported_types = {"autonumber", "formula", "lookup", "owner", "subform"}
        return {
            field.api_name
            for field in repository.list_fields(provider, module)
            if not field.read_only and field.data_type.lower() not in unsupported_types
        }

    @staticmethod
    def _resolve_zoho_field(
        raw_payload: dict[str, Any], aliases: tuple[str, ...]
    ) -> tuple[str, Any] | None:
        """Resolve a resume concept to an existing field in the raw Zoho payload."""
        for alias in aliases:
            if alias in raw_payload:
                return alias, raw_payload[alias]

        normalized_payload = {
            ResumeEnrichmentService._normalize_field_name(key): key for key in raw_payload
        }
        for alias in aliases:
            payload_key = normalized_payload.get(ResumeEnrichmentService._normalize_field_name(alias))
            if payload_key is not None:
                return payload_key, raw_payload[payload_key]

        return None

    @staticmethod
    def _normalize_field_name(value: str) -> str:
        """Normalize API-name spelling for case and separator differences."""
        return "".join(character.lower() for character in value if character.isalnum())

    def _get_extracted_value(self, extracted_data: dict[str, Any], field_path: str) -> Any:
        """Get nested values using dot notation and zero-based list notation."""
        import re

        keys = [match.group(1) or match.group(0) for match in re.finditer(r"[^.\[\]]+|\[(\d+)\]", field_path)]
        value = extracted_data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                value = value[index] if index < len(value) else None
            else:
                return None

        return value

    def _compare_values(self, zoho_value: Any, extracted_value: Any) -> dict[str, Any]:
        """
        Apply business rule for field comparison.

        Logic:
        1. If Zoho has a real non-empty value → KEEP it (never propose update)
        2. If Zoho is empty AND resume has value → PROPOSE update  
        3. If both are empty → NO_CHANGE

        Returns:
            {
                "action": "KEEP_ZOHO" | "PROPOSE_UPDATE" | "NO_CHANGE",
                "existing_zoho_value": zoho_value,
                "extracted_value": extracted_value,
                "proposed_change": extracted_value or None
            }
        """
        zoho_has_value = self._has_value(zoho_value)
        extracted_has_value = self._has_value(extracted_value)

        # Zoho has existing value → NEVER create proposed change
        if zoho_has_value:
            return {
                "action": "KEEP_ZOHO",
                "existing_zoho_value": zoho_value,
                "extracted_value": extracted_value,
                "proposed_change": None,
            }

        # Zoho empty, resume has value → Create proposed change
        if extracted_has_value:
            return {
                "action": "PROPOSE_UPDATE",
                "existing_zoho_value": None,
                "extracted_value": extracted_value,
                "proposed_change": extracted_value,
            }

        # Both empty → No change
        return {
            "action": "NO_CHANGE",
            "existing_zoho_value": None,
            "extracted_value": None,
            "proposed_change": None,
        }

    @staticmethod
    def _has_value(value: Any) -> bool:
        """Return whether a value contains meaningful data for enrichment."""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict, tuple, set)):
            return bool(value)
        return True

    def delete_review_batch(self, batch_id: UUID) -> bool:
        """Delete a review batch and all related records (candidate reviews, proposed changes)."""
        try:
            batch = self.review_batch_repository.get_by_id(batch_id)
            if not batch:
                logger.warning(f"Batch {batch_id} not found")
                return False

            # Delete is handled by cascade delete due to foreign key constraints
            success = self.review_batch_repository.delete(batch_id)
            if success:
                logger.info(f"Deleted batch {batch_id} and all related records")
            return success
        except Exception as exc:
            logger.error(f"Failed to delete batch {batch_id}: {str(exc)}")
            return False

    def _log_activity(
        self,
        *,
        actor_id: UUID | None,
        action_type: str,
        description: str,
        entity_type: str,
        entity_id: UUID,
        result: str = "success",
        metadata: dict | None = None,
    ) -> None:
        if self.activity_log_repository is None:
            return
        self.activity_log_repository.create(
            actor_id=actor_id,
            action_type=action_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            result=result,
            metadata=metadata,
        )
