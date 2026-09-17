from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_integration_service, require_roles
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.integrations import AutoSyncSettingsRequest, ZohoCandidateDiagnosticsResponse, ZohoIntegrationStatusResponse
from app.services.integration_service import IntegrationService


integrations_router = APIRouter()


@integrations_router.get(
    "/zoho/status",
    response_model=ZohoIntegrationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Zoho Recruit integration status",
    description=(
        "Returns current Zoho Recruit integration state including connectivity, "
        "access level, sync type, and last successful sync timestamp."
    ),
)
async def get_zoho_status(
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ZohoIntegrationStatusResponse:
    return integration_service.get_zoho_status()


@integrations_router.put(
    "/zoho/auto-sync",
    response_model=ZohoIntegrationStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
    },
    summary="Update Zoho auto-sync settings",
    description=(
        "Enables or disables automatic synchronization from Zoho Recruit. "
        "When enabled, candidates are synced automatically at the specified interval."
    ),
)
async def update_zoho_auto_sync(
    settings: AutoSyncSettingsRequest,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ZohoIntegrationStatusResponse:
    return integration_service.update_auto_sync_settings(settings.auto_sync_enabled, settings.auto_sync_interval_minutes)


@integrations_router.get(
    "/zoho/candidates/diagnostics",
    response_model=ZohoCandidateDiagnosticsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid, or expired token"},
        403: {"model": ErrorResponse, "description": "Role is not allowed to access this endpoint"},
        409: {"model": ErrorResponse, "description": "Zoho diagnostics could not be fetched"},
    },
    summary="Get Zoho candidate diagnostics",
    description=(
        "Returns Zoho Candidate field metadata, current mapper targets, a live sample payload key set, and the "
        "latest synced raw payload key set to help align sync field mappings."
    ),
)
async def get_zoho_candidate_diagnostics(
    _: User = Depends(require_roles("Recruiter", "Admin")),
    integration_service: IntegrationService = Depends(get_integration_service),
) -> ZohoCandidateDiagnosticsResponse:
    return integration_service.get_zoho_candidate_diagnostics()
