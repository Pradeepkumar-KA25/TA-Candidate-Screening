from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DuplicateCandidateSnapshotResponse(BaseModel):
    id: UUID
    zoho_candidate_id: str | None = None
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_company: str | None = None
    current_location: str | None = None
    total_experience_years: float | None = None


class DuplicatePairResponse(BaseModel):
    id: UUID
    match_basis: str
    confidence: float
    status: str
    created_at: datetime
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    candidate: DuplicateCandidateSnapshotResponse
    matched_candidate: DuplicateCandidateSnapshotResponse


class DuplicateGroupResponse(BaseModel):
    jd_id: UUID | None = None
    jd_code: str | None = None
    jd_title: str | None = None
    duplicate_count: int
    items: list[DuplicatePairResponse]


class DuplicateSummaryResponse(BaseModel):
    job_descriptions_reviewed: int
    possible_duplicates: int
    no_duplicate_signal: int
    unassigned_duplicates: int


class DuplicateGroupedResponse(BaseModel):
    summary: DuplicateSummaryResponse
    groups: list[DuplicateGroupResponse]
