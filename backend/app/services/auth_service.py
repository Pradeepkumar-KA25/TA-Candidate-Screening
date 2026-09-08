from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.security import create_access_token, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, LoginResponse, RecruiterProfile


class AuthError(Exception):
    status_code = 401
    detail = "Invalid credentials"


class InactiveAccountError(AuthError):
    status_code = 403
    detail = "Recruiter account is disabled"


class UnauthorizedRoleError(AuthError):
    status_code = 403
    detail = "User is not authorized to sign in"


class MissingTokenError(AuthError):
    status_code = 401
    detail = "Authentication token is missing"


class InvalidTokenError(AuthError):
    status_code = 401
    detail = "Authentication token is invalid"


class ExpiredTokenError(AuthError):
    status_code = 401
    detail = "Authentication token has expired"


class AccessDeniedError(AuthError):
    status_code = 403
    detail = "User is not authorized to access this resource"


@dataclass(slots=True)
class AuthService:
    repository: AuthRepository

    allowed_roles: tuple[str, ...] = ("Recruiter", "Admin")

    def login(self, request: LoginRequest) -> LoginResponse:
        user = self.repository.get_user_by_email(request.email)
        if user is None:
            raise AuthError()

        if not user.is_active:
            raise InactiveAccountError()

        if user.role not in self.allowed_roles:
            raise UnauthorizedRoleError()

        if not verify_password(request.password, user.password_hash):
            raise AuthError()

        access_token, expires_in, _ = create_access_token(
            user_id=user.id,
            role=user.role,
            remember_me=request.remember_me,
        )
        self.repository.update_last_login(user.id)

        return LoginResponse(
            access_token=access_token,
            expires_in=expires_in,
            recruiter=RecruiterProfile(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                last_login_at=datetime.now(UTC),
            ),
        )

    def logout(self) -> None:
        # JWTs are stateless in this slice; the client must discard stored session state.
        return None
