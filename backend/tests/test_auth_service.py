from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthError, AuthService, InactiveAccountError, UnauthorizedRoleError


def test_auth_service_login_success(sqlite_session, user_factory) -> None:
    user = user_factory(password_hash=hash_password("Secret123!"))
    service = AuthService(AuthRepository(sqlite_session))

    response = service.login(LoginRequest(email=user.email, password="Secret123!", remember_me=True))

    assert response.token_type == "bearer"
    assert response.expires_in == settings.remember_me_expire_days * 24 * 60 * 60
    assert response.recruiter.email == user.email
    assert response.recruiter.role == "Recruiter"

    payload = jwt.decode(
        response.access_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(user.id)
    assert payload["role"] == "Recruiter"
    assert payload["remember_me"] is True

    refreshed_user = sqlite_session.scalar(select(User).where(User.id == user.id))
    assert refreshed_user is not None
    assert refreshed_user.last_login_at is not None


def test_auth_service_rejects_invalid_credentials(sqlite_session, user_factory) -> None:
    user = user_factory(password_hash=hash_password("Secret123!"))
    service = AuthService(AuthRepository(sqlite_session))

    with pytest.raises(AuthError) as exc_info:
        service.login(LoginRequest(email=user.email, password="WrongPassword"))

    assert exc_info.value.detail == "Invalid credentials"


def test_auth_service_rejects_unknown_email(sqlite_session, user_factory) -> None:
    user_factory(password_hash=hash_password("Secret123!"))
    service = AuthService(AuthRepository(sqlite_session))

    with pytest.raises(AuthError) as exc_info:
        service.login(LoginRequest(email="unknown@example.com", password="Secret123!"))

    assert exc_info.value.detail == "Invalid credentials"


def test_auth_service_rejects_inactive_user(sqlite_session, user_factory) -> None:
    user = user_factory(password_hash=hash_password("Secret123!"), is_active=False)
    service = AuthService(AuthRepository(sqlite_session))

    with pytest.raises(InactiveAccountError) as exc_info:
        service.login(LoginRequest(email=user.email, password="Secret123!"))

    assert exc_info.value.detail == "Recruiter account is disabled"


def test_auth_service_rejects_unauthorized_role(sqlite_session, user_factory) -> None:
    user = user_factory(password_hash=hash_password("Secret123!"), role="Candidate")
    service = AuthService(AuthRepository(sqlite_session))

    with pytest.raises(UnauthorizedRoleError) as exc_info:
        service.login(LoginRequest(email=user.email, password="Secret123!"))

    assert exc_info.value.detail == "User is not authorized to sign in"
