from __future__ import annotations

from datetime import datetime
from typing import Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposedFieldChangeResponse(BaseModel):
    """Response model for a proposed field change."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    zoho_field_api_name: str
    zoho_field_display_name: str
    existing_zoho_value: Union[str, dict] | None = None
    extracted_resume_value: Union[str, dict] | None = None
    proposed_value: Union[str, dict] | None = None
    change_status: str  # PENDING, APPROVED, REJECTED
    field_approval_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CandidateReviewResponse(BaseModel):
    """Response model for a candidate review."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    candidate_id: UUID
    candidate_name: str
    approval_status: str  # PENDING, APPROVED, REJECTED
    approval_notes: str | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    proposed_changes: list[ProposedFieldChangeResponse] = Field(default_factory=list)


class ReviewBatchResponse(BaseModel):
    """Response model for a review batch."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_number: str
    batch_size: int
    total_candidates: int
    processed_candidates: int
    pending_candidates: int
    approved_candidates: int
    rejected_candidates: int
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    error_message: str | None = None
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ReviewBatchDetailResponse(ReviewBatchResponse):
    """Detailed batch response with candidate list."""

    candidates: list[CandidateReviewResponse] = Field(default_factory=list)


class CreateReviewBatchRequest(BaseModel):
    """Request model for creating a review batch."""

    batch_size: int | None = Field(None, gt=0, le=1000, description="Number of candidates to process")


class ApproveCandidateChangesRequest(BaseModel):
    """Request model for approving proposed changes."""

    field_ids: list[UUID] | None = Field(None, description="Specific field IDs to approve, or None for all")
    notes: str | None = Field(None, max_length=512, description="Optional approval notes")


class RejectCandidateChangesRequest(BaseModel):
    """Request model for rejecting proposed changes."""

    field_ids: list[UUID] | None = Field(None, description="Specific field IDs to reject, or None for all")
    notes: str | None = Field(None, max_length=512, description="Optional rejection notes")


class ReviewBatchListResponse(BaseModel):
    """List response for review batches."""

    batches: list[ReviewBatchResponse]
    total: int
    page: int
    page_size: int


class CandidateReviewListResponse(BaseModel):
    """List response for candidate reviews in a batch."""

    candidates: list[CandidateReviewResponse]
    total: int
    page: int
    page_size: int
