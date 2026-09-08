from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.saved_filter import SavedFilter


class SavedFilterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        recruiter_id: UUID,
        name: str,
        jd_id: UUID | None,
        filter_criteria: dict,
    ) -> SavedFilter:
        saved_filter = SavedFilter(
            recruiter_id=recruiter_id,
            name=name,
            jd_id=jd_id,
            filter_criteria=filter_criteria,
        )
        self.session.add(saved_filter)
        self.session.commit()
        self.session.refresh(saved_filter)
        return saved_filter

    def list_by_recruiter(self, recruiter_id: UUID) -> list[SavedFilter]:
        statement = (
            select(SavedFilter)
            .where(SavedFilter.recruiter_id == recruiter_id)
            .order_by(SavedFilter.updated_at.desc(), SavedFilter.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def has_name_for_recruiter(self, recruiter_id: UUID, name: str) -> bool:
        normalized_name = name.strip().lower()
        if not normalized_name:
            return False

        statement = (
            select(func.count(SavedFilter.id))
            .where(SavedFilter.recruiter_id == recruiter_id)
            .where(func.lower(SavedFilter.name) == normalized_name)
        )
        return (self.session.scalar(statement) or 0) > 0
