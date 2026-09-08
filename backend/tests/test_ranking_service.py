from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.ranking_criterion import RankingCriterion
from app.services.candidate_filter_service import CandidateFilterCriteria
from app.services.ranking_service import (
    RankingNoCriteriaError,
    RankingJDNotFoundError,
    RankingService,
)


def test_rank_candidates_with_single_criterion(sqlite_session) -> None:
    """Test ranking with a single criterion (skills)."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-TEST-001",
        title="Python Developer",
        required_skills=["Python", "FastAPI"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria: 100% on skills
    criteria = RankingCriterion(
        jd_id=jd.id,
        criteria_name="Technical Skills",
        weight_points=100.0,
    )
    sqlite_session.add(criteria)
    sqlite_session.flush()

    # Add candidates
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="Expert Developer",
        skills=["Python", "FastAPI", "Django", "PostgreSQL", "Docker"],
        total_experience_years=10.0,
        notice_period_days=30,
    )
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="Junior Developer",
        skills=["Python"],
        total_experience_years=2.0,
        notice_period_days=60,
    )
    candidate3 = Candidate(
        zoho_record_id="C3",
        full_name="Career Changer",
        skills=None,
        total_experience_years=5.0,
        notice_period_days=30,
    )
    sqlite_session.add_all([candidate1, candidate2, candidate3])
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

    # Test ranking
    result = service.rank_candidates(jd.id)

    assert len(result.ranked_candidates) == 3
    assert result.ranked_candidates[0].full_name == "Expert Developer"
    assert result.ranked_candidates[0].rank == 1
    assert result.ranked_candidates[1].full_name == "Junior Developer"
    assert result.ranked_candidates[1].rank == 2
    assert result.ranked_candidates[2].full_name == "Career Changer"
    assert result.ranked_candidates[2].rank == 3


def test_rank_candidates_with_multiple_criteria(sqlite_session) -> None:
    """Test ranking with multiple weighted criteria."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-TEST-002",
        title="Senior Engineer",
        required_skills=["Python", "AWS"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria with weights
    criteria_list = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=40.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=35.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Notice Period", weight_points=25.0),
    ]
    sqlite_session.add_all(criteria_list)
    sqlite_session.flush()

    # Add candidates with different profiles
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="Strong Candidate",
        skills=["Python", "AWS", "Docker"],
        total_experience_years=10.0,
        notice_period_days=30,
    )
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="Experienced but Long Notice",
        skills=["Python", "AWS"],
        total_experience_years=12.0,
        notice_period_days=90,
    )
    candidate3 = Candidate(
        zoho_record_id="C3",
        full_name="Few Skills but Quick Start",
        skills=["Python"],
        total_experience_years=3.0,
        notice_period_days=15,
    )
    sqlite_session.add_all([candidate1, candidate2, candidate3])
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

    # Test ranking
    result = service.rank_candidates(jd.id)

    assert len(result.ranked_candidates) == 3
    # Verify scores are computed and sorted
    assert result.ranked_candidates[0].score >= result.ranked_candidates[1].score
    assert result.ranked_candidates[1].score >= result.ranked_candidates[2].score
    # Ranks should be sequential
    assert result.ranked_candidates[0].rank == 1
    assert result.ranked_candidates[1].rank == 2
    assert result.ranked_candidates[2].rank == 3


def test_rank_candidates_with_filter_criteria(sqlite_session) -> None:
    """Test ranking applies filter criteria correctly."""
    # Setup JD
    jd = JobDescription(
        jd_code="JD-TEST-003",
        title="Backend Developer",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria = RankingCriterion(
        jd_id=jd.id,
        criteria_name="Experience",
        weight_points=100.0,
    )
    sqlite_session.add(criteria)
    sqlite_session.flush()

    # Add candidates with different statuses
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="Active Candidate",
        skills=["Python"],
        total_experience_years=8.0,
        status="active",
    )
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="Rejected Candidate",
        skills=["Python"],
        total_experience_years=10.0,
        status="rejected",
    )
    sqlite_session.add_all([candidate1, candidate2])
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

    # Test ranking with status filter
    filter_criteria = CandidateFilterCriteria(status="active")
    result = service.rank_candidates(jd.id, filter_criteria)

    assert len(result.ranked_candidates) == 1
    assert result.ranked_candidates[0].full_name == "Active Candidate"


