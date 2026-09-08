from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview
from app.models.job_description import JobDescription
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_list_grouped_duplicates_returns_summary_and_groups(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    jd1 = JobDescription(jd_code="JD-2026-014", title="Java Backend Developer", required_skills=["Java"])
    jd2 = JobDescription(jd_code="JD-2026-021", title="Frontend React Developer", required_skills=["React"])
    sqlite_session.add_all([jd1, jd2])
    sqlite_session.commit()
    sqlite_session.refresh(jd1)
    sqlite_session.refresh(jd2)

    candidate_1 = Candidate(
        zoho_record_id="zr-1",
        zoho_candidate_id="z-1",
        full_name="Arjun Kumar",
        email="arjun@example.com",
        phone="+919111111111",
        current_company="TechNova",
        current_location="Bengaluru",
        total_experience_years=6.0,
    )
    candidate_2 = Candidate(
        zoho_record_id="zr-2",
        zoho_candidate_id="z-2",
        full_name="Arjun K.",
        email="arjun.k@example.com",
        phone="+919111111111",
        current_company="TechNova",
        current_location="Bengaluru",
        total_experience_years=6.0,
    )
    sqlite_session.add_all([candidate_1, candidate_2])
    sqlite_session.commit()
    sqlite_session.refresh(candidate_1)
    sqlite_session.refresh(candidate_2)

    duplicate_review = DuplicateReview(
        candidate_id=candidate_1.id,
        matched_candidate_id=candidate_2.id,
        match_basis="phone",
        confidence=0.95,
        jd_id=jd1.id,
        status="pending",
    )
    sqlite_session.add(duplicate_review)
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/duplicates", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()

        assert body["summary"]["job_descriptions_reviewed"] == 2
        assert body["summary"]["possible_duplicates"] == 1
        assert body["summary"]["no_duplicate_signal"] == 1
        assert body["summary"]["unassigned_duplicates"] == 0

        assert len(body["groups"]) == 2
        assert body["groups"][0]["jd_code"] == "JD-2026-014"
        assert body["groups"][0]["duplicate_count"] == 1
        assert body["groups"][0]["items"][0]["candidate"]["full_name"] == "Arjun Kumar"
        assert body["groups"][0]["items"][0]["matched_candidate"]["full_name"] == "Arjun K."

        assert body["groups"][1]["jd_code"] == "JD-2026-021"
        assert body["groups"][1]["duplicate_count"] == 0
        assert body["groups"][1]["items"] == []
    finally:
        app.dependency_overrides.clear()


def test_list_grouped_duplicates_includes_unassigned_group(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(jd_code="JD-2026-111", title="Data Engineer", required_skills=["Python"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate_1 = Candidate(zoho_record_id="zr-11", zoho_candidate_id="z-11", full_name="Nisha Rao")
    candidate_2 = Candidate(zoho_record_id="zr-12", zoho_candidate_id="z-12", full_name="Nisha R")
    sqlite_session.add_all([candidate_1, candidate_2])
    sqlite_session.commit()
    sqlite_session.refresh(candidate_1)
    sqlite_session.refresh(candidate_2)

    sqlite_session.add(
        DuplicateReview(
            candidate_id=candidate_1.id,
            matched_candidate_id=candidate_2.id,
            match_basis="email",
            confidence=0.88,
            jd_id=None,
            status="pending",
        )
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/duplicates", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()

        assert body["summary"]["job_descriptions_reviewed"] == 1
        assert body["summary"]["possible_duplicates"] == 1
        assert body["summary"]["no_duplicate_signal"] == 1
        assert body["summary"]["unassigned_duplicates"] == 1

        assert len(body["groups"]) == 2
        assert body["groups"][0]["jd_code"] == "JD-2026-111"
        assert body["groups"][0]["duplicate_count"] == 0
        assert body["groups"][1]["jd_id"] is None
        assert body["groups"][1]["jd_title"] == "Unassigned"
        assert body["groups"][1]["duplicate_count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_review_duplicate_marks_record_reviewed_and_logs_activity(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    candidate_1 = Candidate(zoho_record_id="zr-21", zoho_candidate_id="z-21", full_name="Asha Sharma")
    candidate_2 = Candidate(zoho_record_id="zr-22", zoho_candidate_id="z-22", full_name="Asha S")
    sqlite_session.add_all([candidate_1, candidate_2])
    sqlite_session.commit()
    sqlite_session.refresh(candidate_1)
    sqlite_session.refresh(candidate_2)

    duplicate_review = DuplicateReview(
        candidate_id=candidate_1.id,
        matched_candidate_id=candidate_2.id,
        match_basis="email_exact",
        confidence=0.95,
        status="pending",
    )
    sqlite_session.add(duplicate_review)
    sqlite_session.commit()
    sqlite_session.refresh(duplicate_review)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.patch(f"/api/v1/duplicates/{duplicate_review.id}/review", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(duplicate_review.id)
        assert body["status"] == "reviewed"
        assert body["reviewed_by"] == str(recruiter.id)
        assert body["reviewed_at"] is not None

        sqlite_session.refresh(duplicate_review)
        assert duplicate_review.status == "reviewed"
        assert duplicate_review.reviewed_by == recruiter.id
        assert duplicate_review.reviewed_at is not None

        activity = sqlite_session.query(ActivityLog).filter(ActivityLog.action_type == "duplicate_reviewed").one()
        assert activity.actor_id == recruiter.id
        assert str(duplicate_review.id) in activity.description
    finally:
        app.dependency_overrides.clear()


def test_review_duplicate_rejects_unknown_record(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.patch(
            "/api/v1/duplicates/11111111-1111-1111-1111-111111111111/review",
            headers=_header(recruiter),
        )

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "DUPLICATE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_review_duplicate_rejects_already_reviewed_record(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    reviewer = user_factory(email="reviewer@example.com", role="Recruiter")
    candidate_1 = Candidate(zoho_record_id="zr-31", zoho_candidate_id="z-31", full_name="Meera Das")
    candidate_2 = Candidate(zoho_record_id="zr-32", zoho_candidate_id="z-32", full_name="Meera D")
    sqlite_session.add_all([candidate_1, candidate_2])
    sqlite_session.commit()
    sqlite_session.refresh(candidate_1)
    sqlite_session.refresh(candidate_2)

    duplicate_review = DuplicateReview(
        candidate_id=candidate_1.id,
        matched_candidate_id=candidate_2.id,
        match_basis="phone_exact",
        confidence=0.93,
        status="reviewed",
        reviewed_by=reviewer.id,
    )
    sqlite_session.add(duplicate_review)
    sqlite_session.commit()
    sqlite_session.refresh(duplicate_review)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.patch(f"/api/v1/duplicates/{duplicate_review.id}/review", headers=_header(recruiter))

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "DUPLICATE_ALREADY_REVIEWED"
    finally:
        app.dependency_overrides.clear()


def test_review_duplicate_rejects_unauthorized_role(sqlite_session, user_factory) -> None:
    candidate_user = user_factory(role="Candidate")
    candidate_1 = Candidate(zoho_record_id="zr-41", zoho_candidate_id="z-41", full_name="Ishaan Rao")
    candidate_2 = Candidate(zoho_record_id="zr-42", zoho_candidate_id="z-42", full_name="Ishaan R")
    sqlite_session.add_all([candidate_1, candidate_2])
    sqlite_session.commit()
    sqlite_session.refresh(candidate_1)
    sqlite_session.refresh(candidate_2)

    duplicate_review = DuplicateReview(
        candidate_id=candidate_1.id,
        matched_candidate_id=candidate_2.id,
        match_basis="phone_exact",
        confidence=0.93,
        status="pending",
    )
    sqlite_session.add(duplicate_review)
    sqlite_session.commit()
    sqlite_session.refresh(duplicate_review)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.patch(f"/api/v1/duplicates/{duplicate_review.id}/review", headers=_header(candidate_user))

        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ERROR"
    finally:
        app.dependency_overrides.clear()
