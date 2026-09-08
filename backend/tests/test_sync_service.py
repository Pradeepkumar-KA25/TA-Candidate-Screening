from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.crypto import encrypt_value
from app.integrations.zoho_recruit import ZohoCandidatesPage
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings
from app.models.user import User
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.repositories.normalization_rule_repository import NormalizationRuleRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.services.duplicate_detection_service import DuplicateDetectionResult
from app.services.normalization_service import NormalizationService
from app.services.sync_service import SyncConflictError, SyncService


class FakeZohoOAuthClient:
    def refresh_access_token(self, refresh_token: str):
        return None


class FakeZohoRecruitClient:
    def __init__(
        self,
        payloads: list[dict] | None = None,
        error: Exception | None = None,
        pages: dict[int, ZohoCandidatesPage] | None = None,
    ) -> None:
        self.payloads = payloads or []
        self.error = error
        self.pages = pages

    def fetch_candidates_page(self, access_token: str, page: int, per_page: int) -> ZohoCandidatesPage:
        if self.error is not None:
            raise self.error
        if self.pages is not None:
            return self.pages.get(page, ZohoCandidatesPage(candidates=[], has_more=False))
        return ZohoCandidatesPage(candidates=self.payloads, has_more=False)


class FakeDuplicateDetectionService:
    def __init__(self, should_raise: Exception | None = None) -> None:
        self.should_raise = should_raise
        self.called = 0

    def detect(self) -> DuplicateDetectionResult:
        self.called += 1
        if self.should_raise is not None:
            raise self.should_raise
        return DuplicateDetectionResult(scanned=0, potential_duplicates=0, created=0, updated=0)


def _build_sync_service(
    sqlite_session,
    zoho_client: FakeZohoRecruitClient,
    duplicate_detection_service: FakeDuplicateDetectionService | None = None,
) -> SyncService:
    return SyncService(
        sync_log_repository=SyncLogRepository(sqlite_session),
        candidate_repository=CandidateRepository(sqlite_session),
        integration_repository=IntegrationSettingsRepository(sqlite_session),
        activity_log_repository=ActivityLogRepository(sqlite_session),
        duplicate_detection_service=duplicate_detection_service
        or FakeDuplicateDetectionService(),
        normalization_service=NormalizationService(NormalizationRuleRepository(sqlite_session)),
        zoho_oauth_client=FakeZohoOAuthClient(),
        zoho_recruit_client=zoho_client,
    )


def test_sync_service_success_flow(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    payloads = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Asha Sharma",
            "Email": "asha@example.com",
            "Experience_in_Years": "6",
            "Relevant_Experience": "5",
            "Current_Employer": "Acme",
            "Current_Location": "Bangalore",
            "Preferred_Location": "Bangalore",
            "Notice_Period": "30",
            "Skill_Set": "Python, FastAPI",
            "Highest_Qualification": "btech",
            "Current_Salary": "15",
            "Expected_Salary": "20",
            "Candidate_Status": "active",
            "Source": "LinkedIn",
        },
        {
            "id": "z-2",
            "Candidate_ID": "CAND-2",
            "Full_Name": "Ravi Kumar",
            "Email": "ravi@example.com",
            "Experience_in_Years": "8",
            "Relevant_Experience": "7",
            "Current_Employer": "Globex",
            "Current_Location": "Chennai",
            "Preferred_Location": "Chennai",
            "Notice_Period": "45",
            "Skill_Set": "Java, Spring",
            "Highest_Qualification": "mca",
            "Current_Salary": "18",
            "Expected_Salary": "24",
            "Candidate_Status": "screening",
            "Source": "CareerSite",
        },
    ]

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=payloads))

    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    status = service.get_sync_status(trigger.sync_id)
    assert status.status == "completed"
    assert status.records_fetched == 2
    assert status.records_new == 2
    assert status.records_updated == 0


def test_sync_service_marks_failed_on_client_error(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(error=RuntimeError("Zoho temporary failure")))

    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    status = service.get_sync_status(trigger.sync_id)
    assert status.status == "failed"
    assert status.error_message is not None


