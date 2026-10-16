from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_activity_log_repository, get_auth_service, require_roles
from app.repositories.activity_log_repository import ActivityLogRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, MicrosoftLoginRequest
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
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> LoginResponse:
    response = auth_service.login(request)
    actor_id = response.recruiter.id if activity_log_repository.session.get(User, response.recruiter.id) else None
    activity_log_repository.create(
        actor_id=actor_id,
        action_type="user_logged_in",
        description="User signed in",
        entity_type="user",
        entity_id=response.recruiter.id,
    )
    return response


@auth_router.post(
    "/microsoft-login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Invalid Microsoft token or unknown user"},
        403: {"description": "Inactive, unauthorized, or non-organization account"},
    },
    summary="Authenticate using Microsoft account",
    description="Validates Microsoft ID token and returns a JWT access token with recruiter profile data.",
)
async def microsoft_login(
    request: MicrosoftLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> LoginResponse:
    response = auth_service.microsoft_login(request)
    actor_id = response.recruiter.id if activity_log_repository.session.get(User, response.recruiter.id) else None
    activity_log_repository.create(
        actor_id=actor_id,
        action_type="user_logged_in",
        description="User signed in via Microsoft account",
        entity_type="user",
        entity_id=response.recruiter.id,
    )
    return response


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
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
    auth_service: AuthService = Depends(get_auth_service),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> LogoutResponse:
    auth_service.logout()
    activity_log_repository.create(
        actor_id=current_user.id,
        action_type="user_logged_out",
        description="User signed out",
        entity_type="user",
        entity_id=current_user.id,
    )
    return LogoutResponse(message="Logout successful")
