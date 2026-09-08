from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration_settings import IntegrationSettings


class IntegrationSettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_provider(self, provider: str) -> IntegrationSettings | None:
        statement = select(IntegrationSettings).where(IntegrationSettings.provider == provider)
        return self.session.scalar(statement)

    def get_or_create(self, provider: str) -> IntegrationSettings:
        record = self.get_by_provider(provider)
        if record is not None:
            return record

        now = datetime.now(UTC)
        record = IntegrationSettings(
            provider=provider,
            status="disconnected",
            connection_state="disconnected",
            access_level="read_only",
            sync_type="manual",
            last_checked_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save(self, settings: IntegrationSettings) -> IntegrationSettings:
        settings.updated_at = datetime.now(UTC)
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings
