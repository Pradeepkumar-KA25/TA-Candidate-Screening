from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.dependencies import get_candidate_service, require_roles
from app.models.user import User
from app.schemas.candidates import CandidateDetailResponse, CandidateListResponse
from app.schemas.errors import ErrorResponse
from app.services.candidate_service import CandidateService


candidate_router = APIRouter()


@candidate_router.get(
    "",
    response_model=CandidateListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        422: {"model": ErrorResponse, "description": "Invalid filter input"},
    },
    summary="List candidates",
    description=(
        "Returns a paginated, sortable candidate list with optional free-text search across name, skills, and "
        "company, plus inline basic filters (skills, experience range, location, notice period, and status)."
    ),
)
async def list_candidates(
    _: User = Depends(require_roles("Recruiter", "Admin")),
    q: str | None = Query(default=None, max_length=100, description="Search term for candidate name, skills, or company"),
    jd_id: UUID | None = Query(default=None, description="Selected job description UUID for scoped skill matching"),
    skills: str | None = Query(default=None, max_length=250, description="Comma-separated skills filter"),
    experience_min: float | None = Query(default=None, ge=0, description="Minimum total experience in years"),
    experience_max: float | None = Query(default=None, ge=0, description="Maximum total experience in years"),
    location: str | None = Query(default=None, max_length=120, description="Candidate current location filter"),
    preferred_location: str | None = Query(default=None, max_length=120, description="Candidate preferred location filter"),
    notice_period_max: int | None = Query(default=None, ge=0, description="Maximum notice period in days"),
    status: str | None = Query(default=None, max_length=64, description="Candidate status filter, optionally comma-separated"),
    degree: str | None = Query(default=None, max_length=120, description="Normalized degree filter"),
    certification: str | None = Query(default=None, max_length=120, description="Certification text filter"),
    resume_updated_since: int | None = Query(default=None, ge=0, description="Updated in last N days"),
    source: str | None = Query(default=None, max_length=64, description="Candidate source filter"),
    relevant_experience: float | None = Query(default=None, ge=0, description="Minimum relevant experience in years"),
    current_ctc: float | None = Query(default=None, ge=0, description="Minimum current CTC"),
    expected_ctc: float | None = Query(default=None, ge=0, description="Minimum expected CTC"),
    previous_company: str | None = Query(default=None, max_length=120, description="Previous company text filter"),
    employment_status: str | None = Query(default=None, max_length=64, description="Employment status text filter"),
    page: int = Query(default=1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(default=10, ge=1, le=100, description="Number of rows per page"),
    sort_by: str = Query(default="full_name", description="Field to sort by"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort direction"),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateListResponse:
    return candidate_service.list_candidates(
        page=page,
        page_size=page_size,
        q=q,
        sort_by=sort_by,
        sort_order=sort_order,
        jd_id=jd_id,
        skills=skills,
        experience_min=experience_min,
        experience_max=experience_max,
        location=location,
        preferred_location=preferred_location,
        notice_period_max=notice_period_max,
        status=status,
        degree=degree,
        certification=certification,
        resume_updated_since=resume_updated_since,
        source=source,
        relevant_experience=relevant_experience,
        current_ctc=current_ctc,
        expected_ctc=expected_ctc,
        previous_company=previous_company,
        employment_status=employment_status,
    )


@candidate_router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Candidate not found"},
    },
    summary="Get candidate details",
    description=(
        "Returns a complete candidate profile including normalized-data field pairs and current "
        "job-description and match context metadata."
    ),
)
async def get_candidate_details(
    candidate_id: UUID = Path(description="Candidate UUID"),
    _: User = Depends(require_roles("Recruiter", "Admin")),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateDetailResponse:
    return candidate_service.get_candidate_details(candidate_id)