def test_sync_service_rejects_concurrent_run(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient())

    first = service.start_sync(recruiter.id)
    assert first.status == "running"

    try:
        service.start_sync(recruiter.id)
        assert False, "Expected SyncConflictError"
    except SyncConflictError:
        assert True


def test_sync_service_resets_stale_running_sync_before_start(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")
    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient())

    stale_log = service.sync_log_repository.create_running(triggered_by=recruiter.id)
    stale_log.started_at = datetime.now(UTC) - timedelta(hours=3)
    service.sync_log_repository.session.add(stale_log)
    service.sync_log_repository.session.commit()

    trigger = service.start_sync(recruiter.id)

    reset_log = service.sync_log_repository.get_by_id(stale_log.id)
    assert reset_log is not None
    assert reset_log.status == "failed"
    assert reset_log.error_message == "automatic reset: stale running sync"
    assert trigger.status == "running"


def test_sync_service_skips_existing_candidate_on_resync(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    first_payload = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Asha Sharma",
            "Email": "asha@example.com",
            "Phone": "9000000001",
            "Current_Employer": "Acme",
            "Current_Location": "Bangalore",
            "Skill_Set": "Python",
        }
    ]
    second_payload = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Asha Sharma",
            "Email": "asha@example.com",
            "Phone": "9000000001",
            "Current_Employer": "Initech",
            "Current_Location": "Bangalore",
            "Skill_Set": "Python, FastAPI",
        }
    ]

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=first_payload))
    trigger_1 = service.start_sync(recruiter.id)
    service.run_sync(trigger_1.sync_id)

    trigger_2 = service.start_sync(recruiter.id)
    service.zoho_recruit_client = FakeZohoRecruitClient(payloads=second_payload)
    service.run_sync(trigger_2.sync_id)

    first_status = service.get_sync_status(trigger_1.sync_id)
    second_status = service.get_sync_status(trigger_2.sync_id)
    assert first_status.records_new == 1
    assert second_status.records_new == 0
    assert second_status.records_updated == 0

    candidate_repo = CandidateRepository(sqlite_session)
    candidate = candidate_repo.get_by_zoho_record_id("z-1")
    assert candidate is not None
    assert candidate.current_company == "Acme"
    assert candidate.zoho_candidate_id == "CAND-1"


def test_sync_service_skips_invalid_candidate_payload(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    payloads = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Valid Candidate",
            "Email": "valid@example.com",
            "Current_Location": "Bangalore",
            "Skill_Set": "Python",
        },
        {
            "id": "z-2",
            "Candidate_ID": "CAND-2",
            "Full_Name": "No Contact Candidate",
            "Current_Location": "Chennai",
        },
    ]

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=payloads))
    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    status = service.get_sync_status(trigger.sync_id)
    assert status.status == "completed"
    assert status.records_fetched == 2
    assert status.records_new == 1
    assert status.records_updated == 0


def test_sync_service_maps_tenant_specific_zoho_fields(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    payloads = [
        {
            "id": "z-tenant-1",
            "Candidate_ID": "KAN-1001",
            "Full_Name": "Dhiraj Rote",
            "Email": "dhiraj@example.com",
            "Experience_in_Yrs": 9,
            "Overall_IT_Experince": "9",
            "Relevant_Exp": "9",
            "Employer_Details": "Envirta Technologies LLC",
            "Current_Work_Location": "Pune",
            "Preferred_Work_Location": "Pune",
            "Highest_Qualification_Held": "Bachelor of Engineering",
            "Skill_Set": "Figma, User Experience",
            "CTC": "18",
            "Notice_Period": "30",
            "Source": "Employee Referral",
        }
    ]

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=payloads))

    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    candidate_repo = CandidateRepository(sqlite_session)
    candidate = candidate_repo.get_by_zoho_record_id("z-tenant-1")
    assert candidate is not None
    assert candidate.zoho_record_id == "z-tenant-1"
    assert candidate.zoho_candidate_id == "KAN-1001"
    assert candidate.total_experience_years == 9
    assert candidate.relevant_experience_years == 9
    assert candidate.current_company == "Envirta Technologies LLC"
    assert candidate.current_location == "Pune"
    assert candidate.preferred_location == "Pune"
    assert candidate.degree == "Bachelor of Engineering"
    assert candidate.source == "Employee Referral"


