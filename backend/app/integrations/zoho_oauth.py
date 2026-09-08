from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass(slots=True)
class ZohoTokenRefreshResult:
    access_token: str
    expires_in: int
    scope: str | None = None


class ZohoOAuthClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def refresh_access_token(self, refresh_token: str) -> ZohoTokenRefreshResult | None:
        if not settings.zoho_client_id or not settings.zoho_client_secret:
            return None

        endpoint = f"{settings.zoho_accounts_base_url.rstrip('/')}/oauth/v2/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.zoho_client_id,
            "client_secret": settings.zoho_client_secret,
        }

        try:
            if self._client is not None:
                response = self._client.post(endpoint, data=payload)
            else:
                with httpx.Client(timeout=settings.zoho_connection_timeout_seconds) as client:
                    response = client.post(endpoint, data=payload)

            response.raise_for_status()
            body = response.json()
            access_token = body.get("access_token")
            if not isinstance(access_token, str) or not access_token.strip():
                return None

            expires_raw = body.get("expires_in") or body.get("expires_in_sec")
            try:
                expires_in = int(expires_raw)
            except (TypeError, ValueError):
                expires_in = 3600

            scope = body.get("scope") if isinstance(body.get("scope"), str) else None
            return ZohoTokenRefreshResult(access_token=access_token, expires_in=expires_in, scope=scope)
        except (httpx.HTTPError, ValueError):
            return None
