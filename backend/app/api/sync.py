from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.core.dependencies import get_sync_service, require_roles
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.sync import (
    CandidateSyncHistoryResponse,
    CandidateSyncStatusResponse,
    CandidateSyncSummaryResponse,
    CandidateSyncTriggerResponse,
)
from app.services.sync_service import SyncService


sync_router = APIRouter()


@sync_router.post(
    "/candidates",
    response_model=CandidateSyncTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        409: {"model": ErrorResponse, "description": "A candidate sync is already running"},
    },
    summary="Trigger candidate sync from Zoho Recruit",
    description=(
        "Queues a background candidate synchronization run and returns a sync id for progress tracking. "
        "If another sync is already running, the request is rejected."
    ),
)
async def trigger_candidate_sync(
    background_tasks: BackgroundTasks,
    current_recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    sync_service: SyncService = Depends(get_sync_service),
) -> CandidateSyncTriggerResponse:
    trigger_response = sync_service.start_sync(current_recruiter.id)
    background_tasks.add_task(sync_service.run_sync, trigger_response.sync_id)
    return trigger_response


@sync_router.get(
    "/history",
    response_model=CandidateSyncHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get candidate sync history",
    description="Returns recent sync runs with record counts, duration fields, and errors.",
)
async def get_sync_history(
    current_recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    limit: int = Query(6, ge=1, le=20),
    sync_service: SyncService = Depends(get_sync_service),
) -> CandidateSyncHistoryResponse:
    return sync_service.get_sync_history(current_recruiter.id, limit)


@sync_router.get(
    "/{sync_id}",
    response_model=CandidateSyncStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Sync id not found"},
    },
    summary="Get candidate sync status",
    description="Returns the current status and counters for a previously triggered candidate sync run.",
)
async def get_candidate_sync_status(
    sync_id: UUID,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    sync_service: SyncService = Depends(get_sync_service),
) -> CandidateSyncStatusResponse:
    return sync_service.get_sync_status(sync_id)


@sync_router.get(
    "/{sync_id}/summary",
    response_model=CandidateSyncSummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        404: {"model": ErrorResponse, "description": "Sync id not found"},
    },
    summary="Get candidate sync summary",
    description="Returns sync counts and representative normalization examples for a sync run.",
)
async def get_candidate_sync_summary(
    sync_id: UUID,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    sync_service: SyncService = Depends(get_sync_service),
) -> CandidateSyncSummaryResponse:
    return sync_service.get_sync_summary(sync_id)
