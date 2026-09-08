from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.dependencies import get_integration_service
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.schemas.integrations import (
    ZohoCandidateDiagnosticsResponse,
    ZohoFieldMetadataResponse,
    ZohoIntegrationStatusResponse,
)


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


class FakeIntegrationService:
    def __init__(
        self,
        response: ZohoIntegrationStatusResponse,
        diagnostics: ZohoCandidateDiagnosticsResponse | None = None,
    ) -> None:
        self.response = response
        self.diagnostics = diagnostics

    def get_zoho_status(self) -> ZohoIntegrationStatusResponse:
        return self.response

    def get_zoho_candidate_diagnostics(self) -> ZohoCandidateDiagnosticsResponse:
        assert self.diagnostics is not None
        return self.diagnostics


def test_get_zoho_status_connected() -> None:
    service = FakeIntegrationService(
        ZohoIntegrationStatusResponse(
            integration="Zoho Recruit",
            connection_state="connected",
            status="healthy",
            access_level="read_only",
            sync_type="manual",
            last_successful_sync_at=datetime.now(UTC),
            last_checked_at=datetime.now(UTC),
        )
    )

    app.dependency_overrides[get_integration_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.get("/api/v1/integrations/zoho/status")

        assert response.status_code == 200
        body = response.json()
        assert body["connection_state"] == "connected"
        assert body["status"] == "healthy"
    finally:
        app.dependency_overrides.clear()


def test_get_zoho_status_disconnected() -> None:
    service = FakeIntegrationService(
        ZohoIntegrationStatusResponse(
            integration="Zoho Recruit",
            connection_state="disconnected",
            status="disconnected",
            access_level="read_only",
            sync_type="manual",
            last_successful_sync_at=None,
            last_checked_at=datetime.now(UTC),
        )
    )

    app.dependency_overrides[get_integration_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.get("/api/v1/integrations/zoho/status")

        assert response.status_code == 200
        body = response.json()
        assert body["connection_state"] == "disconnected"
        assert body["status"] == "disconnected"
    finally:
        app.dependency_overrides.clear()


def test_get_zoho_status_token_expired() -> None:
    service = FakeIntegrationService(
        ZohoIntegrationStatusResponse(
            integration="Zoho Recruit",
            connection_state="disconnected",
            status="token_expired",
            access_level="read_only",
            sync_type="manual",
            last_successful_sync_at=None,
            last_checked_at=datetime.now(UTC),
        )
    )

    app.dependency_overrides[get_integration_service] = lambda: service
    try:
        client = TestClient(app)
        response = client.get("/api/v1/integrations/zoho/status")

        assert response.status_code == 200
        body = response.json()
        assert body["connection_state"] == "disconnected"
        assert body["status"] == "token_expired"
    finally:
        app.dependency_overrides.clear()


def test_get_zoho_candidate_diagnostics(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    service = FakeIntegrationService(
        ZohoIntegrationStatusResponse(
            integration="Zoho Recruit",
            connection_state="connected",
            status="healthy",
            access_level="read_only",
            sync_type="manual",
            last_successful_sync_at=None,
            last_checked_at=datetime.now(UTC),
        ),
        diagnostics=ZohoCandidateDiagnosticsResponse(
            integration="Zoho Recruit",
            connection_state="connected",
            status="healthy",
            candidate_field_count=2,
            field_metadata=[
                ZohoFieldMetadataResponse(api_name="Experience_in_Years", display_label="Experience", data_type="integer"),
                ZohoFieldMetadataResponse(api_name="Current_Employer", display_label="Current Employer", data_type="text"),
            ],
            live_sample_payload_keys=["Experience_in_Years", "Current_Employer"],
            latest_synced_payload_keys=["Experience_in_Years", "Current_Employer"],
            current_mapping_targets={"total_experience_years": ["Experience_in_Years"]},
            likely_matches={
                "total_experience_years": [
                    ZohoFieldMetadataResponse(
                        api_name="Experience_in_Years",
                        display_label="Experience",
                        data_type="integer",
                    )
                ]
            },
        ),
    )

    app.dependency_overrides[get_integration_service] = lambda: service
    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/integrations/zoho/candidates/diagnostics", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["candidate_field_count"] == 2
        assert body["field_metadata"][0]["api_name"] == "Experience_in_Years"
        assert body["live_sample_payload_keys"] == ["Experience_in_Years", "Current_Employer"]
    finally:
        app.dependency_overrides.clear()
