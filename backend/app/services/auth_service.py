from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from secrets import token_urlsafe

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWKClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, LoginResponse, MicrosoftLoginRequest, RecruiterProfile


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


class MicrosoftLoginRequiredError(AuthError):
    status_code = 403
    detail = "Use Microsoft sign-in for this account"


class InvalidMicrosoftTokenError(AuthError):
    status_code = 401
    detail = "Microsoft authentication token is invalid or expired"


class UnauthorizedEmailDomainError(AuthError):
    status_code = 403
    detail = "Only organization email accounts are allowed to sign in"


class MicrosoftAuthNotConfiguredError(AuthError):
    status_code = 503
    detail = "Microsoft sign-in is not configured on the server"


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

    def microsoft_login(self, request: MicrosoftLoginRequest) -> LoginResponse:
        if not settings.microsoft_client_id:
            raise MicrosoftAuthNotConfiguredError()

        claims = self._validate_microsoft_id_token(request.id_token)
        email = self._extract_email_claim(claims)
        if not email:
            raise InvalidMicrosoftTokenError()

        if not self._is_migration_email(email) and not self._is_allowed_org_email(email):
            raise UnauthorizedEmailDomainError()

        user = self.repository.get_user_by_email(email)
        if user is None:
            user = self._provision_microsoft_user(email=email, claims=claims)

        if not user.is_active:
            raise InactiveAccountError()

        if user.role not in self.allowed_roles:
            raise UnauthorizedRoleError()

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

    def _migration_login_emails(self) -> set[str]:
        return {
            email.strip().lower()
            for email in settings.migration_login_emails.split(",")
            if email.strip()
        }

    def _is_migration_email(self, email: str) -> bool:
        return email.strip().lower() in self._migration_login_emails()

    def _is_allowed_org_email(self, email: str) -> bool:
        domain = settings.microsoft_allowed_email_domain.strip().lower().lstrip("@")
        normalized_email = email.strip().lower()
        return bool(domain) and normalized_email.endswith(f"@{domain}")

    def _extract_email_claim(self, claims: dict) -> str | None:
        candidate = claims.get("preferred_username") or claims.get("email") or claims.get("upn")
        if not isinstance(candidate, str):
            return None
        return candidate.strip().lower() or None

    def _validate_microsoft_id_token(self, id_token: str) -> dict:
        tenant = settings.microsoft_tenant_id.strip() or "organizations"
        jwks_client = PyJWKClient(f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys")

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.microsoft_client_id,
                options={"verify_signature": True, "verify_exp": True, "verify_aud": True, "verify_iss": False},
            )
        except (InvalidTokenError, ExpiredSignatureError, ValueError):
            raise InvalidMicrosoftTokenError() from None

        issuer = claims.get("iss")
        if not isinstance(issuer, str) or not issuer.startswith("https://login.microsoftonline.com/"):
            raise InvalidMicrosoftTokenError()

        if tenant not in {"common", "organizations", "consumers"}:
            expected_issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"
            if issuer.lower() != expected_issuer.lower():
                raise InvalidMicrosoftTokenError()

        return claims

    def _provision_microsoft_user(self, *, email: str, claims: dict):
        display_name = claims.get("name")
        if not isinstance(display_name, str) or not display_name.strip():
            local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
            display_name = local_part.title() if local_part else "Recruiter User"

        return self.repository.create_user(
            full_name=display_name,
            email=email,
            password_hash=hash_password(token_urlsafe(32)),
            role="Recruiter",
        )

    def logout(self) -> None:
        # JWTs are stateless in this slice; the client must discard stored session state.
        return None
