from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NormalizationRule(Base):
    __tablename__ = "normalization_rules"
    __table_args__ = (UniqueConstraint("field_type", "raw_value", name="uq_normalization_rules_field_raw"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    field_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"NormalizationRule(id={self.id!s}, field_type={self.field_type!r}, raw_value={self.raw_value!r}, "
            f"normalized_value={self.normalized_value!r})"
        )
