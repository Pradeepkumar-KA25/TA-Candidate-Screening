from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.crypto import decrypt_value, encrypt_value
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoFieldMetadata, ZohoRecruitClient, ZohoRecruitClientError
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.schemas.integrations import (
    ZohoCandidateDiagnosticsResponse,
    ZohoFieldMetadataResponse,
    ZohoIntegrationStatusResponse,
)


class IntegrationError(Exception):
    status_code = 400
    code = "INTEGRATION_ERROR"
    detail = "Integration request could not be processed"


class ZohoDiagnosticsUnavailableError(IntegrationError):
    status_code = 409
    code = "ZOHO_DIAGNOSTICS_UNAVAILABLE"

    def __init__(self, detail: str) -> None:
        self.detail = detail


@dataclass(slots=True)
class IntegrationService:
    repository: IntegrationSettingsRepository
    candidate_repository: CandidateRepository
    zoho_oauth_client: ZohoOAuthClient
    zoho_recruit_client: ZohoRecruitClient

    provider_name: str = "zoho_recruit"

    @staticmethod
    def _as_utc(timestamp: datetime | None) -> datetime | None:
        if timestamp is None:
            return None
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)
        return timestamp.astimezone(UTC)

    def get_zoho_status(self) -> ZohoIntegrationStatusResponse:
        record = self.repository.get_or_create(self.provider_name)
        now = datetime.now(UTC)

        record.last_checked_at = now
        self._ensure_active_zoho_token(record)
        return self._to_response(record)

    def get_zoho_candidate_diagnostics(self) -> ZohoCandidateDiagnosticsResponse:
        record = self.repository.get_or_create(self.provider_name)
        access_token = self._ensure_active_zoho_token(record)

        if not access_token:
            raise ZohoDiagnosticsUnavailableError(record.last_error or "Zoho access token is not available")

        metadata_error: str | None = None
        live_sample_error: str | None = None

        try:
            field_metadata = self.zoho_recruit_client.fetch_candidate_field_metadata(access_token)
        except ZohoRecruitClientError as exc:
            field_metadata = []
            metadata_error = str(exc)

        try:
            live_sample_page = self.zoho_recruit_client.fetch_candidates_page(access_token=access_token, page=1, per_page=1)
            live_sample_payload = live_sample_page.candidates[0] if live_sample_page.candidates else {}
        except ZohoRecruitClientError as exc:
            live_sample_payload = {}
            live_sample_error = str(exc)

        latest_synced = self.candidate_repository.get_latest_synced_candidate()
        latest_payload = latest_synced.raw_payload if latest_synced and isinstance(latest_synced.raw_payload, dict) else {}

        current_mapping_targets = {
            "total_experience_years": ["Experience_in_Years", "Experience_in_Yrs", "Overall_IT_Experince"],
            "relevant_experience_years": ["Relevant_Experience", "Relevant_Exp"],
            "current_company": ["Current_Employer", "Employer_Details"],
            "current_location": ["Current_Location", "Current_Work_Location", "Current_Location_of_Candidate_KANINI_Work_Locati"],
            "preferred_location": ["Preferred_Location", "Preferred_Work_Location"],
            "degree": ["Highest_Qualification", "Highest_Qualification_Held"],
            "skills": ["Skill_Set", "Skills"],
            "current_ctc": ["Current_Salary", "CTC"],
            "expected_ctc": ["Expected_Salary", "Current_CTC_Expected_CTC"],
        }

        return ZohoCandidateDiagnosticsResponse(
            integration="Zoho Recruit",
            connection_state=record.connection_state,
            status=record.status,
            candidate_field_count=len(field_metadata),
            field_metadata=[self._to_field_metadata_response(item) for item in field_metadata],
            live_sample_payload_keys=sorted(str(key) for key in live_sample_payload.keys()),
            latest_synced_payload_keys=sorted(str(key) for key in latest_payload.keys()),
            current_mapping_targets=current_mapping_targets,
            likely_matches=self._build_likely_matches(field_metadata),
            metadata_error=metadata_error,
            live_sample_error=live_sample_error,
        )

    def _ensure_active_zoho_token(self, record) -> str | None:
        now = datetime.now(UTC)

        access_token = decrypt_value(record.access_token_encrypted)
        refresh_token = decrypt_value(record.refresh_token_encrypted)

        if not access_token:
            record.connection_state = "disconnected"
            record.status = "disconnected"
            if not record.last_error:
                record.last_error = "Access token is not configured"
            self.repository.save(record)
            return None

        token_expires_at = self._as_utc(record.token_expires_at)
        if token_expires_at and token_expires_at > now:
            record.connection_state = "connected"
            record.status = "healthy"
            record.last_error = None
            self.repository.save(record)
            return access_token

        if refresh_token:
            refreshed = self.zoho_oauth_client.refresh_access_token(refresh_token)
            if refreshed is not None:
                record.access_token_encrypted = encrypt_value(refreshed.access_token)
                record.token_expires_at = now + timedelta(seconds=refreshed.expires_in)
                if refreshed.scope:
                    record.scope = refreshed.scope
                record.connection_state = "connected"
                record.status = "healthy"
                record.last_error = None
                self.repository.save(record)
                return refreshed.access_token

        record.connection_state = "disconnected"
        record.status = "token_expired"
        record.last_error = "Access token expired and refresh failed"
        self.repository.save(record)
        return None

    @staticmethod
    def _to_field_metadata_response(item: ZohoFieldMetadata) -> ZohoFieldMetadataResponse:
        return ZohoFieldMetadataResponse(
            api_name=item.api_name,
            display_label=item.display_label,
            data_type=item.data_type,
        )

    def _build_likely_matches(self, field_metadata: list[ZohoFieldMetadata]) -> dict[str, list[ZohoFieldMetadataResponse]]:
        match_terms = {
            "total_experience_years": ["experience", "total"],
            "relevant_experience_years": ["relevant", "experience"],
            "current_company": ["current", "employer"],
            "current_location": ["current", "location"],
            "preferred_location": ["preferred", "location"],
            "education": ["qualification", "education", "degree"],
        }

        results: dict[str, list[ZohoFieldMetadataResponse]] = {}
        for target, terms in match_terms.items():
            matches: list[ZohoFieldMetadataResponse] = []
            for item in field_metadata:
                searchable = f"{item.api_name} {item.display_label}".lower().replace("_", " ")
                if all(term in searchable for term in terms):
                    matches.append(self._to_field_metadata_response(item))
            results[target] = matches[:10]
        return results

    def _to_response(self, record) -> ZohoIntegrationStatusResponse:
        return ZohoIntegrationStatusResponse(
            integration="Zoho Recruit",
            connection_state=record.connection_state,
            status=record.status,
            access_level=record.access_level,
            sync_type=record.sync_type,
            last_successful_sync_at=record.last_successful_sync_at,
            last_checked_at=record.last_checked_at or datetime.now(UTC),
        )
