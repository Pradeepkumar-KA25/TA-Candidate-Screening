from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_candidates: int
    last_sync_at: datetime | None = None
    current_shortlist_size: int
    saved_filter_count: int
    new_candidates: int = 0
    shortlisted_candidates: int = 0
    interview_candidates: int = 0
    pending_duplicates: int = 0
    last_sync_status: str | None = None
    last_sync_new: int = 0
    last_sync_updated: int = 0
    last_sync_errors: int = 0
    pipeline: list["DashboardCountItem"] = []
    source_breakdown: list["DashboardCountItem"] = []
    needs_attention: list["DashboardAttentionItem"] = []
    resume_enrichment: "DashboardEnrichmentStats | None" = None
    activity_summary: list["DashboardCountItem"] = []


class DashboardCountItem(BaseModel):
    label: str
    count: int


class DashboardAttentionItem(BaseModel):
    label: str
    count: int
    route: str


class DashboardActivityItemResponse(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    action_type: str
    description: str
    entity_type: str | None = None
    entity_id: str | None = None
    result: str
    metadata: dict | None = None
    occurred_at: datetime


class DashboardRecentActivityResponse(BaseModel):
    items: list[DashboardActivityItemResponse]


class DashboardEnrichmentStats(BaseModel):
    pending_batches: int = 0
    pending_reviews: int = 0
    approved_reviews: int = 0
    rejected_reviews: int = 0


class DashboardSeriesPoint(BaseModel):
    label: str
    value: int


class DashboardAnalyticsResponse(BaseModel):
    days: int
    candidate_growth: list[DashboardSeriesPoint] = []
    pipeline: list[DashboardCountItem] = []
    sources: list[DashboardCountItem] = []
    sync_outcomes: list[DashboardCountItem] = []
    enrichment_outcomes: list[DashboardCountItem] = []
    activity_by_action: list[DashboardCountItem] = []
