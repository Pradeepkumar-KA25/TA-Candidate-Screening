from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path as FastAPIPath, Query, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.dependencies import get_activity_log_repository, get_candidate_service, require_roles
from app.models.user import User
from app.schemas.candidates import CandidateDetailResponse, CandidateListResponse
from app.schemas.errors import ErrorResponse
from app.services.candidate_service import CandidateService
from app.storage import StorageBackend, get_storage_backend
from app.repositories.activity_log_repository import ActivityLogRepository


class DeleteCandidatesRequest(BaseModel):
    candidate_ids: list[str]  # Accept strings and convert manually


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
    page_size: int = Query(default=10, ge=1, le=10000, description="Number of rows per page"),
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


@candidate_router.post(
    "/batch/delete",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="Delete multiple candidates",
    description="Deletes multiple candidates from the database in a single request. Admin role required.",
)
async def delete_candidates_batch(
    request: DeleteCandidatesRequest,
    current_user: User = Depends(require_roles("Admin")),
    candidate_service: CandidateService = Depends(get_candidate_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> dict:
    import logging
    from uuid import UUID as UUIDType
    
    logger = logging.getLogger(__name__)
    logger.info(f"Batch delete endpoint called")
    logger.info(f"Raw request: {request}")
    logger.info(f"Received {len(request.candidate_ids)} candidate IDs")
    
    # Convert string IDs to UUID
    candidate_uuid_ids = []
    for cid in request.candidate_ids:
        try:
            candidate_uuid_ids.append(UUIDType(cid))
            logger.debug(f"Converted {cid} to UUID")
        except Exception as e:
            logger.error(f"Failed to convert {cid} to UUID: {str(e)}")
    
    logger.info(f"Successfully converted {len(candidate_uuid_ids)} IDs to UUID")
    
    if not candidate_uuid_ids:
        logger.warning("No valid candidate IDs provided")
        return {"message": "No valid candidate IDs provided", "deleted_count": 0}
    
    deleted_count = candidate_service.delete_candidates_batch(candidate_uuid_ids)
    activity_log_repository.create(
        actor_id=current_user.id,
        action_type="candidate_bulk_deleted",
        description=f"Deleted {deleted_count} candidates",
        entity_type="candidate",
        result="success" if deleted_count else "warning",
        metadata={"requested_count": len(candidate_uuid_ids), "deleted_count": deleted_count},
    )
    logger.info(f"Batch delete completed. Deleted {deleted_count} candidates")
    return {"message": f"Deleted {deleted_count} candidate(s) successfully", "deleted_count": deleted_count}


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
    candidate_id: UUID = FastAPIPath(description="Candidate UUID"),
    _: User = Depends(require_roles("Recruiter", "Admin")),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateDetailResponse:
    return candidate_service.get_candidate_details(candidate_id)


@candidate_router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Candidate not found"},
    },
    summary="Delete candidate",
    description="Deletes a candidate from the database. Admin role required.",
)
async def delete_candidate(
    candidate_id: UUID = FastAPIPath(description="Candidate UUID"),
    current_user: User = Depends(require_roles("Admin")),
    candidate_service: CandidateService = Depends(get_candidate_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> dict:
    candidate_service.delete_candidate(candidate_id)
    activity_log_repository.create(
        actor_id=current_user.id,
        action_type="candidate_deleted",
        description="Deleted candidate",
        entity_type="candidate",
        entity_id=candidate_id,
    )
    return {"message": "Candidate deleted successfully"}


@candidate_router.get(
    "/{candidate_id}/resume",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Candidate or resume not found"},
    },
    summary="Get candidate resume",
    description="Returns the resume file for a candidate if available. Supports PDF, DOCX, and other formats.",
)
async def get_candidate_resume(
    candidate_id: UUID = FastAPIPath(..., description="Candidate UUID"),
    _: User = Depends(require_roles("Recruiter", "Admin")),
    candidate_service: CandidateService = Depends(get_candidate_service),
    storage: StorageBackend = Depends(get_storage_backend),
) -> Response:
    """Serve the candidate's resume file."""
    from fastapi import HTTPException
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Resume request for candidate: {candidate_id}")
    
    # Get candidate to retrieve resume URL
    candidate = candidate_service.get_candidate_details(candidate_id)
    logger.info(f"Candidate found: {candidate.full_name}, resume_url: {candidate.resume_url}")
    
    if not candidate.resume_url:
        logger.warning(f"No resume URL for candidate {candidate_id}")
        raise HTTPException(status_code=404, detail="Resume not found for this candidate")
    
    try:
        content = storage.read_bytes(candidate.resume_url)
        if not content:
            raise HTTPException(status_code=404, detail="Resume file is empty")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error reading resume: %s", exc)
        raise HTTPException(status_code=404, detail="Resume file not found") from exc
    
    # Determine media type based on file extension
    suffix = "." + candidate.resume_url.rsplit(".", 1)[-1].lower() if "." in candidate.resume_url else ""
    media_type_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
    }
    
    media_type = media_type_map.get(suffix, "application/octet-stream")
    
    filename = candidate.resume_file_name or f"resume{suffix}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