def test_sync_service_preserves_raw_payload_and_maps_nullable_fields(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    payload = {
        "id": "z-nullable-1",
        "Full_Name": "Meera Das",
        "Email": "meera@example.com",
        "Skill_Set": "Python, FastAPI, SQL",
        "City": "Mumbai",
        "State": "Maharashtra",
        "Country": "India",
        "Current_CTC_Expected_CTC": "12 / 16",
        "Extra_Field": {"foo": "bar"},
    }

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=[payload]))
    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    candidate_repo = CandidateRepository(sqlite_session)
    candidate = candidate_repo.get_by_zoho_record_id("z-nullable-1")
    assert candidate is not None
    assert candidate.zoho_candidate_id is None
    assert candidate.skills == ["Python", "FastAPI", "SQL"]
    assert candidate.current_location == "Mumbai, Maharashtra, India"
    assert candidate.current_ctc == 12
    assert candidate.expected_ctc == 16
    assert candidate.degree is None
    assert candidate.notice_period_days is None
    assert candidate.status is None
    assert candidate.source is None
    assert candidate.raw_payload == payload


def test_sync_service_skips_legacy_row_using_old_zoho_candidate_id_storage(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)

    legacy_candidate = Candidate(
        zoho_record_id="legacy-row",
        zoho_candidate_id="legacy-z-1",
        full_name="Asha Sharma",
        email="asha@example.com",
        source="zoho_recruit",
        status="active",
    )
    legacy_candidate.zoho_record_id = "legacy-z-1"
    sqlite_session.add(legacy_candidate)
    sqlite_session.commit()

    payload = {
        "id": "legacy-z-1",
        "Candidate_ID": "CAND-9001",
        "Full_Name": "Asha Sharma",
        "Email": "asha@example.com",
        "Phone": "9000000001",
        "Skill_Set": "Python, FastAPI",
        "Source": "Indeed",
    }

    service = _build_sync_service(sqlite_session, FakeZohoRecruitClient(payloads=[payload]))
    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    candidate = CandidateRepository(sqlite_session).get_by_zoho_record_id("legacy-z-1")
    assert candidate is not None
    assert candidate.zoho_candidate_id == "legacy-z-1"
    assert candidate.source == "zoho_recruit"

    status = service.get_sync_status(trigger.sync_id)
    assert status.records_new == 0
    assert status.records_updated == 0


def test_sync_service_triggers_duplicate_detection_after_success(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    duplicate_detection_service = FakeDuplicateDetectionService()
    payloads = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Asha Sharma",
            "Email": "asha@example.com",
            "Phone": "9000000001",
            "Skill_Set": "Python",
        }
    ]

    service = _build_sync_service(
        sqlite_session,
        FakeZohoRecruitClient(payloads=payloads),
        duplicate_detection_service=duplicate_detection_service,
    )
    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    assert duplicate_detection_service.called == 1


def test_sync_service_does_not_fail_when_duplicate_detection_fails(sqlite_session, user_factory) -> None:
    recruiter = user_factory(role="Recruiter")

    integration = IntegrationSettings(
        provider="zoho_recruit",
        access_token_encrypted=encrypt_value("active-token"),
        access_level="read_only",
        sync_type="manual",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    sqlite_session.add(integration)
    sqlite_session.commit()

    duplicate_detection_service = FakeDuplicateDetectionService(should_raise=RuntimeError("duplicate detection failed"))
    payloads = [
        {
            "id": "z-1",
            "Candidate_ID": "CAND-1",
            "Full_Name": "Asha Sharma",
            "Email": "asha@example.com",
            "Phone": "9000000001",
            "Skill_Set": "Python",
        }
    ]

    service = _build_sync_service(
        sqlite_session,
        FakeZohoRecruitClient(payloads=payloads),
        duplicate_detection_service=duplicate_detection_service,
    )
    trigger = service.start_sync(recruiter.id)
    service.run_sync(trigger.sync_id)

    status = service.get_sync_status(trigger.sync_id)
    assert status.status == "completed"
    assert duplicate_detection_service.called == 1
