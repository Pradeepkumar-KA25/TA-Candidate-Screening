from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.crypto import encrypt_value
from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview
from app.models.integration_settings import IntegrationSettings
from app.models.job_description import JobDescription
from app.models.saved_filter import SavedFilter
from app.models.shortlist import Shortlist
from app.models.shortlist_candidate import ShortlistCandidate
from app.models.sync_log import SyncLog
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def _seed_dashboard_data(sqlite_session, recruiter: User) -> None:
    now = datetime.now(UTC)

    candidate_one = Candidate(
        zoho_record_id="z-1",
        zoho_candidate_id="z-1",
        full_name="Asha Sharma",
        email="asha@example.com",
        status="active",
        source="zoho_recruit",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    candidate_two = Candidate(
        zoho_record_id="z-2",
        zoho_candidate_id="z-2",
        full_name="Ravi Kumar",
        email="ravi@example.com",
        status="active",
        source="zoho_recruit",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
    )
    sqlite_session.add_all([candidate_one, candidate_two])
    sqlite_session.flush()

    sqlite_session.add(
        IntegrationSettings(
            provider="zoho_recruit",
            access_token_encrypted=encrypt_value("active-token"),
            refresh_token_encrypted=encrypt_value("refresh-token"),
            token_expires_at=now + timedelta(hours=1),
            access_level="read_only",
            sync_type="manual",
            last_successful_sync_at=now - timedelta(minutes=30),
        )
    )

    job_description = JobDescription(jd_code="JD-001", title="Backend Engineer", required_skills=["Python"])
    sqlite_session.add(job_description)
    sqlite_session.flush()

    older_shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=job_description.id, created_at=now - timedelta(days=2))
    current_shortlist = Shortlist(recruiter_id=recruiter.id, jd_id=job_description.id, created_at=now - timedelta(minutes=20))
    sqlite_session.add_all([older_shortlist, current_shortlist])
    sqlite_session.flush()

    sqlite_session.add_all(
        [
            ShortlistCandidate(shortlist_id=older_shortlist.id, candidate_id=candidate_one.id),
            ShortlistCandidate(shortlist_id=current_shortlist.id, candidate_id=candidate_one.id),
            ShortlistCandidate(shortlist_id=current_shortlist.id, candidate_id=candidate_two.id),
        ]
    )

    sqlite_session.add(
        SyncLog(
            triggered_by=recruiter.id,
            status="completed",
            records_fetched=2,
            records_new=1,
            records_updated=1,
            completed_at=now - timedelta(minutes=30),
        )
    )

    sqlite_session.add_all(
        [
            SavedFilter(recruiter_id=recruiter.id, name="Backend filter", filter_criteria={"skills": ["Python"]}),
            SavedFilter(recruiter_id=recruiter.id, name="Frontend filter", filter_criteria={"skills": ["Angular"]}),
        ]
    )

    sqlite_session.add_all(
        [
            ActivityLog(
                actor_id=recruiter.id,
                action_type="export_downloaded",
                description="Exported shortlist to Excel",
                occurred_at=now - timedelta(minutes=5),
            ),
            ActivityLog(
                actor_id=recruiter.id,
                action_type="shortlist_prepared",
                description="Prepared candidate shortlist",
                occurred_at=now - timedelta(minutes=15),
            ),
            ActivityLog(
                actor_id=recruiter.id,
                action_type="filter_used",
                description="Used Java Backend filter template",
                occurred_at=now - timedelta(minutes=25),
            ),
            ActivityLog(
                actor_id=recruiter.id,
                action_type="sync_completed",
                description="Zoho candidate sync completed",
                occurred_at=now - timedelta(minutes=35),
            ),
        ]
    )
    sqlite_session.commit()


def test_dashboard_stats_returns_aggregates(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_dashboard_data(sqlite_session, recruiter)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/dashboard/stats", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["total_candidates"] == 2
        assert body["current_shortlist_size"] == 2
        assert body["saved_filter_count"] == 2
        assert body["last_sync_at"] is not None
        assert body["new_candidates"] == 2
        assert body["shortlisted_candidates"] == 2
        assert body["last_sync_status"] == "completed"
        assert body["last_sync_new"] == 1
        assert body["last_sync_updated"] == 1
        assert body["source_breakdown"] == [{"label": "zoho_recruit", "count": 2}]
    finally:
        app.dependency_overrides.clear()


def test_dashboard_recent_activity_returns_ordered_limited_items(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_dashboard_data(sqlite_session, recruiter)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/dashboard/recent-activity?limit=2", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["items"][0]["action_type"] == "export_downloaded"
        assert body["items"][1]["action_type"] == "shortlist_prepared"
    finally:
        app.dependency_overrides.clear()


def test_dashboard_recent_activity_includes_duplicate_review_audit(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    candidate_1 = Candidate(zoho_record_id="z-101", zoho_candidate_id="z-101", full_name="Asha Sharma")
    candidate_2 = Candidate(zoho_record_id="z-102", zoho_candidate_id="z-102", full_name="Asha S")
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
        review_response = client.patch(f"/api/v1/duplicates/{duplicate_review.id}/review", headers=_header(recruiter))
        assert review_response.status_code == 200

        activity_response = client.get("/api/v1/dashboard/recent-activity?limit=5", headers=_header(recruiter))
        assert activity_response.status_code == 200
        body = activity_response.json()
        assert body["items"][0]["action_type"] == "duplicate_reviewed"
        assert str(duplicate_review.id) in body["items"][0]["description"]
    finally:
        app.dependency_overrides.clear()


def test_dashboard_stats_requires_authentication(sqlite_session, user_factory) -> None:
    user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/dashboard/stats")

        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_ERROR"
    finally:
        app.dependency_overrides.clear()
