from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ShortlistCandidate(Base):
    __tablename__ = "shortlist_candidates"
    __table_args__ = (PrimaryKeyConstraint("shortlist_id", "candidate_id"),)

    shortlist_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("shortlists.id"), nullable=False)
    candidate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"ShortlistCandidate(shortlist_id={self.shortlist_id!s}, candidate_id={self.candidate_id!s})"
