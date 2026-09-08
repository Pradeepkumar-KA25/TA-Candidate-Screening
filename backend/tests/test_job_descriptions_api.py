from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.job_description import JobDescription
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_job_descriptions_list_returns_dropdown_items(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    sqlite_session.add_all(
        [
            JobDescription(
                jd_code="JD-2026-014",
                title="Java Backend Developer",
                required_skills=["Java", "Spring Boot", "Microservices"],
            ),
            JobDescription(
                jd_code="JD-2026-101",
                title="Python API Developer",
                required_skills=["Python", "FastAPI"],
            ),
        ]
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/job-descriptions", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["jd_code"] == "JD-2026-014"
        assert body[0]["title"] == "Java Backend Developer"
        assert body[0]["required_skills"] == ["Java", "Spring Boot", "Microservices"]
        assert set(body[0].keys()) == {"id", "jd_code", "title", "required_skills"}
    finally:
        app.dependency_overrides.clear()


def test_job_descriptions_create_persists_and_returns_record(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/job-descriptions",
            headers=_header(recruiter),
            json={
                "jd_code": " JD-2026-250 ",
                "title": " Senior Backend Engineer ",
                "required_skills": [" Python ", " FastAPI", "", "SQL"],
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["jd_code"] == "JD-2026-250"
        assert body["title"] == "Senior Backend Engineer"
        assert body["required_skills"] == ["Python", "FastAPI", "SQL"]
        assert "id" in body
        assert "created_at" in body
    finally:
        app.dependency_overrides.clear()


def test_job_descriptions_create_rejects_duplicate_code(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    sqlite_session.add(
        JobDescription(
            jd_code="JD-2026-014",
            title="Java Backend Developer",
            required_skills=["Java"],
        )
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/job-descriptions",
            headers=_header(recruiter),
            json={
                "jd_code": "jd-2026-014",
                "title": "Another Title",
                "required_skills": ["Java", "Spring Boot"],
            },
        )

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "JOB_DESCRIPTION_ALREADY_EXISTS"
    finally:
        app.dependency_overrides.clear()