def test_rank_candidates_raises_404_for_nonexistent_jd(sqlite_session) -> None:
    """Test ranking raises error for non-existent JD."""
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    nonexistent_id = uuid4()
    with pytest.raises(RankingJDNotFoundError):
        service.rank_candidates(nonexistent_id)


def test_rank_candidates_raises_error_for_no_criteria(sqlite_session) -> None:
    """Test ranking raises error when JD has no criteria."""
    # Setup JD without criteria
    jd = JobDescription(
        jd_code="JD-TEST-004",
        title="Test Position",
        required_skills=["Anything"],
    )
    sqlite_session.add(jd)
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
        service.rank_candidates(jd.id)


def test_score_skills_criterion(sqlite_session) -> None:
    """Test skills scoring logic."""
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test candidate with no skills
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="No Skills",
        skills=None,
    )
    score1 = service._score_skills(candidate1)
    assert score1 == 0.2  # Penalized

    # Test candidate with few skills
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="Few Skills",
        skills=["Python"],
    )
    score2 = service._score_skills(candidate2)
    assert 0 < score2 < 1

    # Test candidate with many skills
    candidate3 = Candidate(
        zoho_record_id="C3",
        full_name="Many Skills",
        skills=["Python", "Java", "C++", "Go", "Rust"],
    )
    score3 = service._score_skills(candidate3)
    assert score3 == 1.0  # Full score


def test_score_experience_criterion(sqlite_session) -> None:
    """Test experience scoring logic."""
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test candidate with no experience
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="No Experience",
        total_experience_years=None,
    )
    score1 = service._score_experience(candidate1)
    assert score1 == 0.2  # Penalized

    # Test candidate with moderate experience
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="5 Years",
        total_experience_years=5.0,
    )
    score2 = service._score_experience(candidate2)
    assert 0.4 < score2 < 0.6

    # Test candidate with 10+ years
    candidate3 = Candidate(
        zoho_record_id="C3",
        full_name="10 Years",
        total_experience_years=10.0,
    )
    score3 = service._score_experience(candidate3)
    assert score3 == 1.0


def test_score_notice_period_criterion(sqlite_session) -> None:
    """Test notice period scoring logic."""
    from app.repositories.job_description_repository import JobDescriptionRepository
    from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
    from app.repositories.candidate_repository import CandidateRepository

    service = RankingService(
        session=sqlite_session,
        job_description_repository=JobDescriptionRepository(sqlite_session),
        ranking_criteria_repository=RankingCriteriaRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
    )

    # Test candidate with no notice period data
    candidate1 = Candidate(
        zoho_record_id="C1",
        full_name="Unknown Notice",
        notice_period_days=None,
    )
    score1 = service._score_notice_period(candidate1)
    assert score1 == 0.5  # Neutral

    # Test candidate with short notice (30 days)
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="30 Days Notice",
        notice_period_days=30,
    )
    score2 = service._score_notice_period(candidate2)
    assert score2 == 1.0  # Perfect

    # Test candidate with medium notice (60 days)
    candidate3 = Candidate(
        zoho_record_id="C3",
        full_name="60 Days Notice",
        notice_period_days=60,
    )
    score3 = service._score_notice_period(candidate3)
    assert score3 == 0.5

    # Test candidate with long notice (90+ days)
    candidate4 = Candidate(
        zoho_record_id="C4",
        full_name="90 Days Notice",
        notice_period_days=90,
    )
    score4 = service._score_notice_period(candidate4)
    assert score4 == 0.2
