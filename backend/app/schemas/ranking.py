from __future__ import annotations

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class RankedCandidateResponse(BaseModel):
    """A candidate with computed ranking score."""
    id: UUID
    rank: int  # 1-indexed rank in the sorted list
    full_name: str
    zoho_candidate_id: str | None = None
    email: str | None = None
    phone: str | None = None
    current_location: str | None = None
    current_company: str | None = None
    skills: list[str] | None = None
    total_experience_years: float | None = None
    notice_period_days: int | None = None
    score: float  # Raw score (0-100, sum of weighted criteria)
    match_percentage: float  # Match % (0-100, which is score * 100 / 100 = score)
    status: str | None = None


class RankingResponse(BaseModel):
    """Response containing ranked candidates for a JD with given filters."""
    jd_id: UUID
    jd_title: str
    total_candidates: int  # Total candidates after applying filters
    ranked_candidates: list[RankedCandidateResponse]
    filter_summary: dict[str, str | int | float | None] | None = None  # Echo back applied filters


class RankingScoreBreakdownResponse(BaseModel):
    """Detailed breakdown of score computation for a single candidate."""
    candidate_id: UUID
    candidate_name: str
    criterion_name: str
    weight_points: float  # From ranking_criteria
    match_score: float  # Normalized 0-1 match for this criterion
    weighted_contribution: float  # weight_points * match_score
