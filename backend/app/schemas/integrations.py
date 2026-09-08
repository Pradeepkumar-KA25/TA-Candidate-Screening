from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ZohoIntegrationStatusResponse(BaseModel):
    integration: str
    connection_state: str
    status: str
    access_level: str
    sync_type: str
    last_successful_sync_at: datetime | None = None
    last_checked_at: datetime


class ZohoFieldMetadataResponse(BaseModel):
    api_name: str
    display_label: str
    data_type: str


class ZohoCandidateDiagnosticsResponse(BaseModel):
    integration: str
    connection_state: str
    status: str
    candidate_field_count: int
    field_metadata: list[ZohoFieldMetadataResponse]
    live_sample_payload_keys: list[str]
    latest_synced_payload_keys: list[str]
    current_mapping_targets: dict[str, list[str]]
    likely_matches: dict[str, list[ZohoFieldMetadataResponse]]
    metadata_error: str | None = None
    live_sample_error: str | None = None
