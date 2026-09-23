from __future__ import annotations

from uuid import UUID

from sqlalchemy import cast, func, select, Integer
from sqlalchemy.orm import Session

from app.models.review_batch import ReviewBatch


class ReviewBatchRepository:
    """Repository for managing review batches."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        batch_number: str,
        batch_size: int,
        total_candidates: int,
        created_by_user_id: UUID | None = None,
    ) -> ReviewBatch:
        """Create a new review batch."""
        batch = ReviewBatch(
            batch_number=batch_number,
            batch_size=batch_size,
            total_candidates=total_candidates,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(batch)
        self.session.flush()
        return batch

    def get_by_id(self, batch_id: UUID) -> ReviewBatch | None:
        """Get batch by ID."""
        return self.session.query(ReviewBatch).filter(ReviewBatch.id == batch_id).first()

    def get_by_batch_number(self, batch_number: str) -> ReviewBatch | None:
        """Get batch by batch number."""
        return self.session.query(ReviewBatch).filter(ReviewBatch.batch_number == batch_number).first()

    def get_paginated(self, page: int = 1, page_size: int = 10) -> tuple[list[ReviewBatch], int]:
        """Get batches with pagination."""
        query = self.session.query(ReviewBatch).order_by(ReviewBatch.created_at.desc())
        total = query.count()
        batches = query.offset((page - 1) * page_size).limit(page_size).all()
        return batches, total

    def update_status(self, batch_id: UUID, status: str) -> ReviewBatch | None:
        """Update batch status."""
        batch = self.get_by_id(batch_id)
        if batch:
            batch.status = status
            if status == "PROCESSING":
                from datetime import datetime, timezone

                batch.processing_started_at = datetime.now(timezone.utc)
            elif status == "COMPLETED":
                from datetime import datetime, timezone

                batch.processing_completed_at = datetime.now(timezone.utc)
            self.session.flush()
        return batch

    def update_candidates_count(
        self,
        batch_id: UUID,
        processed: int | None = None,
        pending: int | None = None,
        approved: int | None = None,
        rejected: int | None = None,
    ) -> ReviewBatch | None:
        """Update candidate counts."""
        batch = self.get_by_id(batch_id)
        if batch:
            if processed is not None:
                batch.processed_candidates = processed
            if pending is not None:
                batch.pending_candidates = pending
            if approved is not None:
                batch.approved_candidates = approved
            if rejected is not None:
                batch.rejected_candidates = rejected
            self.session.flush()
        return batch

    def delete(self, batch_id: UUID) -> bool:
        """Delete a batch and all related candidate reviews and proposed changes."""
        batch = self.get_by_id(batch_id)
        if batch:
            self.session.delete(batch)
            self.session.flush()
            return True
        return False

    def get_next_batch_number(self) -> str:
        """Generate next batch number (e.g., BATCH-0001).
        
        Uses MAX batch number to handle deleted batches properly.
        For example: if BATCH-0001 is deleted and BATCH-0002 exists, 
        next batch will be BATCH-0003 (not BATCH-0002 again).
        """
        # Find max batch number: extract digits from "BATCH-0002" and get max
        result = self.session.execute(
            select(func.max(
                cast(
                    func.substring(ReviewBatch.batch_number, 7),  # Extract "0002" from "BATCH-0002"
                    Integer
                )
            ))
        )
        max_batch_num = result.scalar() or 0
        return f"BATCH-{max_batch_num + 1:04d}"
