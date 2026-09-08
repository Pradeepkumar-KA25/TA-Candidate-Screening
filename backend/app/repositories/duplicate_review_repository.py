from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, aliased

from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview


class DuplicateReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_pair(self, *, candidate_id: UUID, matched_candidate_id: UUID) -> DuplicateReview | None:
        statement = select(DuplicateReview).where(
            and_(
                DuplicateReview.candidate_id == candidate_id,
                DuplicateReview.matched_candidate_id == matched_candidate_id,
            )
        )
        return self.session.scalar(statement)

    def get_by_id(self, duplicate_review_id: UUID) -> DuplicateReview | None:
        statement = select(DuplicateReview).where(DuplicateReview.id == duplicate_review_id)
        return self.session.scalar(statement)

    def create_or_update_pending(
        self,
        *,
        candidate_id: UUID,
        matched_candidate_id: UUID,
        match_basis: str,
        confidence: float,
        jd_id: UUID | None = None,
    ) -> tuple[DuplicateReview, bool]:
        existing = self.get_by_pair(candidate_id=candidate_id, matched_candidate_id=matched_candidate_id)
        if existing is None:
            review = DuplicateReview(
                candidate_id=candidate_id,
                matched_candidate_id=matched_candidate_id,
                match_basis=match_basis,
                confidence=confidence,
                jd_id=jd_id,
                status="pending",
            )
            self.session.add(review)
            self.session.flush()
            return review, True

        if existing.status != "reviewed":
            existing.match_basis = match_basis
            existing.confidence = confidence
            existing.jd_id = jd_id
            self.session.add(existing)
            self.session.flush()

        return existing, False

    def list_with_candidates(self) -> list[tuple[DuplicateReview, Candidate, Candidate]]:
        candidate_alias = aliased(Candidate)
        matched_alias = aliased(Candidate)

        statement = (
            select(DuplicateReview, candidate_alias, matched_alias)
            .join(candidate_alias, candidate_alias.id == DuplicateReview.candidate_id)
            .join(matched_alias, matched_alias.id == DuplicateReview.matched_candidate_id)
            .order_by(DuplicateReview.jd_id.asc().nulls_last(), DuplicateReview.created_at.desc(), DuplicateReview.id.desc())
        )
        rows = self.session.execute(statement).all()
        return [(item[0], item[1], item[2]) for item in rows]

    def get_with_candidates(self, duplicate_review_id: UUID) -> tuple[DuplicateReview, Candidate, Candidate] | None:
        candidate_alias = aliased(Candidate)
        matched_alias = aliased(Candidate)

        statement = (
            select(DuplicateReview, candidate_alias, matched_alias)
            .join(candidate_alias, candidate_alias.id == DuplicateReview.candidate_id)
            .join(matched_alias, matched_alias.id == DuplicateReview.matched_candidate_id)
            .where(DuplicateReview.id == duplicate_review_id)
        )
        row = self.session.execute(statement).first()
        if row is None:
            return None
        return row[0], row[1], row[2]

    def mark_reviewed(self, *, duplicate_review_id: UUID, reviewed_by: UUID) -> DuplicateReview:
        review = self.get_by_id(duplicate_review_id)
        if review is None:
            raise ValueError("Duplicate review not found")

        review.status = "reviewed"
        review.reviewed_by = reviewed_by
        review.reviewed_at = datetime.now(UTC)
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

