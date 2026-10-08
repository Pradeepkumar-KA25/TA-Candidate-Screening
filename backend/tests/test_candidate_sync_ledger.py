from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.core.crypto import encrypt_value
from app.models.integration_settings import IntegrationSettings
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_sync_ledger_repository import CandidateSyncLedgerRepository
from app.services.resume_enrichment_service import ResumeEnrichmentService
from tests.test_sync_service import FakeZohoRecruitClient, _build_sync_service


def test_ledger_skips_deleted_unchanged_candidate_and_processes_newer_profile(
    sqlite_session,
    user_factory,
) -> None:
    recruiter = user_factory(role="Recruiter")
    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    first_payload = {
        "id": "z-1",
        "Candidate_ID": "CAND-1",
        "Full_Name": "Asha Sharma",
        "Email": "asha@example.com",
        "Current_Employer": "Acme",
        "Modified_Time": "2026-10-08T09:00:00+00:00",
    }
    service = _build_sync_service(
        sqlite_session,
        FakeZohoRecruitClient(payloads=[first_payload]),
    )

    first_sync = service.start_sync(recruiter.id)
    service.run_sync(first_sync.sync_id)

    candidate_repository = CandidateRepository(sqlite_session)
    ledger_repository = CandidateSyncLedgerRepository(sqlite_session)
    candidate = candidate_repository.get_by_zoho_record_id("z-1")
    ledger_entry = ledger_repository.get_by_zoho_record_id("z-1")
    assert candidate is not None
    assert ledger_entry is not None
    assert ledger_entry.status == "completed"
    assert service.get_sync_status(first_sync.sync_id).records_new == 1

    candidate_repository.delete(candidate.id)
    assert candidate_repository.get_by_zoho_record_id("z-1") is None

    second_sync = service.start_sync(recruiter.id)
    service.run_sync(second_sync.sync_id)

    second_status = service.get_sync_status(second_sync.sync_id)
    assert second_status.records_new == 0
    assert second_status.records_updated == 0
    assert candidate_repository.get_by_zoho_record_id("z-1") is None
    assert ledger_repository.get_by_zoho_record_id("z-1") is not None

    changed_payload = {
        **first_payload,
        "Current_Employer": "Initech",
        "Modified_Time": "2026-10-08T10:00:00+00:00",
    }
    service.zoho_recruit_client = FakeZohoRecruitClient(payloads=[changed_payload])
    third_sync = service.start_sync(recruiter.id)
    service.run_sync(third_sync.sync_id)

    third_status = service.get_sync_status(third_sync.sync_id)
    recreated_candidate = candidate_repository.get_by_zoho_record_id("z-1")
    refreshed_ledger_entry = ledger_repository.get_by_zoho_record_id("z-1")
    assert third_status.records_new == 0
    assert third_status.records_updated == 1
    assert recreated_candidate is not None
    assert recreated_candidate.current_company == "Initech"
    assert refreshed_ledger_entry is not None
    assert refreshed_ledger_entry.last_processed_modified_time is not None
    assert refreshed_ledger_entry.last_processed_modified_time.hour == 10


def test_invalid_candidate_does_not_create_completed_ledger_entry(
    sqlite_session,
    user_factory,
) -> None:
    recruiter = user_factory(role="Recruiter")
    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    payload = {
        "id": "z-invalid",
        "Full_Name": "Missing Contact",
        "Modified_Time": "2026-10-08T09:00:00+00:00",
    }
    service = _build_sync_service(
        sqlite_session,
        FakeZohoRecruitClient(payloads=[payload]),
    )

    sync = service.start_sync(recruiter.id)
    service.run_sync(sync.sync_id)

    ledger_entry = CandidateSyncLedgerRepository(sqlite_session).get_by_zoho_record_id("z-invalid")
    assert ledger_entry is None
    assert service.get_sync_status(sync.sync_id).records_failed == 1


def test_successful_write_back_records_post_update_zoho_version(
    sqlite_session,
    monkeypatch,
) -> None:
    class FakeWriteBackClient:
        def update_candidate(self, access_token: str, candidate_id: str, fields: dict) -> dict:
            return {"data": [{"code": "SUCCESS"}]}

        def fetch_candidate(self, access_token: str, candidate_id: str) -> dict:
            return {
                "id": candidate_id,
                "Email": "updated@example.com",
                "Modified_Time": "2026-10-08T11:00:00+00:00",
            }

    monkeypatch.setattr("app.services.resume_enrichment_service.settings.zoho_write_enabled", True)
    ledger_repository = CandidateSyncLedgerRepository(sqlite_session)
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)
    service.candidate_review_repository = SimpleNamespace(get_by_id=lambda candidate_review_id: object())
    service.integration_service = SimpleNamespace(get_active_access_token=lambda: "active-token")
    service.zoho_recruit_client = FakeWriteBackClient()
    service.candidate_sync_ledger_repository = ledger_repository
    service.prepare_approved_write_back = lambda candidate_review_id: {
        "candidate_review_id": str(candidate_review_id),
        "zoho_record_id": "z-1",
        "payload": {"Email": "updated@example.com"},
    }
    service._prepare_live_write_back = lambda candidate_review_id, preview: preview

    result = service.send_approved_changes(SimpleNamespace())

    ledger_entry = ledger_repository.get_by_zoho_record_id("z-1")
    assert result["status"] == "SENT"
    assert ledger_entry is not None
    assert ledger_entry.status == "completed"
    assert ledger_entry.last_processed_modified_time is not None
    assert ledger_entry.last_processed_modified_time.hour == 11
