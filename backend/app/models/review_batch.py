from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReviewBatch(Base):
    """Represents a batch of candidates processed for resume enrichment review."""

    __tablename__ = "review_batches"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    batch_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Configured at batch creation
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"ReviewBatch(id={self.id!s}, batch_number={self.batch_number!r}, status={self.status!r})"
