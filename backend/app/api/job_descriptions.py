from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import (
    get_job_description_service,
    get_ranking_criteria_service,
    require_roles,
)
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.job_descriptions import CreateJobDescriptionRequest, JobDescriptionListItemResponse, JobDescriptionResponse
from app.schemas.ranking_criteria import GetRankingCriteriaResponse, SetRankingCriteriaRequest
from app.services.job_description_service import JobDescriptionService
from app.services.ranking_criteria_service import (
    RankingCriteriaNotFoundError,
    RankingCriteriaWeightValidationError,
)
from app.services.ranking_criteria_service import RankingCriteriaService


job_description_router = APIRouter()


@job_description_router.get(
    "",
    response_model=list[JobDescriptionListItemResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="List job descriptions",
    description="Returns job descriptions for JD filter dropdowns.",
)
async def list_job_descriptions(
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: JobDescriptionService = Depends(get_job_description_service),
) -> list[JobDescriptionListItemResponse]:
    return service.list_job_descriptions()


@job_description_router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        409: {"model": ErrorResponse, "description": "Job description with same code already exists"},
        422: {"model": ErrorResponse, "description": "Invalid job description input"},
    },
    summary="Create job description",
    description="Creates a job description record for use in JD-aware candidate filtering.",
)
async def create_job_description(
    request: CreateJobDescriptionRequest,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: JobDescriptionService = Depends(get_job_description_service),
) -> JobDescriptionResponse:
    return service.create_job_description(request)


@job_description_router.get(
    "/{jd_id}/criteria",
    response_model=GetRankingCriteriaResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Job description not found"},
    },
    summary="Get ranking criteria for a job description",
    description="Returns the weighted ranking criteria for a specific job description.",
)
async def get_ranking_criteria(
    jd_id: UUID,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: RankingCriteriaService = Depends(get_ranking_criteria_service),
) -> GetRankingCriteriaResponse:
    try:
        return service.get_criteria_for_jd(jd_id)
    except RankingCriteriaNotFoundError as e:
        raise e


@job_description_router.post(
    "/{jd_id}/criteria",
    response_model=GetRankingCriteriaResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Job description not found"},
        422: {"model": ErrorResponse, "description": "Invalid criteria or weight sum does not equal 100"},
    },
    summary="Set ranking criteria for a job description",
    description="Replaces all ranking criteria for a job description. Weight points must total exactly 100.",
)
async def set_ranking_criteria(
    jd_id: UUID,
    request: SetRankingCriteriaRequest,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: RankingCriteriaService = Depends(get_ranking_criteria_service),
) -> GetRankingCriteriaResponse:
    try:
        return service.set_criteria_for_jd(jd_id, request)
    except RankingCriteriaNotFoundError as e:
        raise e
    except RankingCriteriaWeightValidationError as e:
        raise e
