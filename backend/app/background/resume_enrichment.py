from __future__ import annotations

import logging
from uuid import UUID

from app.core.database import get_session_factory
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_sync_ledger_repository import CandidateSyncLedgerRepository
from app.repositories.candidate_review_repository import CandidateReviewRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.repositories.proposed_field_change_repository import ProposedFieldChangeRepository
from app.repositories.review_batch_repository import ReviewBatchRepository
from app.repositories.zoho_field_metadata_repository import ZohoFieldMetadataRepository
from app.services.integration_service import IntegrationService
from app.services.resume_enrichment_service import ResumeEnrichmentService
from app.services.resume_fetch_service import ResumeFetchService
from app.storage import get_storage_backend


logger = logging.getLogger(__name__)


def process_review_batch_job(batch_id: UUID) -> None:
    """Run a review batch outside the request session and persist each candidate result."""
    session = get_session_factory()()
    try:
        candidate_repository = CandidateRepository(session)
        integration_repository = IntegrationSettingsRepository(session)
        zoho_recruit_client = ZohoRecruitClient()
        service = ResumeEnrichmentService(
            review_batch_repository=ReviewBatchRepository(session),
            candidate_review_repository=CandidateReviewRepository(session),
            proposed_field_change_repository=ProposedFieldChangeRepository(session),
            candidate_repository=candidate_repository,
            zoho_recruit_client=zoho_recruit_client,
            resume_fetch_service=ResumeFetchService(
                candidate_repository=candidate_repository,
                zoho_recruit_client=zoho_recruit_client,
                storage=get_storage_backend(),
            ),
            activity_log_repository=ActivityLogRepository(session),
            zoho_field_metadata_repository=ZohoFieldMetadataRepository(session),
            integration_service=IntegrationService(
                repository=integration_repository,
                candidate_repository=candidate_repository,
                zoho_oauth_client=ZohoOAuthClient(),
                zoho_recruit_client=zoho_recruit_client,
            ),
            candidate_sync_ledger_repository=CandidateSyncLedgerRepository(session),
        )
        service.process_review_batch(batch_id)
    except Exception:
        session.rollback()
        logger.exception("Resume enrichment batch %s failed", batch_id)
        batch = ReviewBatchRepository(session).get_by_id(batch_id)
        if batch is not None:
            batch.status = "FAILED"
            batch.error_message = "Background processing failed. See server logs for details."
            session.commit()
    finally:
        session.close()