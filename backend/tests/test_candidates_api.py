from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def _seed_candidates(sqlite_session) -> None:
    now = datetime.now(UTC)
    sqlite_session.add_all(
        [
            Candidate(
                zoho_record_id="z-1",
                zoho_candidate_id="z-1",
                full_name="Arjun Kumar",
                email="arjun@example.com",
                phone="+91 98XXXXXX10",
                current_company="TechNova Solutions",
                current_location="Bengaluru",
                preferred_location="Bengaluru",
                skills=["Java", "Spring Boot", "Microservices"],
                total_experience_years=6,
                relevant_experience_years=5,
                notice_period_days=30,
                status="active",
                degree="B.E. CSE",
                normalized_degree="Bachelor Degree - Computer Science",
                current_ctc=10,
                expected_ctc=14,
                source="zoho_recruit",
                match_metadata={
                    "jd_id": "JD-2026-014",
                    "jd_title": "Java Backend Developer",
                    "match_percentage": 92,
                    "match_score": 92,
                    "matched_criteria": ["Java", "Spring Boot", "Microservices"],
                },
                raw_payload={
                    "Current_Location": "Bangalore Karnataka",
                    "Preferred_Location": "Bangalore",
                    "Highest_Qualification": "B.E. CSE",
                    "Notice_Period": "1 Month",
                    "Skill_Set": "java,spring boot,micro services",
                        "Certification": "AWS Certified Developer",
                        "Previous_Company": "Infosys",
                        "Employment_Status": "employed",
                },
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=1),
            ),
            Candidate(
                zoho_record_id="z-2",
                zoho_candidate_id="z-2",
                full_name="Priya Sharma",
                email="priya@example.com",
                current_company="CloudEdge Systems",
                current_location="Bengaluru",
                skills=["Java", "Python", "AWS"],
                total_experience_years=5,
                notice_period_days=15,
                status="open_to_opportunities",
                match_metadata={"match_percentage": 85},
                source="zoho_recruit",
                raw_payload={
                    "Certification": "Azure Fundamentals",
                    "Previous_Company": "Capgemini",
                    "Employment_Status": "employed",
                },
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(hours=12),
            ),
            Candidate(
                zoho_record_id="z-3",
                zoho_candidate_id="z-3",
                full_name="Ravi Verma",
                email="ravi@example.com",
                current_company="Nexus Labs",
                current_location="Hyderabad",
                skills=["Python", "FastAPI"],
                total_experience_years=4,
                relevant_experience_years=3,
                notice_period_days=45,
                status="active",
                degree="MCA",
                normalized_degree="Master Degree - Computer Applications",
                source="referral",
                match_metadata={"match_percentage": 74},
                raw_payload={
                    "Certification": "Google Cloud Associate",
                    "Previous_Company": "Nexus Labs",
                    "Employment_Status": "contract",
                },
                created_at=now - timedelta(days=1),
                updated_at=now - timedelta(hours=2),
            ),
        ]
    )
    sqlite_session.commit()


