from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.crypto import encrypt_value
from app.integrations.zoho_oauth import ZohoTokenRefreshResult
from app.models.integration_settings import IntegrationSettings
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.services.integration_service import IntegrationService


class FakeZohoOAuthClient:
    def __init__(self, result: ZohoTokenRefreshResult | None = None) -> None:
        self.result = result
        self.calls = 0

    def refresh_access_token(self, refresh_token: str) -> ZohoTokenRefreshResult | None:
        self.calls += 1
        return self.result


def test_get_zoho_status_returns_connected_for_active_token(sqlite_session) -> None:
    record = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        token_expires_at=datetime.now(UTC) + timedelta(minutes=30),
        access_level="read_only",
        sync_type="manual",
    )
    sqlite_session.add(record)
    sqlite_session.commit()

    repository = IntegrationSettingsRepository(sqlite_session)
    oauth_client = FakeZohoOAuthClient()
    service = IntegrationService(repository=repository, zoho_oauth_client=oauth_client)

    response = service.get_zoho_status()

    assert response.connection_state == "connected"
    assert response.status == "healthy"
    assert oauth_client.calls == 0


def test_get_zoho_status_returns_disconnected_without_token(sqlite_session) -> None:
    repository = IntegrationSettingsRepository(sqlite_session)
    oauth_client = FakeZohoOAuthClient()
    service = IntegrationService(repository=repository, zoho_oauth_client=oauth_client)

    response = service.get_zoho_status()

    assert response.connection_state == "disconnected"
    assert response.status == "disconnected"
    assert oauth_client.calls == 0


def test_get_zoho_status_refreshes_expired_token(sqlite_session) -> None:
    record = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("expired-token"),
        refresh_token_encrypted=encrypt_value("refresh-token"),
        token_expires_at=datetime.now(UTC) - timedelta(minutes=5),
        access_level="read_only",
        sync_type="manual",
    )
    sqlite_session.add(record)
    sqlite_session.commit()

    repository = IntegrationSettingsRepository(sqlite_session)
    oauth_client = FakeZohoOAuthClient(
        result=ZohoTokenRefreshResult(access_token="new-token", expires_in=3600, scope="ZohoRecruit.modules.ALL")
    )
    service = IntegrationService(repository=repository, zoho_oauth_client=oauth_client)

    response = service.get_zoho_status()

    assert response.connection_state == "connected"
    assert response.status == "healthy"
    assert oauth_client.calls == 1


def test_get_zoho_status_marks_expired_when_refresh_fails(sqlite_session) -> None:
    record = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("expired-token"),
        refresh_token_encrypted=encrypt_value("refresh-token"),
        token_expires_at=datetime.now(UTC) - timedelta(minutes=5),
        access_level="read_only",
        sync_type="manual",
    )
    sqlite_session.add(record)
    sqlite_session.commit()

    repository = IntegrationSettingsRepository(sqlite_session)
    oauth_client = FakeZohoOAuthClient(result=None)
    service = IntegrationService(repository=repository, zoho_oauth_client=oauth_client)

    response = service.get_zoho_status()

    assert response.connection_state == "disconnected"
    assert response.status == "token_expired"
    assert oauth_client.calls == 1
