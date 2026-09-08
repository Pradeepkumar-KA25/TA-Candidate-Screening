from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.schemas.duplicates import (
    DuplicateCandidateSnapshotResponse,
    DuplicateGroupResponse,
    DuplicateGroupedResponse,
    DuplicatePairResponse,
    DuplicateSummaryResponse,
)


class DuplicateError(Exception):
    status_code = 400
    code = "DUPLICATE_ERROR"
    detail = "Duplicate request could not be processed"


class DuplicateNotFoundError(DuplicateError):
    status_code = 404
    code = "DUPLICATE_NOT_FOUND"
    detail = "Duplicate review was not found"


class DuplicateAlreadyReviewedError(DuplicateError):
    status_code = 409
    code = "DUPLICATE_ALREADY_REVIEWED"
    detail = "Duplicate review has already been marked as reviewed"


@dataclass(slots=True)
class DuplicateService:
    duplicate_review_repository: DuplicateReviewRepository
    job_description_repository: JobDescriptionRepository
    activity_log_repository: ActivityLogRepository

    def list_grouped_duplicates(self) -> DuplicateGroupedResponse:
        raw_records = self.duplicate_review_repository.list_with_candidates()
        jd_items = self.job_description_repository.list_for_dropdown()

        groups: dict[UUID | None, DuplicateGroupResponse] = {}
        for jd in jd_items:
            groups[jd.id] = DuplicateGroupResponse(
                jd_id=jd.id,
                jd_code=jd.jd_code,
                jd_title=jd.title,
                duplicate_count=0,
                items=[],
            )

        unassigned_group = DuplicateGroupResponse(
            jd_id=None,
            jd_code=None,
            jd_title="Unassigned",
            duplicate_count=0,
            items=[],
        )

        for review, candidate, matched_candidate in raw_records:
            pair = DuplicatePairResponse(
                id=review.id,
                match_basis=review.match_basis,
                confidence=review.confidence,
                status=review.status,
                created_at=review.created_at,
                reviewed_by=review.reviewed_by,
                reviewed_at=review.reviewed_at,
                candidate=DuplicateCandidateSnapshotResponse(
                    id=candidate.id,
                    zoho_candidate_id=candidate.zoho_candidate_id,
                    full_name=candidate.full_name,
                    email=candidate.email,
                    phone=candidate.phone,
                    current_company=candidate.current_company,
                    current_location=candidate.current_location,
                    total_experience_years=candidate.total_experience_years,
                ),
                matched_candidate=DuplicateCandidateSnapshotResponse(
                    id=matched_candidate.id,
                    zoho_candidate_id=matched_candidate.zoho_candidate_id,
                    full_name=matched_candidate.full_name,
                    email=matched_candidate.email,
                    phone=matched_candidate.phone,
                    current_company=matched_candidate.current_company,
                    current_location=matched_candidate.current_location,
                    total_experience_years=matched_candidate.total_experience_years,
                ),
            )

            target = groups.get(review.jd_id) if review.jd_id else None
            if target is None:
                target = unassigned_group
            target.items.append(pair)
            target.duplicate_count += 1

        ordered_groups = [groups[jd.id] for jd in jd_items]
        if unassigned_group.duplicate_count > 0:
            ordered_groups.append(unassigned_group)

        possible_duplicates = sum(group.duplicate_count for group in ordered_groups)
        no_duplicate_signal = sum(1 for group in ordered_groups if group.jd_id is not None and group.duplicate_count == 0)

        summary = DuplicateSummaryResponse(
            job_descriptions_reviewed=len(jd_items),
            possible_duplicates=possible_duplicates,
            no_duplicate_signal=no_duplicate_signal,
            unassigned_duplicates=unassigned_group.duplicate_count,
        )

        return DuplicateGroupedResponse(summary=summary, groups=ordered_groups)

    def review_duplicate(self, *, duplicate_review_id: UUID, recruiter_id: UUID) -> DuplicatePairResponse:
        record = self.duplicate_review_repository.get_with_candidates(duplicate_review_id)
        if record is None:
            raise DuplicateNotFoundError()

        review, candidate, matched_candidate = record
        if review.status == "reviewed":
            raise DuplicateAlreadyReviewedError()

        review = self.duplicate_review_repository.mark_reviewed(
            duplicate_review_id=duplicate_review_id,
            reviewed_by=recruiter_id,
        )
        self.activity_log_repository.create(
            actor_id=recruiter_id,
            action_type="duplicate_reviewed",
            description=(
                "Duplicate reviewed "
                f"(duplicate_id={review.id}, candidate_id={candidate.id}, matched_candidate_id={matched_candidate.id})"
            ),
        )

        return DuplicatePairResponse(
            id=review.id,
            match_basis=review.match_basis,
            confidence=review.confidence,
            status=review.status,
            created_at=review.created_at,
            reviewed_by=review.reviewed_by,
            reviewed_at=review.reviewed_at,
            candidate=DuplicateCandidateSnapshotResponse(
                id=candidate.id,
                zoho_candidate_id=candidate.zoho_candidate_id,
                full_name=candidate.full_name,
                email=candidate.email,
                phone=candidate.phone,
                current_company=candidate.current_company,
                current_location=candidate.current_location,
                total_experience_years=candidate.total_experience_years,
            ),
            matched_candidate=DuplicateCandidateSnapshotResponse(
                id=matched_candidate.id,
                zoho_candidate_id=matched_candidate.zoho_candidate_id,
                full_name=matched_candidate.full_name,
                email=matched_candidate.email,
                phone=matched_candidate.phone,
                current_company=matched_candidate.current_company,
                current_location=matched_candidate.current_location,
                total_experience_years=matched_candidate.total_experience_years,
            ),
        )
