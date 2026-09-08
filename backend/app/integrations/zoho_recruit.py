from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import time

import httpx

from app.core.config import settings


class ZohoRecruitClientError(Exception):
    pass


class ZohoRecruitTransientError(ZohoRecruitClientError):
    pass


class ZohoRecruitPermanentError(ZohoRecruitClientError):
    pass


@dataclass(slots=True)
class ZohoCandidatesPage:
    candidates: list[dict]
    has_more: bool


@dataclass(slots=True)
class ZohoFieldMetadata:
    api_name: str
    display_label: str
    data_type: str


class ZohoRecruitClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client
        self._base_url = settings.zoho_recruit_base_url.rstrip("/")

    def iter_candidates(self, access_token: str, per_page: int = 200, fields: list[str] | None = None) -> Iterator[dict]:
        page = 1
        while True:
            page_payload = self._fetch_candidates_page_with_retry(
                access_token=access_token,
                page=page,
                per_page=per_page,
                fields=fields,
            )
            for item in page_payload.candidates:
                yield item

            if not page_payload.has_more:
                break
            page += 1

    def _fetch_candidates_page_with_retry(
        self, *, access_token: str, page: int, per_page: int, fields: list[str] | None = None
    ) -> ZohoCandidatesPage:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                return self.fetch_candidates_page(access_token=access_token, page=page, per_page=per_page, fields=fields)
            except ZohoRecruitTransientError as exc:
                last_error = exc
                # Exponential backoff for transient upstream failures.
                time.sleep(0.25 * (2 ** attempt))

        raise ZohoRecruitTransientError(f"Zoho candidate fetch failed after retries: {last_error}")

    def fetch_candidates_page(
        self, *, access_token: str, page: int, per_page: int, fields: list[str] | None = None
    ) -> ZohoCandidatesPage:
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        params = {"page": page, "per_page": per_page}
        if fields:
            params["fields"] = ",".join(item.strip() for item in fields if item and item.strip())
        endpoint = f"{self._base_url}/Candidates"

        response = self._send_get(endpoint=endpoint, headers=headers, params=params)
        if response.status_code in {429, 500, 502, 503, 504}:
            raise ZohoRecruitTransientError(f"Zoho API transient error: HTTP {response.status_code}")

        if response.status_code >= 400:
            raise ZohoRecruitPermanentError(f"Zoho API error: HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ZohoRecruitPermanentError("Zoho API returned non-JSON response") from exc

        data = payload.get("data")
        if not isinstance(data, list):
            raise ZohoRecruitPermanentError("Zoho API response missing data list")

        info = payload.get("info", {})
        more_records = bool(info.get("more_records")) if isinstance(info, dict) else False
        candidates = [item for item in data if isinstance(item, dict)]
        return ZohoCandidatesPage(candidates=candidates, has_more=more_records)

    def fetch_candidate_field_metadata(self, access_token: str) -> list[ZohoFieldMetadata]:
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        endpoint = f"{self._base_url}/settings/fields"
        params = {"module": "Candidates"}

        response = self._send_get(endpoint=endpoint, headers=headers, params=params)
        if response.status_code in {429, 500, 502, 503, 504}:
            raise ZohoRecruitTransientError(f"Zoho field metadata transient error: HTTP {response.status_code}")

        if response.status_code >= 400:
            raise ZohoRecruitPermanentError(f"Zoho field metadata error: HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ZohoRecruitPermanentError("Zoho field metadata returned non-JSON response") from exc

        data = payload.get("fields") or payload.get("data")
        if not isinstance(data, list):
            raise ZohoRecruitPermanentError("Zoho field metadata response missing fields list")

        items: list[ZohoFieldMetadata] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            api_name = item.get("api_name")
            label = item.get("field_label") or item.get("display_label") or item.get("api_name")
            data_type = item.get("data_type") or "unknown"
            if not isinstance(api_name, str) or not api_name.strip():
                continue
            items.append(
                ZohoFieldMetadata(
                    api_name=api_name.strip(),
                    display_label=str(label).strip(),
                    data_type=str(data_type).strip(),
                )
            )

        return items

    def _send_get(self, *, endpoint: str, headers: dict[str, str], params: dict[str, str | int]) -> httpx.Response:
        try:
            if self._client is not None:
                return self._client.get(endpoint, headers=headers, params=params)

            with httpx.Client(timeout=settings.zoho_connection_timeout_seconds) as client:
                return client.get(endpoint, headers=headers, params=params)
        except httpx.TimeoutException as exc:
            raise ZohoRecruitTransientError("Zoho API request timed out") from exc
        except httpx.HTTPError as exc:
            raise ZohoRecruitTransientError("Zoho API request failed") from exc
