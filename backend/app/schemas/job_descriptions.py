from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateJobDescriptionRequest(BaseModel):
    jd_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    required_skills: list[str] = Field(default_factory=list)

    @field_validator("jd_code")
    @classmethod
    def normalize_jd_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("JD code is required")
        return normalized

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("JD title is required")
        return normalized

    @field_validator("required_skills")
    @classmethod
    def normalize_required_skills(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for skill in value:
            text = str(skill).strip()
            if text:
                normalized.append(text)
        return normalized


class JobDescriptionListItemResponse(BaseModel):
    id: UUID
    jd_code: str
    title: str
    required_skills: list[str] = Field(default_factory=list)


class JobDescriptionResponse(BaseModel):
    id: UUID
    jd_code: str
    title: str
    required_skills: list[str]
    created_at: datetime
