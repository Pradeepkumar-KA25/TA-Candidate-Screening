from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateShortlistRequest(BaseModel):
    jd_id: UUID
    candidate_ids: list[UUID] = Field(min_length=1)


class ShortlistResponse(BaseModel):
    id: UUID
    recruiter_id: UUID
    jd_id: UUID
    candidate_ids: list[UUID]


class ShortlistCandidateItemResponse(BaseModel):
    id: UUID
    zoho_record_id: str
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


class ShortlistListItemResponse(BaseModel):
    id: UUID
    recruiter_id: UUID
    jd_id: UUID
    jd_code: str
    jd_title: str
    created_at: datetime
    candidate_count: int
    candidates: list[ShortlistCandidateItemResponse]