def test_candidates_list_paginates_results(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/candidates?page=2&page_size=2", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert body["total_items"] == 3
        assert body["total_pages"] == 2
        assert len(body["items"]) == 1
        assert body["items"][0]["full_name"] == "Ravi Verma"
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_searches_name_skill_and_company(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)

        name_response = client.get("/api/v1/candidates?q=arjun", headers=_header(recruiter))
        skill_response = client.get("/api/v1/candidates?q=python", headers=_header(recruiter))
        company_response = client.get("/api/v1/candidates?q=cloudedge", headers=_header(recruiter))

        assert name_response.status_code == 200
        assert [item["full_name"] for item in name_response.json()["items"]] == ["Arjun Kumar"]

        assert skill_response.status_code == 200
        assert {item["full_name"] for item in skill_response.json()["items"]} == {"Priya Sharma", "Ravi Verma"}

        assert company_response.status_code == 200
        assert [item["full_name"] for item in company_response.json()["items"]] == ["Priya Sharma"]
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_rejects_invalid_pagination(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/candidates?page=0&page_size=10", headers=_header(recruiter))

        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_supports_basic_filters_individually_and_combined(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)

        skills_response = client.get("/api/v1/candidates?skills=Spring%20Boot", headers=_header(recruiter))
        experience_min_response = client.get("/api/v1/candidates?experience_min=6", headers=_header(recruiter))
        experience_max_response = client.get("/api/v1/candidates?experience_max=4", headers=_header(recruiter))
        location_response = client.get("/api/v1/candidates?location=Hyderabad", headers=_header(recruiter))
        notice_response = client.get("/api/v1/candidates?notice_period_max=20", headers=_header(recruiter))
        status_response = client.get("/api/v1/candidates?status=open_to_opportunities", headers=_header(recruiter))
        grouped_status_response = client.get("/api/v1/candidates?status=active,open_to_opportunities", headers=_header(recruiter))
        combined_response = client.get(
            "/api/v1/candidates?skills=Java,Spring%20Boot&experience_min=5&experience_max=6&location=Bengaluru&notice_period_max=30&status=active",
            headers=_header(recruiter),
        )

        assert skills_response.status_code == 200
        assert [item["full_name"] for item in skills_response.json()["items"]] == ["Arjun Kumar"]

        assert experience_min_response.status_code == 200
        assert {item["full_name"] for item in experience_min_response.json()["items"]} == {"Arjun Kumar"}

        assert experience_max_response.status_code == 200
        assert [item["full_name"] for item in experience_max_response.json()["items"]] == ["Ravi Verma"]

        assert location_response.status_code == 200
        assert [item["full_name"] for item in location_response.json()["items"]] == ["Ravi Verma"]

        assert notice_response.status_code == 200
        assert [item["full_name"] for item in notice_response.json()["items"]] == ["Priya Sharma"]

        assert status_response.status_code == 200
        assert [item["full_name"] for item in status_response.json()["items"]] == ["Priya Sharma"]

        assert grouped_status_response.status_code == 200
        assert {item["full_name"] for item in grouped_status_response.json()["items"]} == {
            "Arjun Kumar",
            "Priya Sharma",
            "Ravi Verma",
        }

        assert combined_response.status_code == 200
        assert [item["full_name"] for item in combined_response.json()["items"]] == ["Arjun Kumar"]
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_supports_jd_skill_scope_and_any_jd(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)

    java_jd = JobDescription(
        jd_code="JD-2026-014",
        title="Java Backend Developer",
        required_skills=["Java", "Microservices"],
    )
    python_jd = JobDescription(
        jd_code="JD-2026-101",
        title="Python API Developer",
        required_skills=["Python", "FastAPI"],
    )
    sqlite_session.add_all([java_jd, python_jd])
    sqlite_session.commit()
    sqlite_session.refresh(java_jd)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)

        jd_scoped_response = client.get(f"/api/v1/candidates?jd_id={java_jd.id}", headers=_header(recruiter))
        jd_with_extra_skills_response = client.get(
            f"/api/v1/candidates?jd_id={java_jd.id}&skills=Spring%20Boot",
            headers=_header(recruiter),
        )
        any_jd_response = client.get("/api/v1/candidates?skills=Python", headers=_header(recruiter))

        assert jd_scoped_response.status_code == 200
        assert [item["full_name"] for item in jd_scoped_response.json()["items"]] == ["Arjun Kumar", "Priya Sharma"]

        assert jd_with_extra_skills_response.status_code == 200
        assert [item["full_name"] for item in jd_with_extra_skills_response.json()["items"]] == ["Arjun Kumar"]

        assert any_jd_response.status_code == 200
        assert {item["full_name"] for item in any_jd_response.json()["items"]} == {"Priya Sharma", "Ravi Verma"}
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_rejects_invalid_experience_filter_range(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/candidates?experience_min=7&experience_max=3", headers=_header(recruiter))

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "INVALID_FILTER_CRITERIA"
        assert body["message"] == "Experience minimum must be less than or equal to experience maximum"
    finally:
        app.dependency_overrides.clear()

def test_candidates_list_supports_advanced_filters_and_combines_with_basic(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)

        degree_response = client.get("/api/v1/candidates?degree=bachelor", headers=_header(recruiter))
        certification_response = client.get("/api/v1/candidates?certification=aws", headers=_header(recruiter))
        resume_response = client.get("/api/v1/candidates?resume_updated_since=1", headers=_header(recruiter))
        source_response = client.get("/api/v1/candidates?source=referral", headers=_header(recruiter))
        relevant_experience_response = client.get("/api/v1/candidates?relevant_experience=5", headers=_header(recruiter))
        current_ctc_response = client.get("/api/v1/candidates?current_ctc=10", headers=_header(recruiter))
        expected_ctc_response = client.get("/api/v1/candidates?expected_ctc=15", headers=_header(recruiter))
        preferred_location_response = client.get("/api/v1/candidates?preferred_location=bengaluru", headers=_header(recruiter))
        previous_company_response = client.get("/api/v1/candidates?previous_company=infosys", headers=_header(recruiter))
        employment_status_response = client.get("/api/v1/candidates?employment_status=contract", headers=_header(recruiter))
        mixed_response = client.get(
            "/api/v1/candidates?skills=java&location=bengaluru&preferred_location=bengaluru&degree=bachelor&certification=aws&source=zoho_recruit",
            headers=_header(recruiter),
        )

        assert degree_response.status_code == 200
        assert [item["full_name"] for item in degree_response.json()["items"]] == ["Arjun Kumar"]

        assert certification_response.status_code == 200
        assert [item["full_name"] for item in certification_response.json()["items"]] == ["Arjun Kumar"]

        assert resume_response.status_code == 200
        assert {item["full_name"] for item in resume_response.json()["items"]} == {"Priya Sharma", "Ravi Verma"}

        assert source_response.status_code == 200
        assert [item["full_name"] for item in source_response.json()["items"]] == ["Ravi Verma"]

        assert relevant_experience_response.status_code == 200
        assert [item["full_name"] for item in relevant_experience_response.json()["items"]] == ["Arjun Kumar"]

        assert current_ctc_response.status_code == 200
        assert [item["full_name"] for item in current_ctc_response.json()["items"]] == ["Arjun Kumar"]

        assert expected_ctc_response.status_code == 200
        assert [item["full_name"] for item in expected_ctc_response.json()["items"]] == []

        assert preferred_location_response.status_code == 200
        assert [item["full_name"] for item in preferred_location_response.json()["items"]] == ["Arjun Kumar"]

        assert previous_company_response.status_code == 200
        assert [item["full_name"] for item in previous_company_response.json()["items"]] == ["Arjun Kumar"]

        assert employment_status_response.status_code == 200
        assert [item["full_name"] for item in employment_status_response.json()["items"]] == ["Ravi Verma"]

        assert mixed_response.status_code == 200
        assert [item["full_name"] for item in mixed_response.json()["items"]] == ["Arjun Kumar"]
    finally:
        app.dependency_overrides.clear()

def test_candidate_details_returns_complete_profile(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    _seed_candidates(sqlite_session)
    candidate = sqlite_session.scalar(select(Candidate).where(Candidate.zoho_candidate_id == "z-1"))
    assert candidate is not None

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/candidates/{candidate.id}", headers=_header(recruiter))

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(candidate.id)
        assert body["full_name"] == "Arjun Kumar"
        assert body["email"] == "arjun@example.com"
        assert body["phone"] == "+91 98XXXXXX10"
        assert body["match_context"]["jd_id"] == "JD-2026-014"
        assert body["match_context"]["jd_title"] == "Java Backend Developer"
        assert body["match_context"]["match_percentage"] == 92
        assert body["normalized_data"]
        
        # Verify extended_fields are included in response
        assert "extended_fields" in body, "extended_fields is missing from response"
        assert isinstance(body["extended_fields"], dict), "extended_fields should be a dict"
        assert "personal_contact" in body["extended_fields"]
        assert "employment" in body["extended_fields"]
        assert "interview_process" in body["extended_fields"]
        assert "candidate_lifecycle" in body["extended_fields"]
        assert "salary_benefits" in body["extended_fields"]
        assert "referral_vendor_sourcing" in body["extended_fields"]

        normalized_fields = {item["field"] for item in body["normalized_data"]}
        assert "current_location" in normalized_fields
        assert "preferred_location" in normalized_fields
        assert "degree" in normalized_fields
        assert "notice_period" in normalized_fields
        assert "skill" in normalized_fields
    finally:
        app.dependency_overrides.clear()


def test_candidate_details_returns_not_found_for_unknown_id(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        unknown_id = uuid4()
        response = client.get(f"/api/v1/candidates/{unknown_id}", headers=_header(recruiter))

        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "CANDIDATE_NOT_FOUND"
        assert body["message"] == "Candidate was not found"
        assert body["path"] == f"/api/v1/candidates/{unknown_id}"
    finally:
        app.dependency_overrides.clear()
