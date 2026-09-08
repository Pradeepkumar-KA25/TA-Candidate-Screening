from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.job_description import JobDescription
from app.models.saved_filter import SavedFilter
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_create_saved_filter_success_and_list_contains_new_record(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    job_description = JobDescription(
        jd_code="JD-2026-014",
        title="Java Backend Developer",
        required_skills=["Java", "Spring Boot"],
    )
    sqlite_session.add(job_description)
    sqlite_session.commit()
    sqlite_session.refresh(job_description)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        payload = {
            "name": "Java Backend Primary",
            "jd_id": str(job_description.id),
            "filter_criteria": {
                "skills": "Java,Spring Boot",
                "experience_min": 4,
                "location": "Bengaluru",
            },
        }

        create_response = client.post("/api/v1/saved-filters", headers=_header(recruiter), json=payload)
        assert create_response.status_code == 201
        create_body = create_response.json()
        assert create_body["name"] == "Java Backend Primary"
        assert create_body["jd_id"] == str(job_description.id)
        assert create_body["filter_criteria"]["skills"] == "Java,Spring Boot"
        assert create_body["resolved_query_params"]["jd_id"] == str(job_description.id)
        assert create_body["resolved_query_params"]["experience_min"] == "4"

        list_response = client.get("/api/v1/saved-filters", headers=_header(recruiter))
        assert list_response.status_code == 200
        list_body = list_response.json()
        assert len(list_body) == 1
        assert list_body[0]["name"] == "Java Backend Primary"
        assert list_body[0]["jd_id"] == str(job_description.id)
    finally:
        app.dependency_overrides.clear()


def test_create_saved_filter_rejects_blank_name(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/saved-filters",
            headers=_header(recruiter),
            json={
                "name": "  ",
                "jd_id": None,
                "filter_criteria": {"skills": "Python"},
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
    finally:
        app.dependency_overrides.clear()


def test_create_saved_filter_persists_jd_association(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    job_description = JobDescription(
        jd_code="JD-2026-101",
        title="Python API Developer",
        required_skills=["Python", "FastAPI"],
    )
    sqlite_session.add(job_description)
    sqlite_session.commit()
    sqlite_session.refresh(job_description)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/saved-filters",
            headers=_header(recruiter),
            json={
                "name": "Python JD Focus",
                "jd_id": str(job_description.id),
                "filter_criteria": {"skills": "Python,FastAPI", "jd_id": str(job_description.id)},
            },
        )

        assert response.status_code == 201

        saved = sqlite_session.query(SavedFilter).filter(SavedFilter.name == "Python JD Focus").first()
        assert saved is not None
        assert str(saved.jd_id) == str(job_description.id)
    finally:
        app.dependency_overrides.clear()


def test_saved_filters_list_is_recruiter_scoped_and_sorted_most_recent_first(sqlite_session, user_factory) -> None:
    recruiter_a = user_factory(email="recruiter.a@example.com", role="Recruiter")
    recruiter_b = user_factory(email="recruiter.b@example.com", role="Recruiter")

    now = datetime.now(UTC)
    older = SavedFilter(
        recruiter_id=recruiter_a.id,
        name="Older Template",
        jd_id=None,
        filter_criteria={"skills": "Java"},
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    newer = SavedFilter(
        recruiter_id=recruiter_a.id,
        name="Newer Template",
        jd_id=None,
        filter_criteria={"skills": "Python", "location": "Hyderabad"},
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(hours=1),
    )
    other_recruiter = SavedFilter(
        recruiter_id=recruiter_b.id,
        name="Other Recruiter Template",
        jd_id=None,
        filter_criteria={"skills": "Go"},
        created_at=now,
        updated_at=now,
    )

    sqlite_session.add_all([older, newer, other_recruiter])
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/saved-filters", headers=_header(recruiter_a))

        assert response.status_code == 200
        body = response.json()
        assert [item["name"] for item in body] == ["Newer Template", "Older Template"]
        assert all(item["recruiter_id"] == str(recruiter_a.id) for item in body)
        assert body[0]["resolved_query_params"]["skills"] == "Python"
        assert body[0]["resolved_query_params"]["location"] == "Hyderabad"
    finally:
        app.dependency_overrides.clear()
