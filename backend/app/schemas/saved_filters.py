from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SaveFilterRequest(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    jd_id: UUID | None = None
    filter_criteria: dict[str, Any]

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Filter name is required")
        return normalized


class SavedFilterResponse(BaseModel):
    id: UUID
    recruiter_id: UUID
    name: str
    jd_id: UUID | None
    filter_criteria: dict[str, Any]
    resolved_query_params: dict[str, str]
    created_at: datetime
    updated_at: datetime
    warning: str | None = None
