from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Shortlist(Base):
    __tablename__ = "shortlists"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    recruiter_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    jd_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"Shortlist(id={self.id!s}, recruiter_id={self.recruiter_id!s}, jd_id={self.jd_id!s})"
