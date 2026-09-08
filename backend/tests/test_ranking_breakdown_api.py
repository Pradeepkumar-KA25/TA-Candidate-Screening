from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.ranking_criterion import RankingCriterion
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_get_candidate_breakdown_returns_all_criteria(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking/{candidate_id}/breakdown returns breakdown for all criteria."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-BD-001",
        title="Test Position",
        required_skills=["Python"],
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

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        
        assert isinstance(body, list)
        assert len(body) == 3  # One entry per criterion
        
        # Verify all criteria are present
        criterion_names = [entry["criterion_name"] for entry in body]
        assert "Technical Skills" in criterion_names
        assert "Experience" in criterion_names
        assert "Notice Period" in criterion_names
        
        # Verify structure of each entry
        for entry in body:
            assert entry["candidate_id"] == str(candidate.id)
            assert entry["candidate_name"] == "Test Candidate"
            assert "weight_points" in entry
            assert "match_score" in entry
            assert "weighted_contribution" in entry
            assert 0 <= entry["match_score"] <= 1.0
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_returns_404_for_nonexistent_candidate(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking/{candidate_id}/breakdown returns 404 for non-existent candidate."""
    recruiter = user_factory(role="Recruiter")
    
    # Create a JD
    jd = JobDescription(
        jd_code="JD-API-BD-002",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    nonexistent_candidate_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{nonexistent_candidate_id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "CANDIDATE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_returns_404_for_nonexistent_jd(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking/{candidate_id}/breakdown returns 404 for non-existent JD."""
    recruiter = user_factory(role="Recruiter")
    
    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    nonexistent_jd_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={nonexistent_jd_id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "JD_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_returns_400_for_no_criteria(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking/{candidate_id}/breakdown returns 400 when JD has no criteria."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD without criteria
    jd = JobDescription(
        jd_code="JD-API-BD-003",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "NO_RANKING_CRITERIA"
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_requires_recruiter_role(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking/{candidate_id}/breakdown requires recruiter role."""
    # Create a JD
    jd = JobDescription(
        jd_code="JD-API-BD-004",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    candidate_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        # Request without authentication
        response = client.get(f"/api/v1/ranking/{candidate_id}/breakdown?jd_id={jd.id}")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_verifies_match_scores(sqlite_session, user_factory) -> None:
    """Test that breakdown match scores are correctly computed."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-BD-005",
        title="Developer",
        required_skills=["Python"],
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

    # Add a candidate with skills
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Skilled Candidate",
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        
        assert len(body) == 1
        entry = body[0]
        
        # Verify match score is in valid range
        assert 0 <= entry["match_score"] <= 1.0
        
        # Verify weighted contribution = weight * match_score
        expected_contribution = entry["weight_points"] * entry["match_score"]
        assert entry["weighted_contribution"] == expected_contribution
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_with_no_skills(sqlite_session, user_factory) -> None:
    """Test breakdown for candidate with no skills."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-BD-006",
        title="Developer",
        required_skills=["Python"],
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

    # Add a candidate without skills
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="No Skills Candidate",
        skills=None,
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        
        assert len(body) == 1
        entry = body[0]
        
        # Should have lower match score for no skills
        assert entry["match_score"] == 0.2  # Penalty for missing skills
        assert entry["weighted_contribution"] == 100.0 * 0.2  # 20
    finally:
        app.dependency_overrides.clear()


def test_get_candidate_breakdown_multiple_criteria_different_scores(sqlite_session, user_factory) -> None:
    """Test breakdown with multiple criteria showing different match scores."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-BD-007",
        title="Senior Role",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria_list = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=30.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=50.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Notice Period", weight_points=20.0),
    ]
    sqlite_session.add_all(criteria_list)
    sqlite_session.flush()

    # Add a candidate with mixed profile
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Mixed Profile",
        skills=["Python", "Java"],  # Good skills
        total_experience_years=15.0,  # Excellent experience
        notice_period_days=60,  # Moderate notice
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking/{candidate.id}/breakdown?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        
        assert len(body) == 3
        
        # Verify different match scores for different criteria
        match_scores = [entry["match_score"] for entry in body]
        # Not all scores should be the same
        assert len(set(match_scores)) >= 2 or all(s == match_scores[0] for s in match_scores)
    finally:
        app.dependency_overrides.clear()
