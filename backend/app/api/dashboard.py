from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_dashboard_service, require_roles
from app.models.user import User
from app.schemas.dashboard import DashboardRecentActivityResponse, DashboardStatsResponse
from app.schemas.errors import ErrorResponse
from app.services.dashboard_service import DashboardService


dashboard_router = APIRouter()


@dashboard_router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="Get dashboard stats",
    description="Returns dashboard counters for candidates, shortlist size, saved filters, and the latest sync timestamp.",
)
async def get_dashboard_stats(
    current_recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    return dashboard_service.get_stats(current_recruiter.id)


@dashboard_router.get(
    "/recent-activity",
    response_model=DashboardRecentActivityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="Get dashboard recent activity",
    description="Returns the most recent recruiter-owned activity log entries in reverse chronological order.",
)
async def get_dashboard_recent_activity(
    current_recruiter: User = Depends(require_roles("Recruiter", "Admin")),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of activity entries to return"),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardRecentActivityResponse:
    return dashboard_service.get_recent_activity(current_recruiter.id, limit=limit)