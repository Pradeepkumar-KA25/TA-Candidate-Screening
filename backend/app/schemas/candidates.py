from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CandidateListItemResponse(BaseModel):
    id: UUID
    zoho_candidate_id: str | None = None
    full_name: str
    skills: list[str] | None = None
    total_experience_years: float | None = None
    current_location: str | None = None
    current_company: str | None = None
    notice_period_days: int | None = None
    status: str | None = None
    match_percentage: float | None = None
    updated_at: datetime


class CandidateListResponse(BaseModel):
    items: list[CandidateListItemResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    q: str | None = None
    sort_by: str
    sort_order: str


class CandidateNormalizedPairResponse(BaseModel):
    field: str
    raw_value: str
    normalized_value: str


class CandidateMatchContextResponse(BaseModel):
    jd_id: str | None = None
    jd_title: str | None = None
    match_percentage: float | None = None
    match_score: float | None = None
    matched_criteria: list[str] | None = None
    metadata: dict[str, Any] | None = None


class CandidateDetailResponse(BaseModel):
    id: UUID
    zoho_candidate_id: str | None = None
    full_name: str
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None
    relevant_experience_years: float | None = None
    current_company: str | None = None
    current_location: str | None = None
    preferred_location: str | None = None
    notice_period_days: int | None = None
    skills: list[str] | None = None
    degree: str | None = None
    normalized_degree: str | None = None
    current_ctc: float | None = None
    expected_ctc: float | None = None
    status: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime
    normalized_data: list[CandidateNormalizedPairResponse]
    match_context: CandidateMatchContextResponse
