from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.saved_filter_repository import SavedFilterRepository
from app.schemas.saved_filters import SaveFilterRequest, SavedFilterResponse


class SavedFilterError(Exception):
    status_code = 400
    code = "SAVED_FILTER_ERROR"
    detail = "Saved filter request could not be processed"


class SavedFilterValidationError(SavedFilterError):
    status_code = 422
    code = "INVALID_SAVED_FILTER"

    def __init__(self, detail: str) -> None:
        self.detail = detail


@dataclass(slots=True)
class SavedFilterService:
    repository: SavedFilterRepository
    job_description_repository: JobDescriptionRepository

    def create_saved_filter(self, *, recruiter_id: UUID, request: SaveFilterRequest) -> SavedFilterResponse:
        if not request.filter_criteria:
            raise SavedFilterValidationError("Filter criteria cannot be empty")

        if request.jd_id is not None and self.job_description_repository.get_by_id(request.jd_id) is None:
            raise SavedFilterValidationError("Selected job description was not found")

        warning: str | None = None
        if self.repository.has_name_for_recruiter(recruiter_id, request.name):
            warning = "A saved filter with this name already exists. Saving as a duplicate name."

        saved_filter = self.repository.create(
            recruiter_id=recruiter_id,
            name=request.name,
            jd_id=request.jd_id,
            filter_criteria=request.filter_criteria,
        )
        resolved_query_params = self._resolve_query_params(saved_filter.jd_id, saved_filter.filter_criteria)
        return SavedFilterResponse(
            id=saved_filter.id,
            recruiter_id=saved_filter.recruiter_id,
            name=saved_filter.name,
            jd_id=saved_filter.jd_id,
            filter_criteria=saved_filter.filter_criteria,
            resolved_query_params=resolved_query_params,
            created_at=saved_filter.created_at,
            updated_at=saved_filter.updated_at,
            warning=warning,
        )

    def list_saved_filters(self, *, recruiter_id: UUID) -> list[SavedFilterResponse]:
        items = self.repository.list_by_recruiter(recruiter_id)
        return [
            SavedFilterResponse(
                id=item.id,
                recruiter_id=item.recruiter_id,
                name=item.name,
                jd_id=item.jd_id,
                filter_criteria=item.filter_criteria,
                resolved_query_params=self._resolve_query_params(item.jd_id, item.filter_criteria),
                created_at=item.created_at,
                updated_at=item.updated_at,
                warning=None,
            )
            for item in items
        ]

    @staticmethod
    def _resolve_query_params(jd_id: UUID | None, filter_criteria: dict) -> dict[str, str]:
        allowed_keys = {
            "jd_id",
            "skills",
            "experience_min",
            "experience_max",
            "location",
            "preferred_location",
            "notice_period_max",
            "status",
            "degree",
            "certification",
            "resume_updated_since",
            "source",
            "relevant_experience",
            "current_ctc",
            "expected_ctc",
            "previous_company",
            "employment_status",
            "q",
        }

        resolved: dict[str, str] = {}
        if jd_id is not None:
            resolved["jd_id"] = str(jd_id)

        for key, raw_value in filter_criteria.items():
            if key not in allowed_keys:
                continue

            if raw_value is None:
                continue

            if isinstance(raw_value, str):
                text = raw_value.strip()
                if text:
                    resolved[key] = text
                continue

            if isinstance(raw_value, list):
                parts = [str(item).strip() for item in raw_value if str(item).strip()]
                if parts:
                    resolved[key] = ",".join(parts)
                continue

            if isinstance(raw_value, (int, float)):
                resolved[key] = str(raw_value)

        return resolved
