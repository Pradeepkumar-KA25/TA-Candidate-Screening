from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _resolve_fernet() -> Fernet:
    configured_key = settings.integration_encryption_key
    if not configured_key:
        raise ValueError("INTEGRATION_ENCRYPTION_KEY must be configured")

    return Fernet(configured_key.encode("utf-8"))


def encrypt_value(value: str) -> str:
    return _resolve_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None

    try:
        return _resolve_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
