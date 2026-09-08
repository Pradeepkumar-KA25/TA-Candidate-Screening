from __future__ import annotations

from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.services.duplicate_detection_service import DuplicateDetectionService


def _create_service(sqlite_session) -> DuplicateDetectionService:
    return DuplicateDetectionService(
        candidate_repository=CandidateRepository(sqlite_session),
        duplicate_review_repository=DuplicateReviewRepository(sqlite_session),
    )


def _lookup_review_for_pair(sqlite_session) -> DuplicateReview | None:
    candidates = sorted(sqlite_session.query(Candidate).all(), key=lambda item: str(item.id))
    if len(candidates) < 2:
        return None

    return DuplicateReviewRepository(sqlite_session).get_by_pair(
        candidate_id=candidates[0].id,
        matched_candidate_id=candidates[1].id,
    )


def test_duplicate_detection_exact_match_email_and_phone(sqlite_session) -> None:
    sqlite_session.add_all(
        [
            Candidate(
                zoho_record_id="z-1",
                zoho_candidate_id="C-1",
                full_name="Asha Sharma",
                email="asha@example.com",
                phone="+91 90000 00001",
            ),
            Candidate(
                zoho_record_id="z-2",
                zoho_candidate_id="C-2",
                full_name="Asha S.",
                email="asha@example.com",
                phone="9000000001",
            ),
        ]
    )
    sqlite_session.commit()

    result = _create_service(sqlite_session).detect()

    assert result.scanned == 2
    assert result.potential_duplicates == 1
    assert result.created == 1

    review = _lookup_review_for_pair(sqlite_session)
    assert review is not None
    assert review.match_basis == "email_exact+phone_exact"
    assert review.confidence == 0.99


def test_duplicate_detection_near_match_email_or_phone(sqlite_session) -> None:
    sqlite_session.add_all(
        [
            Candidate(
                zoho_record_id="z-10",
                zoho_candidate_id="C-10",
                full_name="Ravi Kumar",
                email="ravi.kumar+profile@example.com",
                phone="9000000001",
            ),
            Candidate(
                zoho_record_id="z-11",
                zoho_candidate_id="C-11",
                full_name="Ravi K.",
                email="ravikumar@example.com",
                phone="9000000002",
            ),
        ]
    )
    sqlite_session.commit()

    result = _create_service(sqlite_session).detect()

    assert result.potential_duplicates == 1
    review = _lookup_review_for_pair(sqlite_session)
    assert review is not None
    assert review.match_basis == "email_near+phone_near"
    assert review.confidence == 0.88


def test_duplicate_detection_no_match_for_unrelated_candidates(sqlite_session) -> None:
    sqlite_session.add_all(
        [
            Candidate(
                zoho_record_id="z-20",
                zoho_candidate_id="C-20",
                full_name="Asha Sharma",
                email="asha@example.com",
                phone="9000000001",
            ),
            Candidate(
                zoho_record_id="z-21",
                zoho_candidate_id="C-21",
                full_name="Meera Das",
                email="meera@example.org",
                phone="8111111111",
            ),
        ]
    )
    sqlite_session.commit()

    result = _create_service(sqlite_session).detect()

    assert result.scanned == 2
    assert result.potential_duplicates == 0
    assert result.created == 0
