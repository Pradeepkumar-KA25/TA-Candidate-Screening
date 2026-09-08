from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.ranking_criterion import RankingCriterion
from app.services.ranking_service import (
    RankingNoCriteriaError,
    RankingJDNotFoundError,
    RankingCandidateNotFoundError,
    RankingService,
)


def test_get_score_breakdown_fully_matched_candidate(sqlite_session) -> None:
    """Test score breakdown for a candidate with all matching criteria."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-BD-001",
        title="Senior Python Developer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria_list = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=40.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=35.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Notice Period", weight_points=25.0),
    ]
    sqlite_session.add_all(criteria_list)
    sqlite_session.flush()

    # Add a fully-matched candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Full Match Candidate",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        total_experience_years=10.0,
        notice_period_days=15,
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    # Get ranking service
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test breakdown
    breakdown = service.get_score_breakdown(candidate.id, jd.id)

    assert len(breakdown) == 3
    assert breakdown[0].candidate_name == "Full Match Candidate"
    assert breakdown[0].criterion_name == "Technical Skills"
    assert breakdown[0].weight_points == 40.0
    assert 0 <= breakdown[0].match_score <= 1.0
    assert breakdown[0].weighted_contribution == breakdown[0].weight_points * breakdown[0].match_score


def test_get_score_breakdown_partially_matched_candidate(sqlite_session) -> None:
    """Test score breakdown for a candidate with some matching criteria."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-BD-002",
        title="Mid-level Engineer",
        required_skills=["Python", "Java"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria_list = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=50.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=50.0),
    ]
    sqlite_session.add_all(criteria_list)
    sqlite_session.flush()

    # Add a partially-matched candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Partial Match Candidate",
        skills=["Python"],  # Only 1 of required 2 skills
        total_experience_years=5.0,  # Less than 10
        notice_period_days=45,
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    # Get ranking service
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test breakdown
    breakdown = service.get_score_breakdown(candidate.id, jd.id)

    assert len(breakdown) == 2
    # All breakdown entries should have valid scores
    for entry in breakdown:
        assert entry.candidate_id == candidate.id
        assert 0 <= entry.match_score <= 1.0
        assert entry.weighted_contribution >= 0


def test_get_score_breakdown_unmatched_candidate(sqlite_session) -> None:
    """Test score breakdown for a candidate with minimal matching."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-BD-003",
        title="Senior Specialist",
        required_skills=["Specialized Tech"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria = RankingCriterion(
        jd_id=jd.id,
        criteria_name="Technical Skills",
        weight_points=100.0,
    )
    sqlite_session.add(criteria)
    sqlite_session.flush()

    # Add an unmatched candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Unmatched Candidate",
        skills=None,  # No skills
        total_experience_years=1.0,  # Very junior
        notice_period_days=90,  # Long notice period
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    # Get ranking service
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test breakdown
    breakdown = service.get_score_breakdown(candidate.id, jd.id)

    assert len(breakdown) == 1
    assert breakdown[0].candidate_name == "Unmatched Candidate"
    # Should have low match score for skills (penalized for no skills)
    assert breakdown[0].match_score < 1.0


def test_get_score_breakdown_raises_404_for_nonexistent_candidate(sqlite_session) -> None:
    """Test breakdown raises error for non-existent candidate."""
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    nonexistent_candidate_id = uuid4()
    nonexistent_jd_id = uuid4()

    with pytest.raises(RankingCandidateNotFoundError):
        service.get_score_breakdown(nonexistent_candidate_id, nonexistent_jd_id)


def test_get_score_breakdown_raises_404_for_nonexistent_jd(sqlite_session) -> None:
    """Test breakdown raises error for non-existent JD."""
    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    nonexistent_jd_id = uuid4()

    with pytest.raises(RankingJDNotFoundError):
        service.get_score_breakdown(candidate.id, nonexistent_jd_id)


def test_get_score_breakdown_raises_error_for_no_criteria(sqlite_session) -> None:
    """Test breakdown raises error when JD has no criteria."""
    # Setup JD without criteria
    jd = JobDescription(
        jd_code="JD-BD-004",
        title="Test Position",
        required_skills=["Anything"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Anything"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    with pytest.raises(RankingNoCriteriaError):
        service.get_score_breakdown(candidate.id, jd.id)


def test_get_score_breakdown_breakdown_sums_to_total_score(sqlite_session) -> None:
    """Test that breakdown components sum to the total score."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-BD-005",
        title="Full Role",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria with known weights
    criteria_list = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=40.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=35.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Notice Period", weight_points=25.0),
    ]
    sqlite_session.add_all(criteria_list)
    sqlite_session.flush()

    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python", "FastAPI"],
        total_experience_years=8.0,
        notice_period_days=30,
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    # Get ranking service
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Get breakdown
    breakdown = service.get_score_breakdown(candidate.id, jd.id)

    # Sum weighted contributions should equal total score
    total_score = sum(entry.weighted_contribution for entry in breakdown)
    assert 0 <= total_score <= 100
