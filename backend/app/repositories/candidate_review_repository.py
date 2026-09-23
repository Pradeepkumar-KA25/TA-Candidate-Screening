from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.candidate_review import CandidateReview


class CandidateReviewRepository:
    """Repository for managing candidate reviews."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        batch_id: UUID,
        candidate_id: UUID,
        candidate_name: str,
        zoho_candidate_id: str | None = None,
    ) -> CandidateReview:
        """Create a new candidate review."""
        review = CandidateReview(
            batch_id=batch_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            zoho_candidate_id=zoho_candidate_id,
        )
        self.session.add(review)
        self.session.flush()
        return review

    def get_by_id(self, candidate_review_id: UUID) -> CandidateReview | None:
        """Get candidate review by ID."""
        return self.session.query(CandidateReview).filter(CandidateReview.id == candidate_review_id).first()

    def get_by_batch_id(self, batch_id: UUID) -> list[CandidateReview]:
        """Get all candidate reviews in a batch."""
        return self.session.query(CandidateReview).filter(CandidateReview.batch_id == batch_id).all()

    def get_by_batch_id_paginated(
        self, batch_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[CandidateReview], int]:
        """Get candidate reviews in a batch with pagination."""
        query = self.session.query(CandidateReview).filter(CandidateReview.batch_id == batch_id)
        total = query.count()
        reviews = query.offset((page - 1) * page_size).limit(page_size).all()
        return reviews, total

    def get_by_approval_status(self, batch_id: UUID, status: str) -> list[CandidateReview]:
        """Get candidate reviews with specific approval status in a batch."""
        return (
            self.session.query(CandidateReview)
            .filter(CandidateReview.batch_id == batch_id, CandidateReview.approval_status == status)
            .all()
        )

    def update_approval_status(
        self,
        candidate_review_id: UUID,
        status: str,
        user_id: UUID | None = None,
        notes: str | None = None,
    ) -> CandidateReview | None:
        """Update approval status."""
        review = self.get_by_id(candidate_review_id)
        if review:
            review.approval_status = status
            if user_id:
                review.reviewed_by_user_id = user_id
            if notes:
                review.approval_notes = notes
            review.reviewed_at = datetime.now(timezone.utc)
            self.session.flush()
        return review
