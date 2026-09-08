from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.shortlist import Shortlist
from app.models.shortlist_candidate import ShortlistCandidate


class ShortlistRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_or_update(
        self,
        *,
        recruiter_id: UUID,
        jd_id: UUID,
        candidate_ids: list[UUID],
    ) -> Shortlist:
        """Create a new shortlist or update existing one for recruiter/JD pair with candidate ids."""
        # Find existing shortlist for this recruiter/jd pair
        statement = select(Shortlist).where(
            (Shortlist.recruiter_id == recruiter_id) & (Shortlist.jd_id == jd_id)
        )
        shortlist = self.session.scalar(statement)

        # If shortlist doesn't exist, create it
        if not shortlist:
            shortlist = Shortlist(recruiter_id=recruiter_id, jd_id=jd_id)
            self.session.add(shortlist)
            self.session.flush()

        # Delete existing candidates
        delete_statement = delete(ShortlistCandidate).where(
            ShortlistCandidate.shortlist_id == shortlist.id
        )
        self.session.execute(delete_statement)

        # Add new candidates
        for candidate_id in candidate_ids:
            shortlist_candidate = ShortlistCandidate(
                shortlist_id=shortlist.id,
                candidate_id=candidate_id,
            )
            self.session.add(shortlist_candidate)

        self.session.commit()
        self.session.refresh(shortlist)
        return shortlist

    def get_by_recruiter_and_jd(self, recruiter_id: UUID, jd_id: UUID) -> Shortlist | None:
        """Get shortlist for a specific recruiter and JD."""
        statement = select(Shortlist).where(
            (Shortlist.recruiter_id == recruiter_id) & (Shortlist.jd_id == jd_id)
        )
        return self.session.scalar(statement)

    def get_by_id(self, shortlist_id: UUID) -> Shortlist | None:
        statement = select(Shortlist).where(Shortlist.id == shortlist_id)
        return self.session.scalar(statement)

    def get_candidates(self, shortlist_id: UUID) -> list[UUID]:
        """Get all candidate IDs in a shortlist."""
        statement = select(ShortlistCandidate.candidate_id).where(
            ShortlistCandidate.shortlist_id == shortlist_id
        )
        return list(self.session.scalars(statement).all())

    def list_with_candidates_for_recruiter(
        self,
        *,
        recruiter_id: UUID,
        jd_id: UUID | None = None,
    ) -> list[tuple[Shortlist, JobDescription, Candidate]]:
        """Return shortlist rows joined with JD and candidate details for a recruiter."""
        statement = (
            select(Shortlist, JobDescription, Candidate)
            .join(JobDescription, JobDescription.id == Shortlist.jd_id)
            .join(ShortlistCandidate, ShortlistCandidate.shortlist_id == Shortlist.id)
            .join(Candidate, Candidate.id == ShortlistCandidate.candidate_id)
            .where(Shortlist.recruiter_id == recruiter_id)
            .order_by(Shortlist.created_at.desc(), ShortlistCandidate.added_at.asc(), Candidate.full_name.asc())
        )
        if jd_id is not None:
            statement = statement.where(Shortlist.jd_id == jd_id)

        return list(self.session.execute(statement).all())

    def remove_candidate(self, *, shortlist_id: UUID, candidate_id: UUID) -> bool:
        """Remove a candidate from a shortlist. Returns True if removed, False if not present."""
        delete_statement = delete(ShortlistCandidate).where(
            (ShortlistCandidate.shortlist_id == shortlist_id)
            & (ShortlistCandidate.candidate_id == candidate_id)
        )
        result = self.session.execute(delete_statement)
        if result.rowcount and result.rowcount > 0:
            self.session.commit()
            return True
        self.session.rollback()
        return False
