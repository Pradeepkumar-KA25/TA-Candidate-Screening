from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RankingCriteriaItemRequest(BaseModel):
    """Single ranking criterion in a create/update request."""
    criteria_name: str = Field(min_length=1, max_length=255)
    weight_points: float = Field(gt=0, le=100)

    @field_validator("criteria_name")
    @classmethod
    def normalize_criteria_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Criteria name is required")
        return normalized

    @field_validator("weight_points")
    @classmethod
    def validate_weight(cls, value: float) -> float:
        if value <= 0 or value > 100:
            raise ValueError("Weight points must be between 0 (exclusive) and 100 (inclusive)")
        return value


class SetRankingCriteriaRequest(BaseModel):
    """Request to set/replace all ranking criteria for a JD."""
    criteria: list[RankingCriteriaItemRequest] = Field(min_length=1, max_length=100)

    @field_validator("criteria")
    @classmethod
    def validate_weight_sum(cls, value: list[RankingCriteriaItemRequest]) -> list[RankingCriteriaItemRequest]:
        total_weight = sum(item.weight_points for item in value)
        if total_weight != 100.0:
            raise ValueError(f"Total weight points must equal 100, got {total_weight}")
        return value


class RankingCriteriaItemResponse(BaseModel):
    """Single ranking criterion in response."""
    id: UUID
    jd_id: UUID
    criteria_name: str
    weight_points: float
    created_at: datetime


class GetRankingCriteriaResponse(BaseModel):
    """Response containing all ranking criteria for a JD."""
    jd_id: UUID
    criteria: list[RankingCriteriaItemResponse]
    total_weight: float = Field(description="Sum of all weight_points (should be 100)")
