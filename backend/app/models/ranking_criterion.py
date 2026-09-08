from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RankingCriterion(Base):
    __tablename__ = "ranking_criteria"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    jd_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    criteria_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_points: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"RankingCriterion(id={self.id!s}, jd_id={self.jd_id!s}, criteria_name={self.criteria_name!r})"
