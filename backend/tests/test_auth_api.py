from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.dependencies import get_auth_service
from app.main import app
from app.schemas.auth import LoginResponse, RecruiterProfile
from app.services.auth_service import AuthError, InactiveAccountError


class FakeAuthService:
    def __init__(self, response: LoginResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    def login(self, request):
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise RuntimeError("FakeAuthService requires a response or error")
        return self.response


def test_login_endpoint_success() -> None:
    service = FakeAuthService(
        response=LoginResponse(
            access_token="test-token",
            expires_in=3600,
            recruiter=RecruiterProfile(
                id="11111111-1111-1111-1111-111111111111",
                full_name="Asha Sharma",
                email="asha.sharma@example.com",
                role="Recruiter",
            ),
        )
    )

    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "asha.sharma@example.com", "password": "Secret123!", "remember_me": False},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["recruiter"]["email"] == "asha.sharma@example.com"
    finally:
        app.dependency_overrides.clear()


def test_login_endpoint_rejects_invalid_credentials() -> None:
    service = FakeAuthService(error=AuthError())

    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "asha.sharma@example.com", "password": "WrongPassword", "remember_me": False},
        )

        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "Invalid credentials"
        assert body["path"] == "/api/v1/auth/login"
    finally:
        app.dependency_overrides.clear()


def test_login_endpoint_rejects_unknown_email() -> None:
    service = FakeAuthService(error=AuthError())

    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "Secret123!", "remember_me": False},
        )

        assert response.status_code == 401
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "Invalid credentials"
        assert body["path"] == "/api/v1/auth/login"
    finally:
        app.dependency_overrides.clear()


def test_login_endpoint_rejects_inactive_account() -> None:
    service = FakeAuthService(error=InactiveAccountError())

    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "asha.sharma@example.com", "password": "Secret123!", "remember_me": False},
        )

        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
        assert body["message"] == "Recruiter account is disabled"
        assert body["path"] == "/api/v1/auth/login"
    finally:
        app.dependency_overrides.clear()


def test_login_endpoint_returns_validation_error_shape() -> None:
    service = FakeAuthService(error=AuthError())

    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "asha.sharma@example.com", "remember_me": False},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert body["message"] == "Malformed request payload"
        assert body["path"] == "/api/v1/auth/login"
        assert isinstance(body["details"], list)
    finally:
        app.dependency_overrides.clear()
