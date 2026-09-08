from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError as JWTInvalidTokenError
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.normalization_rule_repository import NormalizationRuleRepository
from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
from app.repositories.saved_filter_repository import SavedFilterRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.services.candidate_service import CandidateService
from app.services.dashboard_service import DashboardService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.duplicate_service import DuplicateService
from app.services.auth_service import AuthService
from app.services.integration_service import IntegrationService
from app.services.job_description_service import JobDescriptionService
from app.services.normalization_service import NormalizationService
from app.services.ranking_criteria_service import RankingCriteriaService
from app.services.ranking_service import RankingService
from app.services.saved_filter_service import SavedFilterService
from app.services.sync_service import SyncService
from app.services.auth_service import (
    AccessDeniedError,
    ExpiredTokenError,
    InactiveAccountError,
    InvalidTokenError,
    MissingTokenError,
)


http_bearer = HTTPBearer(auto_error=False)


def get_auth_repository(session: Session = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session)


def get_auth_service(repository: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repository)


def get_integration_settings_repository(
    session: Session = Depends(get_db_session),
) -> IntegrationSettingsRepository:
    return IntegrationSettingsRepository(session)


def get_zoho_oauth_client() -> ZohoOAuthClient:
    return ZohoOAuthClient()


def get_zoho_recruit_client() -> ZohoRecruitClient:
    return ZohoRecruitClient()


def get_sync_log_repository(session: Session = Depends(get_db_session)) -> SyncLogRepository:
    return SyncLogRepository(session)


def get_candidate_repository(session: Session = Depends(get_db_session)) -> CandidateRepository:
    return CandidateRepository(session)


def get_duplicate_review_repository(session: Session = Depends(get_db_session)) -> DuplicateReviewRepository:
    return DuplicateReviewRepository(session)


def get_duplicate_detection_service(
    candidate_repository: CandidateRepository = Depends(get_candidate_repository),
    duplicate_review_repository: DuplicateReviewRepository = Depends(get_duplicate_review_repository),
) -> DuplicateDetectionService:
    return DuplicateDetectionService(
        candidate_repository=candidate_repository,
        duplicate_review_repository=duplicate_review_repository,
    )


def get_integration_service(
    repository: IntegrationSettingsRepository = Depends(get_integration_settings_repository),
    candidate_repository: CandidateRepository = Depends(get_candidate_repository),
    zoho_oauth_client: ZohoOAuthClient = Depends(get_zoho_oauth_client),
    zoho_recruit_client: ZohoRecruitClient = Depends(get_zoho_recruit_client),
) -> IntegrationService:
    return IntegrationService(
        repository=repository,
        candidate_repository=candidate_repository,
        zoho_oauth_client=zoho_oauth_client,
        zoho_recruit_client=zoho_recruit_client,
    )


def get_job_description_repository(session: Session = Depends(get_db_session)) -> JobDescriptionRepository:
    return JobDescriptionRepository(session)


def get_job_description_service(
    repository: JobDescriptionRepository = Depends(get_job_description_repository),
) -> JobDescriptionService:
    return JobDescriptionService(repository=repository)


def get_saved_filter_repository(session: Session = Depends(get_db_session)) -> SavedFilterRepository:
    return SavedFilterRepository(session)


def get_candidate_service(
    repository: CandidateRepository = Depends(get_candidate_repository),
    job_description_repository: JobDescriptionRepository = Depends(get_job_description_repository),
) -> CandidateService:
    return CandidateService(repository=repository, job_description_repository=job_description_repository)


def get_saved_filter_service(
    repository: SavedFilterRepository = Depends(get_saved_filter_repository),
    job_description_repository: JobDescriptionRepository = Depends(get_job_description_repository),
) -> SavedFilterService:
    return SavedFilterService(repository=repository, job_description_repository=job_description_repository)


def get_activity_log_repository(session: Session = Depends(get_db_session)) -> ActivityLogRepository:
    return ActivityLogRepository(session)


