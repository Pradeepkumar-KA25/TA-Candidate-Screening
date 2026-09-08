from __future__ import annotations

from dataclasses import dataclass

from app.repositories.job_description_repository import JobDescriptionRepository
from app.schemas.job_descriptions import CreateJobDescriptionRequest, JobDescriptionListItemResponse, JobDescriptionResponse


class JobDescriptionError(Exception):
    status_code = 400
    code = "JOB_DESCRIPTION_ERROR"
    detail = "Job description request could not be processed"


class JobDescriptionConflictError(JobDescriptionError):
    status_code = 409
    code = "JOB_DESCRIPTION_ALREADY_EXISTS"

    def __init__(self, jd_code: str) -> None:
        self.detail = f"Job description with code '{jd_code}' already exists"


@dataclass(slots=True)
class JobDescriptionService:
    repository: JobDescriptionRepository

    def list_job_descriptions(self) -> list[JobDescriptionListItemResponse]:
        items = self.repository.list_for_dropdown()
        return [
            JobDescriptionListItemResponse(
                id=item.id,
                jd_code=item.jd_code,
                title=item.title,
                required_skills=item.required_skills or [],
            )
            for item in items
        ]

    def create_job_description(self, request: CreateJobDescriptionRequest) -> JobDescriptionResponse:
        existing = self.repository.get_by_code(request.jd_code)
        if existing is not None:
            raise JobDescriptionConflictError(request.jd_code)

        created = self.repository.create(
            jd_code=request.jd_code,
            title=request.title,
            required_skills=request.required_skills,
        )

        return JobDescriptionResponse(
            id=created.id,
            jd_code=created.jd_code,
            title=created.title,
            required_skills=created.required_skills or [],
            created_at=created.created_at,
        )
