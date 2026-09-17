from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", server_default="running", index=True)
    records_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duplicate_matches: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    normalized_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    normalization_examples: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    triggered_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"SyncLog(id={self.id!s}, status={self.status!r})"
