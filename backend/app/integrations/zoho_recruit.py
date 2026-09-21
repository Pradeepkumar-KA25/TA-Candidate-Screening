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

    def fetch_candidate_attachments(self, access_token: str, candidate_id: str) -> list[dict]:
        """Fetch all attachments for a candidate."""
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        # Correct endpoint: /Candidates/{zoho_record_id}/Attachments
        endpoint = f"{self._base_url}/Candidates/{candidate_id}/Attachments"

        response = self._send_get(endpoint=endpoint, headers=headers, params={})
        if response.status_code in {429, 500, 502, 503, 504}:
            raise ZohoRecruitTransientError(f"Zoho attachment fetch transient error: HTTP {response.status_code}")

        if response.status_code == 404:
            # No attachments found
            return []

        if response.status_code >= 400:
            raise ZohoRecruitPermanentError(f"Zoho attachment fetch error: HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ZohoRecruitPermanentError("Zoho attachment API returned non-JSON response") from exc

        data = payload.get("data")
        if not isinstance(data, list):
            return []

        return [item for item in data if isinstance(item, dict)]

    def download_attachment(self, access_token: str, candidate_id: str, attachment_id: str) -> bytes:
        """Download an attachment file content from Zoho Recruit.
        
        IMPORTANT: Requires the OAuth token to have 'Attachments.Read' or equivalent
        download permissions granted in Zoho Admin Console. If you get 'IAMSecurityError',
        the connected app lacks file download permissions.
        
        Args:
            access_token: Zoho API access token
            candidate_id: Zoho Candidate ID (required - endpoint needs candidate context)
            attachment_id: Zoho Attachment ID
        
        Returns:
            Binary file content (PDF, DOCX, etc.)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        
        # The correct endpoint requires BOTH candidate_id and attachment_id
        # /recruit/v2/Candidates/{candidate_id}/Attachments/{attachment_id}
        attachment_endpoint = f"{self._base_url}/Candidates/{candidate_id}/Attachments/{attachment_id}"
        
        # Try different header variations with the correct endpoint
        attempts = [
            # Attempt 1: Default (works with proper permission)
            (attachment_endpoint, headers),
            
            # Attempt 2: With explicit octet-stream
            (attachment_endpoint, {**headers, "Accept": "application/octet-stream"}),
            
            # Attempt 3: Accept anything
            (attachment_endpoint, {**headers, "Accept": "*/*"}),
        ]
        
        last_error = None
        iam_error_detected = False
        
        for endpoint_url, request_headers in attempts:
            try:
                logger.debug(f"Attempting download from: {endpoint_url}")
                
                if self._client is not None:
                    response = self._client.get(endpoint_url, headers=request_headers, follow_redirects=False)
                else:
                    with httpx.Client(timeout=settings.zoho_connection_timeout_seconds) as client:
                        response = client.get(endpoint_url, headers=request_headers, follow_redirects=False)
                
                logger.debug(f"Response - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}, Size: {len(response.content)}")
                
                # Check for IAM security errors (HTTP 302 redirect to IAMSecurityError)
                if response.status_code == 302:
                    location = response.headers.get('location', '')
                    if 'IAMSecurityError' in location or 'iam' in location.lower():
                        iam_error_detected = True
                        logger.error(f"IAM Security Error: OAuth token lacks attachment download permissions. Location: {location}")
                        last_error = "OAuth token lacks 'Attachments.Read' or file download permissions. Contact your Zoho admin to grant this permission to the connected app."
                        continue
                
                # Handle transient errors
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise ZohoRecruitTransientError(f"Zoho API transient error: HTTP {response.status_code}")
                
                # If we got an error (4xx or 5xx), log and try next
                if response.status_code >= 400:
                    error_msg = response.content[:200].decode('utf-8', errors='ignore')
                    logger.debug(f"HTTP {response.status_code}: {error_msg}")
                    last_error = f"HTTP {response.status_code}"
                    continue
                
                # Success response - check content type
                if not response.content:
                    logger.debug("Response is empty")
                    continue
                
                content_type = response.headers.get('content-type', '').lower()
                first_bytes = response.content[:10]
                
                # Check if this is JSON (metadata response)
                if 'json' in content_type or first_bytes.startswith(b'{') or first_bytes.startswith(b'['):
                    logger.debug(f"Got JSON response (metadata), not file content")
                    
                    # Try to extract download link from metadata
                    try:
                        import json
                        metadata = json.loads(response.content)
                        # Check if metadata has download URL or direct content
                        if isinstance(metadata, dict):
                            data = metadata.get('data')
                            if isinstance(data, list) and len(data) > 0:
                                attachment_data = data[0]
                                # Look for direct download URL or file_id hints
                                logger.debug(f"Metadata keys: {list(attachment_data.keys())}")
                    except Exception as e:
                        logger.debug(f"Could not parse metadata: {e}")
                    
                    # Metadata endpoints won't work, try next
                    continue
                
                # Check for valid file signatures
                is_pdf = first_bytes.startswith(b'%PDF')
                is_docx = first_bytes.startswith(b'PK')  # ZIP format
                is_doc = first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']  # MS Office OLE
                
                if is_pdf or is_docx or is_doc or len(response.content) > 1000:
                    logger.info(f"✓ Successfully downloaded {len(response.content)} bytes (PDF:{is_pdf}, DOCX:{is_docx}, DOC:{is_doc})")
                    return response.content
                else:
                    logger.debug(f"Unexpected file signature: {first_bytes.hex()[:20]}")
                    continue
                    
            except ZohoRecruitTransientError:
                # Re-raise transient errors to retry elsewhere
                raise
            except httpx.TimeoutException as exc:
                logger.debug(f"Timeout during download attempt")
                raise ZohoRecruitTransientError("Zoho attachment download timed out") from exc
            except httpx.HTTPError as exc:
                logger.debug(f"HTTP error: {exc}")
                last_error = str(exc)
                continue
            except Exception as exc:
                logger.debug(f"Unexpected error: {exc}")
                last_error = str(exc)
                continue
        
        # All attempts failed
        if iam_error_detected:
            error_msg = f"Zoho attachment download blocked by IAM security policy. The OAuth token lacks 'Attachments.Read' or file download permissions. Contact your Zoho admin to grant this permission to the connected app in Settings > Connected Apps > [Your App] > Scopes."
        else:
            error_msg = f"Could not download attachment. Last error: {last_error}. If you're seeing permission errors, your Zoho admin may need to grant file download permissions to the connected app."
        logger.error(error_msg)
        raise ZohoRecruitPermanentError(error_msg)

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
