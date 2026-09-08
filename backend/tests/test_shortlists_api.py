from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.shortlist import Shortlist
from app.models.shortlist_candidate import ShortlistCandidate
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_create_shortlist_with_candidates(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(jd_code="JD-001", title="Senior Developer", required_skills=["Python"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate1 = candidate_factory(full_name="Alice")
    candidate2 = candidate_factory(full_name="Bob")
    sqlite_session.add_all([candidate1, candidate2])
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/shortlists",
            headers=_header(recruiter),
            json={
                "jd_id": str(jd.id),
                "candidate_ids": [str(candidate1.id), str(candidate2.id)],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["jd_id"] == str(jd.id)
        assert body["recruiter_id"] == str(recruiter.id)
        assert len(body["candidate_ids"]) == 2
        assert str(candidate1.id) in body["candidate_ids"]
        assert str(candidate2.id) in body["candidate_ids"]

        # Verify shortlist was persisted
        shortlist = sqlite_session.query(Shortlist).filter(
            (Shortlist.recruiter_id == recruiter.id) & (Shortlist.jd_id == jd.id)
        ).first()
        assert shortlist is not None
    finally:
        app.dependency_overrides.clear()


def test_create_shortlist_rejects_empty_candidate_list(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(jd_code="JD-002", title="QA Engineer", required_skills=["Testing"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/shortlists",
            headers=_header(recruiter),
            json={
                "jd_id": str(jd.id),
                "candidate_ids": [],
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
    finally:
        app.dependency_overrides.clear()


def test_update_shortlist_replaces_candidates(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(jd_code="JD-003", title="DevOps Engineer", required_skills=["Kubernetes"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate1 = candidate_factory(full_name="Charlie")
    candidate2 = candidate_factory(full_name="Diana")
    candidate3 = candidate_factory(full_name="Eve")
    sqlite_session.add_all([candidate1, candidate2, candidate3])
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)

        # Create initial shortlist with candidate1 and candidate2
        response1 = client.post(
            "/api/v1/shortlists",
            headers=_header(recruiter),
            json={
                "jd_id": str(jd.id),
                "candidate_ids": [str(candidate1.id), str(candidate2.id)],
            },
        )
        assert response1.status_code == 200
        shortlist_id = response1.json()["id"]

        # Update with candidate2 and candidate3 (different set)
        response2 = client.post(
            "/api/v1/shortlists",
            headers=_header(recruiter),
            json={
                "jd_id": str(jd.id),
                "candidate_ids": [str(candidate2.id), str(candidate3.id)],
            },
        )
        assert response2.status_code == 200
        body2 = response2.json()
        assert body2["id"] == shortlist_id  # Same shortlist ID
        assert len(body2["candidate_ids"]) == 2
        assert str(candidate2.id) in body2["candidate_ids"]
        assert str(candidate3.id) in body2["candidate_ids"]
        assert str(candidate1.id) not in body2["candidate_ids"]
    finally:
        app.dependency_overrides.clear()


def test_create_shortlist_requires_authentication(sqlite_session) -> None:
    jd = JobDescription(jd_code="JD-004", title="Frontend Developer", required_skills=["React"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/shortlists",
            json={
                "jd_id": str(jd.id),
                "candidate_ids": ["00000000-0000-0000-0000-000000000000"],
            },
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_export_shortlist_returns_excel_file(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    jd = JobDescription(jd_code="JD-005", title="Backend Engineer", required_skills=["Python"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate = candidate_factory(full_name="Export Candidate", email="export@example.com")
    sqlite_session.add(candidate)
    sqlite_session.commit()

    shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=jd.id)
    sqlite_session.add(shortlist)
    sqlite_session.commit()
    sqlite_session.refresh(shortlist)

    sqlite_session.add(ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate.id))
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/shortlists/{shortlist.id}/export",
            headers=_header(recruiter),
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert len(response.content) > 0
    finally:
        app.dependency_overrides.clear()


def test_export_shortlist_forbidden_for_other_recruiter(
    sqlite_session, user_factory, candidate_factory
) -> None:
    owner = user_factory(role="Recruiter", email="owner@example.com")
    other = user_factory(role="Recruiter", email="other@example.com")
    jd = JobDescription(jd_code="JD-006", title="Data Engineer", required_skills=["SQL"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate = candidate_factory(full_name="Forbidden Candidate")
    sqlite_session.add(candidate)
    sqlite_session.commit()

    shortlist = Shortlist(recruiter_id=owner.id, jd_id=jd.id)
    sqlite_session.add(shortlist)
    sqlite_session.commit()
    sqlite_session.refresh(shortlist)

    sqlite_session.add(ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate.id))
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/v1/shortlists/{shortlist.id}/export",
            headers=_header(other),
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_shortlists_by_recruiter(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter", email="shortlist-list@example.com")
    jd = JobDescription(jd_code="JD-007", title="Platform Engineer", required_skills=["Python", "AWS"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate1 = candidate_factory(full_name="List Candidate One", email="list1@example.com")
    candidate2 = candidate_factory(full_name="List Candidate Two", email="list2@example.com")
    sqlite_session.add_all([candidate1, candidate2])
    sqlite_session.commit()

    shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=jd.id)
    sqlite_session.add(shortlist)
    sqlite_session.commit()
    sqlite_session.refresh(shortlist)

    sqlite_session.add_all(
        [
            ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate1.id),
            ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate2.id),
        ]
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/shortlists", headers=_header(recruiter))

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["jd_id"] == str(jd.id)
        assert payload[0]["jd_title"] == jd.title
        assert payload[0]["candidate_count"] == 2
        assert len(payload[0]["candidates"]) == 2
        assert payload[0]["candidates"][0]["id"] in {str(candidate1.id), str(candidate2.id)}
    finally:
        app.dependency_overrides.clear()


def test_list_shortlists_filters_candidates_by_job_description(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter", email="shortlist-jd-filter@example.com")
    selected_jd = JobDescription(jd_code="JD-007A", title="Python Engineer", required_skills=["Python"])
    other_jd = JobDescription(jd_code="JD-007B", title="Java Engineer", required_skills=["Java"])
    sqlite_session.add_all([selected_jd, other_jd])
    sqlite_session.commit()
    sqlite_session.refresh(selected_jd)
    sqlite_session.refresh(other_jd)

    selected_candidate = candidate_factory(full_name="Python Candidate")
    other_candidate = candidate_factory(full_name="Java Candidate")
    selected_shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=selected_jd.id)
    other_shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=other_jd.id)
    sqlite_session.add_all([selected_candidate, other_candidate, selected_shortlist, other_shortlist])
    sqlite_session.commit()
    sqlite_session.refresh(selected_shortlist)
    sqlite_session.refresh(other_shortlist)

    sqlite_session.add_all(
        [
            ShortlistCandidate(shortlist_id=selected_shortlist.id, candidate_id=selected_candidate.id),
            ShortlistCandidate(shortlist_id=other_shortlist.id, candidate_id=other_candidate.id),
        ]
    )
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/shortlists?jd_id={selected_jd.id}", headers=_header(recruiter))

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["jd_id"] == str(selected_jd.id)
        assert [candidate["id"] for candidate in payload[0]["candidates"]] == [str(selected_candidate.id)]
    finally:
        app.dependency_overrides.clear()


def test_remove_candidate_from_shortlist_success(sqlite_session, user_factory, candidate_factory) -> None:
    recruiter = user_factory(role="Recruiter", email="remove-success@example.com")
    jd = JobDescription(jd_code="JD-008", title="Security Engineer", required_skills=["Python"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate = candidate_factory(full_name="Candidate Remove")
    shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=jd.id)
    sqlite_session.add(shortlist)
    sqlite_session.commit()
    sqlite_session.refresh(shortlist)

    sqlite_session.add(ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate.id))
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.delete(
            f"/api/v1/shortlists/{shortlist.id}/candidates/{candidate.id}",
            headers=_header(recruiter),
        )

        assert response.status_code == 204

        remaining = sqlite_session.query(ShortlistCandidate).filter(
            (ShortlistCandidate.shortlist_id == shortlist.id)
            & (ShortlistCandidate.candidate_id == candidate.id)
        ).first()
        assert remaining is None
    finally:
        app.dependency_overrides.clear()


def test_remove_candidate_from_shortlist_forbidden(sqlite_session, user_factory, candidate_factory) -> None:
    owner = user_factory(role="Recruiter", email="remove-owner@example.com")
    other = user_factory(role="Recruiter", email="remove-other@example.com")
    jd = JobDescription(jd_code="JD-009", title="SRE", required_skills=["Linux"])
    sqlite_session.add(jd)
    sqlite_session.commit()
    sqlite_session.refresh(jd)

    candidate = candidate_factory(full_name="Candidate Protected")
    shortlist = Shortlist(recruiter_id=owner.id, jd_id=jd.id)
    sqlite_session.add(shortlist)
    sqlite_session.commit()
    sqlite_session.refresh(shortlist)

    sqlite_session.add(ShortlistCandidate(shortlist_id=shortlist.id, candidate_id=candidate.id))
    sqlite_session.commit()

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.delete(
            f"/api/v1/shortlists/{shortlist.id}/candidates/{candidate.id}",
            headers=_header(other),
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
