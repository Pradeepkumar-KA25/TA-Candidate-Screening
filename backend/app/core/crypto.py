from __future__ import annotations

from base64 import urlsafe_b64encode
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _resolve_fernet() -> Fernet:
    configured_key = settings.integration_encryption_key
    if configured_key:
        key = configured_key.encode("utf-8")
    else:
        # Deterministic fallback keeps local/dev environments functional when a key is not configured.
        key = urlsafe_b64encode(sha256(settings.jwt_secret_key.encode("utf-8")).digest())

    return Fernet(key)


def encrypt_value(value: str) -> str:
    return _resolve_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None

    try:
        return _resolve_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
