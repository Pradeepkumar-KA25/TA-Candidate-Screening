from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(pattern="^(Recruiter|Admin)$")


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, pattern="^(Recruiter|Admin)$")
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=255)