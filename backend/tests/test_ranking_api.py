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


def test_get_ranked_candidates_returns_sorted_list(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking returns candidates sorted by score descending."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-001",
        title="Software Engineer",
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

    # Add candidates
    candidates = [
        Candidate(
            zoho_record_id=f"C{i}",
            full_name=f"Candidate {i}",
            skills=[f"Skill{i}" for _ in range(i)],
            total_experience_years=float(i),
        )
        for i in range(1, 4)
    ]
    sqlite_session.add_all(candidates)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["jd_id"] == str(jd.id)
        assert body["total_candidates"] == 3
        assert len(body["ranked_candidates"]) == 3
        
        # Verify ranking is sorted descending by score
        scores = [c["score"] for c in body["ranked_candidates"]]
        assert scores == sorted(scores, reverse=True)
        
        # Verify ranks are sequential
        for i, candidate in enumerate(body["ranked_candidates"]):
            assert candidate["rank"] == i + 1
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_returns_404_for_nonexistent_jd(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking returns 404 for non-existent JD."""
    recruiter = user_factory(role="Recruiter")
    nonexistent_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={nonexistent_id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "JD_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_returns_400_for_no_criteria(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking returns 400 when JD has no criteria."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD without criteria
    jd = JobDescription(
        jd_code="JD-API-002",
        title="Test Position",
        required_skills=["Anything"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "NO_RANKING_CRITERIA"
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_applies_status_filter(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking applies status filter."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-003",
        title="Test Position",
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
        status="active",
        total_experience_years=5.0,
    )
    candidate2 = Candidate(
        zoho_record_id="C2",
        full_name="Rejected Candidate",
        skills=["Python"],
        status="rejected",
        total_experience_years=10.0,
    )
    sqlite_session.add_all([candidate1, candidate2])
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}&status_filter=active",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] == 1
        assert body["ranked_candidates"][0]["full_name"] == "Active Candidate"
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_applies_experience_filter(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking applies experience range filter."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-004",
        title="Senior Position",
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

    # Add candidates with different experience levels
    candidates = [
        Candidate(
            zoho_record_id="C1",
            full_name="Junior",
            skills=["Python"],
            total_experience_years=2.0,
        ),
        Candidate(
            zoho_record_id="C2",
            full_name="Mid-level",
            skills=["Python"],
            total_experience_years=5.0,
        ),
        Candidate(
            zoho_record_id="C3",
            full_name="Senior",
            skills=["Python"],
            total_experience_years=10.0,
        ),
    ]
    sqlite_session.add_all(candidates)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        # Filter for experience >= 5 years
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}&experience_min=5",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] == 2  # Mid-level and Senior
        names = [c["full_name"] for c in body["ranked_candidates"]]
        assert "Mid-level" in names
        assert "Senior" in names
        assert "Junior" not in names
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_applies_notice_period_filter(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking applies notice period filter."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-005",
        title="Urgent Hire",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria = RankingCriterion(
        jd_id=jd.id,
        criteria_name="Notice Period",
        weight_points=100.0,
    )
    sqlite_session.add(criteria)
    sqlite_session.flush()

    # Add candidates with different notice periods
    candidates = [
        Candidate(
            zoho_record_id="C1",
            full_name="Quick Start",
            skills=["Python"],
            notice_period_days=15,
            total_experience_years=3.0,
        ),
        Candidate(
            zoho_record_id="C2",
            full_name="Medium Notice",
            skills=["Python"],
            notice_period_days=45,
            total_experience_years=5.0,
        ),
        Candidate(
            zoho_record_id="C3",
            full_name="Long Notice",
            skills=["Python"],
            notice_period_days=90,
            total_experience_years=8.0,
        ),
    ]
    sqlite_session.add_all(candidates)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        # Filter for notice period <= 30 days
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}&notice_period_max=30",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] == 1
        assert body["ranked_candidates"][0]["full_name"] == "Quick Start"
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_requires_recruiter_role(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking requires recruiter role."""
    # Create a JD for the request
    jd = JobDescription(
        jd_code="JD-API-006",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        # Request without authentication
        response = client.get(f"/api/v1/ranking?jd_id={jd.id}")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_returns_match_percentage(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking returns match_percentage for each candidate."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-007",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add ranking criteria
    criteria = RankingCriterion(
        jd_id=jd.id,
        criteria_name="Skills",
        weight_points=100.0,
    )
    sqlite_session.add(criteria)
    sqlite_session.flush()

    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python", "FastAPI"],
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["ranked_candidates"]) == 1
        candidate_data = body["ranked_candidates"][0]
        
        # Verify match_percentage is present and in range 0-100
        assert "match_percentage" in candidate_data
        assert 0 <= candidate_data["match_percentage"] <= 100
        
        # Score and match_percentage should be equal
        assert candidate_data["score"] == candidate_data["match_percentage"]
    finally:
        app.dependency_overrides.clear()


def test_get_ranked_candidates_includes_filter_summary(sqlite_session, user_factory) -> None:
    """Test that GET /api/v1/ranking includes filter summary in response."""
    recruiter = user_factory(role="Recruiter")
    
    # Setup JD
    jd = JobDescription(
        jd_code="JD-API-008",
        title="Test Position",
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

    # Add a candidate
    candidate = Candidate(
        zoho_record_id="C1",
        full_name="Test Candidate",
        skills=["Python"],
        status="active",
        total_experience_years=5.0,
    )
    sqlite_session.add(candidate)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/ranking?jd_id={jd.id}&status_filter=active&experience_min=3",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        body = response.json()
        
        # Verify filter_summary is included
        assert body["filter_summary"] is not None
        assert body["filter_summary"]["status"] == "active"
        assert body["filter_summary"]["experience_min_years"] == 3
    finally:
        app.dependency_overrides.clear()
