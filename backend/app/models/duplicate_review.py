from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DuplicateReview(Base):
    __tablename__ = "duplicate_reviews"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    matched_candidate_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True
    )
    match_basis: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    jd_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"DuplicateReview(id={self.id!s}, status={self.status!r}, confidence={self.confidence!r})"
