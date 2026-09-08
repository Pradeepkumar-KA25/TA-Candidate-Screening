from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.crypto import encrypt_value
from app.core.database import get_db_session
from app.core.security import create_access_token
from app.integrations.zoho_recruit import ZohoCandidatesPage, ZohoRecruitPermanentError
from app.models.normalization_rule import NormalizationRule
from app.main import app
from app.models.integration_settings import IntegrationSettings
from app.models.sync_log import SyncLog
from app.models.user import User
from app.repositories.integration_settings_repository import IntegrationSettingsRepository


class FakeZohoOAuthClient:
    def refresh_access_token(self, refresh_token: str):
        return None


class FakeZohoRecruitClient:
    def __init__(self, payloads: list[dict] | None = None, fail: bool = False) -> None:
        self.payloads = payloads or []
        self.fail = fail

    def fetch_candidates_page(self, access_token: str, page: int, per_page: int) -> ZohoCandidatesPage:
        if self.fail:
            raise ZohoRecruitPermanentError("Mocked Zoho failure")
        if page > 1:
            return ZohoCandidatesPage(candidates=[], has_more=False)
        return ZohoCandidatesPage(candidates=self.payloads, has_more=False)


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def _seed_integration(sqlite_session) -> None:
    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        refresh_token_encrypted=encrypt_value("refresh-token"),
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
        access_level="read_only",
        sync_type="manual",
    )
    sqlite_session.add(integration)
    sqlite_session.commit()


def test_sync_endpoint_success_with_mocked_zoho(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_integration(sqlite_session)

    mock_zoho_client = FakeZohoRecruitClient(
        payloads=[
            {"id": "z-1", "Full_Name": "Asha", "Email": "asha@example.com", "Skill_Set": "Python"},
            {"id": "z-2", "Full_Name": "Ravi", "Email": "ravi@example.com", "Skill_Set": "Java"},
        ]
    )

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        from app.core.dependencies import get_zoho_oauth_client, get_zoho_recruit_client

        app.dependency_overrides[get_zoho_oauth_client] = lambda: FakeZohoOAuthClient()
        app.dependency_overrides[get_zoho_recruit_client] = lambda: mock_zoho_client

        client = TestClient(app)
        start = client.post("/api/v1/sync/candidates", headers=_header(recruiter))

        assert start.status_code == 202
        sync_id = start.json()["sync_id"]

        status_response = client.get(f"/api/v1/sync/{sync_id}", headers=_header(recruiter))
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload["status"] == "completed"
        assert payload["records_fetched"] == 2
    finally:
        app.dependency_overrides.clear()


def test_sync_endpoint_failure_with_mocked_zoho(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_integration(sqlite_session)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        from app.core.dependencies import get_zoho_oauth_client, get_zoho_recruit_client

        app.dependency_overrides[get_zoho_oauth_client] = lambda: FakeZohoOAuthClient()
        app.dependency_overrides[get_zoho_recruit_client] = lambda: FakeZohoRecruitClient(fail=True)

        client = TestClient(app)
        start = client.post("/api/v1/sync/candidates", headers=_header(recruiter))

        assert start.status_code == 202
        sync_id = start.json()["sync_id"]

        status_response = client.get(f"/api/v1/sync/{sync_id}", headers=_header(recruiter))
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload["status"] == "failed"
        assert "Mocked Zoho failure" in (payload.get("error_message") or "")
    finally:
        app.dependency_overrides.clear()


def test_sync_endpoint_rejects_concurrent_sync(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration_repo = IntegrationSettingsRepository(sqlite_session)
    integration_repo.get_or_create("zoho_recruit")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        from app.repositories.sync_log_repository import SyncLogRepository

        sync_repo = SyncLogRepository(sqlite_session)
        sync_repo.create_running(triggered_by=recruiter.id)

        client = TestClient(app)
        response = client.post("/api/v1/sync/candidates", headers=_header(recruiter))

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "SYNC_ALREADY_RUNNING"
    finally:
        app.dependency_overrides.clear()


def test_sync_summary_endpoint_returns_counts_and_examples(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_integration(sqlite_session)

    sqlite_session.add(
        NormalizationRule(field_type="location", raw_value="Bangalore", normalized_value="Bengaluru")
    )
    sqlite_session.add(
        NormalizationRule(field_type="skill", raw_value="JAVA", normalized_value="Java")
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        from app.core.dependencies import get_zoho_oauth_client, get_zoho_recruit_client

        app.dependency_overrides[get_zoho_oauth_client] = lambda: FakeZohoOAuthClient()
        app.dependency_overrides[get_zoho_recruit_client] = lambda: FakeZohoRecruitClient(
            payloads=[
                {
                    "id": "z-1",
                    "Full_Name": "Asha",
                    "Email": "asha@example.com",
                    "Current_Location": "Bangalore",
                    "Skill_Set": "JAVA",
                }
            ]
        )

        client = TestClient(app)
        start = client.post("/api/v1/sync/candidates", headers=_header(recruiter))

        assert start.status_code == 202
        sync_id = start.json()["sync_id"]

        response = client.get(f"/api/v1/sync/{sync_id}/summary", headers=_header(recruiter))
        assert response.status_code == 200
        payload = response.json()

        assert payload["records_fetched"] == 1
        assert payload["records_new"] == 1
        assert payload["records_updated"] == 0
        assert payload["normalized_records"] >= 2
        assert any(example["raw_value"] == "Bangalore" for example in payload["normalization_examples"])
    finally:
        app.dependency_overrides.clear()


def test_sync_summary_endpoint_returns_not_found(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        missing_id = uuid4()
        response = client.get(f"/api/v1/sync/{missing_id}/summary", headers=_header(recruiter))

        assert response.status_code == 404
        payload = response.json()
        assert payload["code"] == "SYNC_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_sync_history_returns_recruiter_runs_with_outcome_counts(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    other_recruiter = user_factory(role="Recruiter", email="other.recruiter@example.com")
    now = datetime.now(UTC)
    sqlite_session.add_all(
        [
            SyncLog(
                triggered_by=recruiter.id,
                status="completed",
                started_at=now - timedelta(minutes=5),
                completed_at=now - timedelta(minutes=4),
                records_fetched=20,
                records_new=5,
                records_updated=12,
                records_failed=1,
                duplicate_matches=2,
            ),
            SyncLog(
                triggered_by=other_recruiter.id,
                status="completed",
                records_fetched=99,
            ),
        ]
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/sync/history", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["records_fetched"] == 20
        assert body["items"][0]["records_failed"] == 1
        assert body["items"][0]["duplicate_matches"] == 2
    finally:
        app.dependency_overrides.clear()
