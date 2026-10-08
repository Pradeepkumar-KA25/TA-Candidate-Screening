from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CandidateSyncLedger(Base):
    __tablename__ = "candidate_sync_ledger"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    zoho_record_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    last_processed_modified_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing", server_default="processing", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
