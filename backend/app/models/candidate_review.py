from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CandidateReview(Base):
    """Represents a candidate's review record within a review batch."""

    __tablename__ = "candidate_reviews"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("review_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    zoho_candidate_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Denormalized for convenience
    approval_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, APPROVED, REJECTED
    approval_notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"CandidateReview(id={self.id!s}, candidate_name={self.candidate_name!r}, approval_status={self.approval_status!r})"
