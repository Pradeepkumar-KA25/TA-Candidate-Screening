from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json


def as_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def parse_zoho_modified_time(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return as_utc(value)
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return as_utc(datetime.fromisoformat(value.strip().replace("Z", "+00:00")))
    except ValueError:
        return None


def candidate_payload_hash(raw_candidate: dict) -> str:
    serialized = json.dumps(raw_candidate, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
