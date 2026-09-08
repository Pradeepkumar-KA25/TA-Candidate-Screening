from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_auth_service, require_roles
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from app.services.auth_service import AuthService

auth_router = APIRouter()


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Inactive or unauthorized recruiter account"},
    },
    summary="Authenticate a recruiter",
    description="Validates recruiter credentials and returns a JWT access token with recruiter profile data.",
)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    return auth_service.login(request)


@auth_router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Missing, invalid, or expired token"},
        403: {"description": "Role is not allowed to access this endpoint"},
    },
    summary="Logout current recruiter session",
    description=(
        "Acknowledges recruiter logout for stateless JWT auth. "
        "Clients must clear local auth/session state after this call."
    ),
)
async def logout(
    _: User = Depends(require_roles("Recruiter", "Admin")),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    auth_service.logout()
    return LogoutResponse(message="Logout successful")
