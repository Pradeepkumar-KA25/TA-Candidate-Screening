from datetime import UTC, datetime, timedelta

from app.core.crypto import encrypt_value
from app.integrations.zoho_recruit import ZohoCandidatesPage
from app.models.integration_settings import IntegrationSettings
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from tests.test_sync_service import FakeZohoRecruitClient, _build_sync_service


def test_sync_advances_to_the_next_zoho_page(sqlite_session, user_factory, monkeypatch) -> None:
    monkeypatch.setattr("app.services.sync_service.settings.zoho_sync_max_records", 1)
    recruiter = user_factory(role="Recruiter")
    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    client = FakeZohoRecruitClient(
        pages={
            1: ZohoCandidatesPage(candidates=[{"id": "z-1", "Full_Name": "First", "Email": "first@example.com"}], has_more=True),
            2: ZohoCandidatesPage(candidates=[{"id": "z-2", "Full_Name": "Second", "Email": "second@example.com"}], has_more=False),
        }
    )
    service = _build_sync_service(sqlite_session, client)

    first_sync = service.start_sync(recruiter.id)
    service.run_sync(first_sync.sync_id)
    second_sync = service.start_sync(recruiter.id)
    service.run_sync(second_sync.sync_id)

    repository = CandidateRepository(sqlite_session)
    settings = IntegrationSettingsRepository(sqlite_session).get_by_provider("zoho_recruit")
    assert service.get_sync_status(first_sync.sync_id).records_new == 1
    assert service.get_sync_status(second_sync.sync_id).records_new == 1
    assert repository.get_by_zoho_record_id("z-1") is not None
    assert repository.get_by_zoho_record_id("z-2") is not None
    assert settings is not None
    assert settings.next_candidate_sync_page == 1