def get_duplicate_service(
    duplicate_review_repository: DuplicateReviewRepository = Depends(get_duplicate_review_repository),
    job_description_repository: JobDescriptionRepository = Depends(get_job_description_repository),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> DuplicateService:
    return DuplicateService(
        duplicate_review_repository=duplicate_review_repository,
        job_description_repository=job_description_repository,
        activity_log_repository=activity_log_repository,
    )


def get_normalization_rule_repository(
    session: Session = Depends(get_db_session),
) -> NormalizationRuleRepository:
    return NormalizationRuleRepository(session)


def get_normalization_service(
    repository: NormalizationRuleRepository = Depends(get_normalization_rule_repository),
) -> NormalizationService:
    return NormalizationService(repository=repository)


def get_dashboard_service(
    session: Session = Depends(get_db_session),
    integration_settings_repository: IntegrationSettingsRepository = Depends(get_integration_settings_repository),
) -> DashboardService:
    return DashboardService(session=session, integration_settings_repository=integration_settings_repository)


def get_sync_service(
    sync_log_repository: SyncLogRepository = Depends(get_sync_log_repository),
    candidate_repository: CandidateRepository = Depends(get_candidate_repository),
    integration_repository: IntegrationSettingsRepository = Depends(get_integration_settings_repository),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
    duplicate_detection_service: DuplicateDetectionService = Depends(get_duplicate_detection_service),
    normalization_service: NormalizationService = Depends(get_normalization_service),
    zoho_oauth_client: ZohoOAuthClient = Depends(get_zoho_oauth_client),
    zoho_recruit_client: ZohoRecruitClient = Depends(get_zoho_recruit_client),
) -> SyncService:
    return SyncService(
        sync_log_repository=sync_log_repository,
        candidate_repository=candidate_repository,
        integration_repository=integration_repository,
        activity_log_repository=activity_log_repository,
        duplicate_detection_service=duplicate_detection_service,
        normalization_service=normalization_service,
        zoho_oauth_client=zoho_oauth_client,
        zoho_recruit_client=zoho_recruit_client,
    )


def get_ranking_criteria_repository(session: Session = Depends(get_db_session)) -> RankingCriteriaRepository:
    return RankingCriteriaRepository(session)


def get_ranking_criteria_service(
    repository: RankingCriteriaRepository = Depends(get_ranking_criteria_repository),
    job_description_repository: JobDescriptionRepository = Depends(get_job_description_repository),
) -> RankingCriteriaService:
    return RankingCriteriaService(
        repository=repository,
        job_description_repository=job_description_repository,
    )


def get_ranking_service(
    session: Session = Depends(get_db_session),
    job_description_repository: JobDescriptionRepository = Depends(get_job_description_repository),
    ranking_criteria_repository: RankingCriteriaRepository = Depends(get_ranking_criteria_repository),
    candidate_repository: CandidateRepository = Depends(get_candidate_repository),
) -> RankingService:
    return RankingService(
        session=session,
        job_description_repository=job_description_repository,
        ranking_criteria_repository=ranking_criteria_repository,
        candidate_repository=candidate_repository,
    )


def get_current_recruiter(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    repository: AuthRepository = Depends(get_auth_repository),
) -> User:
    if credentials is None:
        raise MissingTokenError()

    try:
        payload = decode_access_token(credentials.credentials)
    except ExpiredSignatureError as exc:
        raise ExpiredTokenError() from exc
    except JWTInvalidTokenError as exc:
        raise InvalidTokenError() from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError()

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise InvalidTokenError() from exc

    recruiter = repository.get_user_by_id(user_id)
    if recruiter is None:
        raise InvalidTokenError()

    if not recruiter.is_active:
        raise InactiveAccountError()

    return recruiter


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def role_dependency(current_recruiter: User = Depends(get_current_recruiter)) -> User:
        if current_recruiter.role not in allowed_roles:
            raise AccessDeniedError()
        return current_recruiter

    return role_dependency
