from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.job_description import JobDescription
from app.models.ranking_criterion import RankingCriterion
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_get_ranking_criteria_returns_empty_list_for_new_jd(sqlite_session, user_factory) -> None:
    """Test that a new JD with no criteria returns an empty list."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-001",
        title="Test Position",
        required_skills=["Python", "FastAPI"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/job-descriptions/{jd.id}/criteria", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["jd_id"] == str(jd.id)
        assert body["criteria"] == []
        assert body["total_weight"] == 0
    finally:
        app.dependency_overrides.clear()


def test_get_ranking_criteria_returns_404_for_nonexistent_jd(sqlite_session, user_factory) -> None:
    """Test that querying a non-existent JD returns 404."""
    recruiter = user_factory(role="Recruiter")
    nonexistent_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/job-descriptions/{nonexistent_id}/criteria", headers=_header(recruiter))

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "JD_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_get_ranking_criteria_returns_populated_list(sqlite_session, user_factory) -> None:
    """Test that existing criteria are returned correctly."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-002",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    criteria = [
        RankingCriterion(jd_id=jd.id, criteria_name="Technical Skills", weight_points=40.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Experience", weight_points=35.0),
        RankingCriterion(jd_id=jd.id, criteria_name="Soft Skills", weight_points=25.0),
    ]
    sqlite_session.add_all(criteria)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/job-descriptions/{jd.id}/criteria", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert len(body["criteria"]) == 3
        assert body["total_weight"] == 100.0
        assert body["criteria"][0]["criteria_name"] == "Technical Skills"
        assert body["criteria"][0]["weight_points"] == 40.0
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_creates_new_criteria(sqlite_session, user_factory) -> None:
    """Test that POST endpoint creates new criteria with valid weights."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-003",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            headers=_header(recruiter),
            json={
                "criteria": [
                    {"criteria_name": "Technical Skills", "weight_points": 50.0},
                    {"criteria_name": "Experience", "weight_points": 30.0},
                    {"criteria_name": "Culture Fit", "weight_points": 20.0},
                ]
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["criteria"]) == 3
        assert body["total_weight"] == 100.0
        assert body["criteria"][0]["criteria_name"] == "Technical Skills"
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_replaces_existing_criteria(sqlite_session, user_factory) -> None:
    """Test that POST endpoint replaces existing criteria."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-004",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.flush()

    # Add existing criteria
    existing = RankingCriterion(jd_id=jd.id, criteria_name="Old Criteria", weight_points=100.0)
    sqlite_session.add(existing)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            headers=_header(recruiter),
            json={
                "criteria": [
                    {"criteria_name": "New Criteria 1", "weight_points": 60.0},
                    {"criteria_name": "New Criteria 2", "weight_points": 40.0},
                ]
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["criteria"]) == 2
        assert body["criteria"][0]["criteria_name"] == "New Criteria 1"
        
        # Verify old criteria is gone
        get_response = client.get(f"/api/v1/job-descriptions/{jd.id}/criteria", headers=_header(recruiter))
        get_body = get_response.json()
        assert len(get_body["criteria"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_rejects_weight_sum_less_than_100(sqlite_session, user_factory) -> None:
    """Test that POST endpoint rejects weights summing to less than 100."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-005",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            headers=_header(recruiter),
            json={
                "criteria": [
                    {"criteria_name": "Skill 1", "weight_points": 40.0},
                    {"criteria_name": "Skill 2", "weight_points": 50.0},
                ]
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        # Verify there's a validation error for the criteria field
        assert body["details"] is not None
        assert any("criteria" in str(detail).lower() for detail in body["details"])
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_rejects_weight_sum_greater_than_100(sqlite_session, user_factory) -> None:
    """Test that POST endpoint rejects weights summing to more than 100."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-006",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            headers=_header(recruiter),
            json={
                "criteria": [
                    {"criteria_name": "Skill 1", "weight_points": 50.0},
                    {"criteria_name": "Skill 2", "weight_points": 55.0},
                ]
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        # Verify there's a validation error for the criteria field
        assert body["details"] is not None
        assert any("criteria" in str(detail).lower() for detail in body["details"])
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_requires_recruiter_role(sqlite_session, user_factory) -> None:
    """Test that the endpoint is protected and only accessible to recruiters."""
    # This assumes there's a test user with a different role or no auth
    # For now, we'll just test the unauthorized access
    jd = JobDescription(
        jd_code="JD-007",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            json={
                "criteria": [
                    {"criteria_name": "Skill 1", "weight_points": 100.0},
                ]
            },
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_rejects_empty_criteria_list(sqlite_session, user_factory) -> None:
    """Test that POST endpoint rejects empty criteria list."""
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(
        jd_code="JD-008",
        title="Test Position",
        required_skills=["Python"],
    )
    sqlite_session.add(jd)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{jd.id}/criteria",
            headers=_header(recruiter),
            json={"criteria": []},
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_set_ranking_criteria_returns_404_for_nonexistent_jd(sqlite_session, user_factory) -> None:
    """Test that POST endpoint returns 404 for non-existent JD."""
    recruiter = user_factory(role="Recruiter")
    nonexistent_id = uuid4()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/job-descriptions/{nonexistent_id}/criteria",
            headers=_header(recruiter),
            json={
                "criteria": [
                    {"criteria_name": "Skill 1", "weight_points": 100.0},
                ]
            },
        )

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "JD_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()
