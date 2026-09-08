from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_logout_rejects_missing_token(sqlite_session, user_factory) -> None:
    user_factory()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "Authentication token is missing"
    finally:
        app.dependency_overrides.clear()


def test_logout_rejects_expired_token(sqlite_session, user_factory) -> None:
    user = user_factory(role="Recruiter")

    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role,
            "iat": int((now - timedelta(minutes=2)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
            "remember_me": False,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post("/api/v1/auth/logout", headers=_auth_header(expired_token))

        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "Authentication token has expired"
    finally:
        app.dependency_overrides.clear()


def test_logout_accepts_valid_token(sqlite_session, user_factory) -> None:
    user = user_factory(role="Recruiter")
    access_token, _, _ = create_access_token(user.id, user.role, remember_me=False)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post("/api/v1/auth/logout", headers=_auth_header(access_token))

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Logout successful"
    finally:
        app.dependency_overrides.clear()


def test_logout_rejects_unauthorized_role(sqlite_session, user_factory) -> None:
    user = user_factory(role="Candidate")
    access_token, _, _ = create_access_token(user.id, user.role, remember_me=False)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post("/api/v1/auth/logout", headers=_auth_header(access_token))

        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "User is not authorized to access this resource"
    finally:
        app.dependency_overrides.clear()
