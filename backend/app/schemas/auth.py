from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    remember_me: bool = False

    model_config = ConfigDict(str_strip_whitespace=True)


class RecruiterProfile(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: str
    last_login_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    recruiter: RecruiterProfile


class LogoutResponse(BaseModel):
    message: str
