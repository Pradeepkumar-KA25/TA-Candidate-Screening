from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CompanySector(Base):
    __tablename__ = "company_sectors"
    __table_args__ = (UniqueConstraint("company_key", name="uq_company_sectors_company_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    sector: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="ollama")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )