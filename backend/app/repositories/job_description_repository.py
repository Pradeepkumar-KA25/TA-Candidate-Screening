from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription


class JobDescriptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, job_description_id: UUID) -> JobDescription | None:
        statement = select(JobDescription).where(JobDescription.id == job_description_id)
        return self.session.scalar(statement)

    def get_by_code(self, jd_code: str) -> JobDescription | None:
        normalized = jd_code.strip().lower()
        statement = select(JobDescription).where(func.lower(JobDescription.jd_code) == normalized)
        return self.session.scalar(statement)

    def create(self, *, jd_code: str, title: str, required_skills: list[str]) -> JobDescription:
        item = JobDescription(
            jd_code=jd_code,
            title=title,
            required_skills=required_skills,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def list_for_dropdown(self) -> list[JobDescription]:
        statement = select(JobDescription).order_by(JobDescription.jd_code.asc())
        return list(self.session.scalars(statement).all())
