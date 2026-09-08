from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_recruiter
from app.core.database import get_db_session
from app.models.user import User
from app.repositories.shortlist_repository import ShortlistRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.schemas.shortlists import CreateShortlistRequest, ShortlistListItemResponse, ShortlistResponse
from app.services.shortlist_service import ShortlistService
from app.services.excel_export_service import ExcelExportService
from app.models.shortlist import Shortlist
from app.models.job_description import JobDescription

shortlist_router = APIRouter()


@shortlist_router.post("", response_model=ShortlistResponse)
async def create_shortlist(
    request: CreateShortlistRequest,
    current_user: User = Depends(get_current_recruiter),
    session: Session = Depends(get_db_session),
) -> ShortlistResponse:
    """Create or update a shortlist for the current recruiter with selected candidate ids."""
    repository = ShortlistRepository(session)
    service = ShortlistService(repository)

    return service.create_or_update(
        recruiter_id=current_user.id,
        jd_id=request.jd_id,
        candidate_ids=request.candidate_ids,
    )


@shortlist_router.get("", response_model=list[ShortlistListItemResponse])
async def list_shortlists(
    current_user: User = Depends(get_current_recruiter),
    jd_id: UUID | None = Query(default=None, description="Optional JD id to filter shortlists"),
    session: Session = Depends(get_db_session),
) -> list[ShortlistListItemResponse]:
    """List recruiter shortlists grouped by JD and include full candidate details."""
    repository = ShortlistRepository(session)
    service = ShortlistService(repository)
    return service.list_for_recruiter(recruiter_id=current_user.id, jd_id=jd_id)


@shortlist_router.delete("/{shortlist_id}/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_candidate_from_shortlist(
    shortlist_id: UUID,
    candidate_id: UUID,
    current_user: User = Depends(get_current_recruiter),
    session: Session = Depends(get_db_session),
):
    """Remove a candidate from a shortlist owned by the current recruiter."""
    repository = ShortlistRepository(session)
    service = ShortlistService(repository)

    try:
        service.remove_candidate(
            recruiter_id=current_user.id,
            shortlist_id=shortlist_id,
            candidate_id=candidate_id,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "SHORTLIST_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shortlist not found") from exc
        if code == "SHORTLIST_CANDIDATE_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found in shortlist") from exc
        raise
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this shortlist") from exc


@shortlist_router.get("/{shortlist_id}/export")
async def export_shortlist(
    shortlist_id: UUID,
    current_user: User = Depends(get_current_recruiter),
    session: Session = Depends(get_db_session),
):
    """Export a shortlist as an Excel (.xlsx) file.
    
    The exported file contains:
    - Candidate information (name, email, experience, skills, location, notice period)
    - Export summary (generated time, JD info, candidate count)
    
    Authorization: Only the recruiter who created the shortlist can export it.
    """
    # Verify shortlist exists and belongs to current recruiter
    shortlist = session.query(Shortlist).filter(Shortlist.id == shortlist_id).first()
    if not shortlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shortlist not found")
    
    if shortlist.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this shortlist"
        )

    try:
        # Generate the Excel file
        export_service = ExcelExportService(session)
        file_bytes, filename = export_service.generate_shortlist_export(shortlist_id)
        
        # Get JD info for logging
        jd = session.query(JobDescription).filter(JobDescription.id == shortlist.jd_id).first()
        
        # Log the export activity
        activity_log_repo = ActivityLogRepository(session)
        activity_log_repo.create(
            actor_id=current_user.id,
            action_type="shortlist_export",
            description=f"Exported shortlist for '{jd.title if jd else 'Unknown'}' with {len(file_bytes)} bytes",
        )
        
        # Return as downloadable file
        return StreamingResponse(
            iter([file_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes)),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

