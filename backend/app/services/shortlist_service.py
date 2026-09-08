from __future__ import annotations

from uuid import UUID

from app.repositories.shortlist_repository import ShortlistRepository
from app.schemas.shortlists import (
    ShortlistCandidateItemResponse,
    ShortlistListItemResponse,
    ShortlistResponse,
)


class ShortlistService:
    def __init__(self, repository: ShortlistRepository) -> None:
        self.repository = repository

    def create_or_update(
        self,
        *,
        recruiter_id: UUID,
        jd_id: UUID,
        candidate_ids: list[UUID],
    ) -> ShortlistResponse:
        """Create or update a shortlist with the given candidate ids."""
        shortlist = self.repository.create_or_update(
            recruiter_id=recruiter_id,
            jd_id=jd_id,
            candidate_ids=candidate_ids,
        )

        candidate_ids_result = self.repository.get_candidates(shortlist.id)

        return ShortlistResponse(
            id=shortlist.id,
            recruiter_id=shortlist.recruiter_id,
            jd_id=shortlist.jd_id,
            candidate_ids=candidate_ids_result,
        )

    def list_for_recruiter(
        self,
        *,
        recruiter_id: UUID,
        jd_id: UUID | None = None,
    ) -> list[ShortlistListItemResponse]:
        """List shortlists for a recruiter grouped by JD with full candidate detail."""
        rows = self.repository.list_with_candidates_for_recruiter(
            recruiter_id=recruiter_id,
            jd_id=jd_id,
        )

        grouped: dict[UUID, ShortlistListItemResponse] = {}
        for shortlist, jd, candidate in rows:
            item = grouped.get(shortlist.id)
            if item is None:
                item = ShortlistListItemResponse(
                    id=shortlist.id,
                    recruiter_id=shortlist.recruiter_id,
                    jd_id=shortlist.jd_id,
                    jd_code=jd.jd_code,
                    jd_title=jd.title,
                    created_at=shortlist.created_at,
                    candidate_count=0,
                    candidates=[],
                )
                grouped[shortlist.id] = item

            item.candidates.append(
                ShortlistCandidateItemResponse(
                    id=candidate.id,
                    zoho_record_id=candidate.zoho_record_id,
                    zoho_candidate_id=candidate.zoho_candidate_id,
                    full_name=candidate.full_name,
                    email=candidate.email,
                    phone=candidate.phone,
                    total_experience_years=candidate.total_experience_years,
                    relevant_experience_years=candidate.relevant_experience_years,
                    current_company=candidate.current_company,
                    current_location=candidate.current_location,
                    preferred_location=candidate.preferred_location,
                    notice_period_days=candidate.notice_period_days,
                    skills=candidate.skills,
                    degree=candidate.degree,
                    normalized_degree=candidate.normalized_degree,
                    current_ctc=candidate.current_ctc,
                    expected_ctc=candidate.expected_ctc,
                    status=candidate.status,
                    source=candidate.source,
                    created_at=candidate.created_at,
                    updated_at=candidate.updated_at,
                )
            )
            item.candidate_count += 1

        return list(grouped.values())

    def remove_candidate(
        self,
        *,
        recruiter_id: UUID,
        shortlist_id: UUID,
        candidate_id: UUID,
    ) -> bool:
        """Remove a candidate from a shortlist owned by recruiter."""
        shortlist = self.repository.get_by_id(shortlist_id)
        if shortlist is None:
            raise ValueError("SHORTLIST_NOT_FOUND")

        if shortlist.recruiter_id != recruiter_id:
            raise PermissionError("SHORTLIST_FORBIDDEN")

        removed = self.repository.remove_candidate(shortlist_id=shortlist_id, candidate_id=candidate_id)
        if not removed:
            raise ValueError("SHORTLIST_CANDIDATE_NOT_FOUND")
        return True
