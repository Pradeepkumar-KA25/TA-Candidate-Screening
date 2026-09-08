from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, status

from app.core.dependencies import (
    get_ranking_service,
    require_roles,
)
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.ranking import RankingResponse, RankingScoreBreakdownResponse
from app.services.candidate_filter_service import CandidateFilterCriteria
from app.services.ranking_service import (
    RankingJDNotFoundError,
    RankingNoCriteriaError,
    RankingCandidateNotFoundError,
    RankingService,
)


ranking_router = APIRouter()


@ranking_router.get(
    "",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Job description not found or no ranking criteria defined"},
        400: {"model": ErrorResponse, "description": "No ranking criteria defined for JD"},
    },
    summary="Get ranked candidates for a job description",
    description="Returns candidates ranked by weighted score against the JD's ranking criteria, sorted descending by score.",
)
async def get_ranked_candidates(
    jd_id: Annotated[UUID, Query(description="Job description ID")],
    status_filter: Annotated[str | None, Query(description="Filter by candidate status")] = None,
    source_filter: Annotated[str | None, Query(description="Filter by candidate source")] = None,
    location_filter: Annotated[str | None, Query(description="Filter by location")] = None,
    experience_min: Annotated[float | None, Query(ge=0, description="Minimum years of experience")] = None,
    experience_max: Annotated[float | None, Query(ge=0, description="Maximum years of experience")] = None,
    notice_period_max: Annotated[int | None, Query(ge=0, description="Maximum notice period in days")] = None,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: RankingService = Depends(get_ranking_service),
) -> RankingResponse:
    """Get ranked candidates for a job description.
    
    Query Parameters:
    - jd_id: Job description ID (required)
    - status_filter: Optional candidate status filter
    - source_filter: Optional candidate source filter
    - location_filter: Optional location filter
    - experience_min/max: Optional experience range filter
    - notice_period_max: Optional maximum notice period filter
    """
    # Build filter criteria from query parameters
    filter_criteria = CandidateFilterCriteria(
        status=status_filter,
        source=source_filter,
        location=location_filter,
        experience_min=experience_min,
        experience_max=experience_max,
        notice_period_max=notice_period_max,
    )

    try:
        return service.rank_candidates(jd_id, filter_criteria)
    except RankingJDNotFoundError as e:
        raise e
    except RankingNoCriteriaError as e:
        raise e


@ranking_router.get(
    "/{candidate_id}/breakdown",
    response_model=list[RankingScoreBreakdownResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Candidate or Job description not found"},
        400: {"model": ErrorResponse, "description": "No ranking criteria defined for JD"},
    },
    summary="Get match breakdown for a candidate against a JD",
    description="Returns detailed breakdown showing how each criterion was scored for a specific candidate against a JD.",
)
async def get_candidate_breakdown(
    candidate_id: Annotated[UUID, Path(description="Candidate ID")],
    jd_id: Annotated[UUID, Query(description="Job description ID")],
    _: User = Depends(require_roles("Recruiter", "Admin")),
    service: RankingService = Depends(get_ranking_service),
) -> list[RankingScoreBreakdownResponse]:
    """Get detailed match breakdown for a candidate against a job description.
    
    Returns per-criterion scoring details showing how the candidate matched each criterion.
    
    Query Parameters:
    - candidate_id: Candidate ID (required, in path)
    - jd_id: Job description ID (required)
    """
    try:
        return service.get_score_breakdown(candidate_id, jd_id)
    except RankingCandidateNotFoundError as e:
        raise e
    except RankingJDNotFoundError as e:
        raise e
    except RankingNoCriteriaError as e:
        raise e
