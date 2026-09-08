from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_duplicate_service, require_roles
from app.models.user import User
from app.schemas.duplicates import DuplicateGroupedResponse, DuplicatePairResponse
from app.schemas.errors import ErrorResponse
from app.services.duplicate_service import DuplicateService


duplicate_router = APIRouter()


@duplicate_router.get(
    "",
    response_model=DuplicateGroupedResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="List grouped duplicate candidates",
    description=(
        "Returns duplicate-review records grouped by job description, with pairwise candidate comparison details "
        "and top-level summary counts for dashboarding."
    ),
)
async def list_grouped_duplicates(
    _: User = Depends(require_roles("Recruiter", "Admin")),
    duplicate_service: DuplicateService = Depends(get_duplicate_service),
) -> DuplicateGroupedResponse:
    return duplicate_service.list_grouped_duplicates()


@duplicate_router.patch(
    "/{duplicate_id}/review",
    response_model=DuplicatePairResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Duplicate review not found"},
        409: {"model": ErrorResponse, "description": "Duplicate review has already been reviewed"},
    },
    summary="Mark duplicate as reviewed",
    description="Marks a duplicate-review record as reviewed and records who reviewed it and when.",
)
async def review_duplicate(
    duplicate_id: UUID,
    recruiter: User = Depends(require_roles("Recruiter")),
    duplicate_service: DuplicateService = Depends(get_duplicate_service),
) -> DuplicatePairResponse:
    return duplicate_service.review_duplicate(duplicate_review_id=duplicate_id, recruiter_id=recruiter.id)
