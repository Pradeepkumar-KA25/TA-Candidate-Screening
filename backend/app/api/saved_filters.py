from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_activity_log_repository, get_saved_filter_service, require_roles
from app.repositories.activity_log_repository import ActivityLogRepository
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.saved_filters import SaveFilterRequest, SavedFilterResponse
from app.services.saved_filter_service import SavedFilterService


saved_filter_router = APIRouter()


@saved_filter_router.get(
    "",
    response_model=list[SavedFilterResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="List saved filters",
    description="Returns saved filter templates for the current recruiter.",
)
async def list_saved_filters(
    recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    saved_filter_service: SavedFilterService = Depends(get_saved_filter_service),
) -> list[SavedFilterResponse]:
    return saved_filter_service.list_saved_filters(recruiter_id=recruiter.id)


@saved_filter_router.post(
    "",
    response_model=SavedFilterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        422: {"model": ErrorResponse, "description": "Invalid saved filter input"},
    },
    summary="Create saved filter",
    description="Creates a named saved filter template for the current recruiter.",
)
async def create_saved_filter(
    request: SaveFilterRequest,
    recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    saved_filter_service: SavedFilterService = Depends(get_saved_filter_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> SavedFilterResponse:
    response = saved_filter_service.create_saved_filter(recruiter_id=recruiter.id, request=request)
    activity_log_repository.create(
        actor_id=recruiter.id,
        action_type="saved_filter_created",
        description=f"Created saved filter '{response.name}'",
        entity_type="saved_filter",
        entity_id=response.id,
        metadata={"job_description_id": str(response.jd_id) if response.jd_id else None},
    )
    return response
