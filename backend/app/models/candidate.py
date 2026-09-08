from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    zoho_record_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    zoho_candidate_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    total_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevant_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_degree: Mapped[str | None] = mapped_column(String(255), nullable=True)

    current_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    match_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"Candidate(id={self.id!s}, zoho_record_id={self.zoho_record_id!r}, "
            f"zoho_candidate_id={self.zoho_candidate_id!r})"
        )
