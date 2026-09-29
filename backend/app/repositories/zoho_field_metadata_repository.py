from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.zoho_field_metadata import ZohoFieldMetadataRecord


class ZohoFieldMetadataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_fresh(self, provider: str, module: str, max_age: timedelta) -> bool:
        latest = self.session.scalar(
            select(ZohoFieldMetadataRecord.fetched_at)
            .where(
                ZohoFieldMetadataRecord.provider == provider,
                ZohoFieldMetadataRecord.module == module,
            )
            .order_by(ZohoFieldMetadataRecord.fetched_at.desc())
            .limit(1)
        )
        if latest is None:
            return False
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        return latest >= datetime.now(UTC) - max_age

    def replace_fields(self, provider: str, module: str, fields: list[dict]) -> None:
        self.session.execute(
            delete(ZohoFieldMetadataRecord).where(
                ZohoFieldMetadataRecord.provider == provider,
                ZohoFieldMetadataRecord.module == module,
            )
        )
        fetched_at = datetime.now(UTC)
        for field in fields:
            self.session.add(
                ZohoFieldMetadataRecord(
                    provider=provider,
                    module=module,
                    api_name=field["api_name"],
                    display_label=field["display_label"],
                    data_type=field["data_type"],
                    read_only=field["read_only"],
                    raw_metadata=field["raw_metadata"],
                    fetched_at=fetched_at,
                )
            )
        self.session.flush()

    def list_fields(self, provider: str, module: str) -> list[ZohoFieldMetadataRecord]:
        return list(
            self.session.scalars(
                select(ZohoFieldMetadataRecord)
                .where(
                    ZohoFieldMetadataRecord.provider == provider,
                    ZohoFieldMetadataRecord.module == module,
                )
                .order_by(ZohoFieldMetadataRecord.api_name)
            ).all()
        )
