from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: UUID, role: str, remember_me: bool) -> tuple[str, int, datetime]:
    now = datetime.now(UTC)
    expires_delta = (
        timedelta(days=settings.remember_me_expire_days)
        if remember_me
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "remember_me": remember_me,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds()), expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise ExpiredSignatureError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise InvalidTokenError("Invalid authentication token") from exc

    return payload