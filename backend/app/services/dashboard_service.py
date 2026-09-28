from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview
from app.models.candidate_review import CandidateReview
from app.models.review_batch import ReviewBatch
from app.models.saved_filter import SavedFilter
from app.models.shortlist import Shortlist
from app.models.shortlist_candidate import ShortlistCandidate
from app.models.sync_log import SyncLog
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.schemas.dashboard import (
    DashboardActivityItemResponse,
    DashboardAttentionItem,
    DashboardCountItem,
    DashboardRecentActivityResponse,
    DashboardStatsResponse,
    DashboardEnrichmentStats,
    DashboardAnalyticsResponse,
    DashboardSeriesPoint,
)


@dataclass(slots=True)
class DashboardService:
    session: Session
    integration_settings_repository: IntegrationSettingsRepository

    provider_name: str = "zoho_recruit"

    def get_stats(self, recruiter_id: UUID) -> DashboardStatsResponse:
        total_candidates = self.session.scalar(select(func.count(Candidate.id))) or 0
        new_candidates = self.session.scalar(
            select(func.count(Candidate.id)).where(Candidate.created_at >= datetime.now(UTC) - timedelta(days=7))
        ) or 0
        saved_filter_count = self.session.scalar(
            select(func.count(SavedFilter.id)).where(SavedFilter.recruiter_id == recruiter_id)
        ) or 0
        current_shortlist_size = self._get_current_shortlist_size(recruiter_id)
        shortlisted_candidates = self.session.scalar(
            select(func.count(func.distinct(ShortlistCandidate.candidate_id)))
            .join(Shortlist, Shortlist.id == ShortlistCandidate.shortlist_id)
            .where(Shortlist.recruiter_id == recruiter_id)
        ) or 0
        screening_candidates = self._count_candidates_with_statuses("active", "screening", "open_to_opportunities")
        interview_candidates = self._count_candidates_with_statuses("interview", "interview_scheduled")
        selected_candidates = self._count_candidates_with_statuses("selected", "hired")
        pending_duplicates = self.session.scalar(
            select(func.count(DuplicateReview.id)).where(DuplicateReview.status == "pending")
        ) or 0
        latest_sync = self.session.scalar(
            select(SyncLog)
            .where(SyncLog.triggered_by == recruiter_id)
            .order_by(desc(SyncLog.started_at), desc(SyncLog.id))
            .limit(1)
        )
        integration = self.integration_settings_repository.get_or_create(self.provider_name)
        enrichment = DashboardEnrichmentStats(
            pending_batches=self.session.scalar(
                select(func.count(ReviewBatch.id)).where(ReviewBatch.status.in_(["PENDING", "PROCESSING"]))
            ) or 0,
            pending_reviews=self.session.scalar(
                select(func.count(CandidateReview.id)).where(CandidateReview.approval_status == "PENDING")
            ) or 0,
            approved_reviews=self.session.scalar(
                select(func.count(CandidateReview.id)).where(CandidateReview.approval_status == "APPROVED")
            ) or 0,
            rejected_reviews=self.session.scalar(
                select(func.count(CandidateReview.id)).where(CandidateReview.approval_status == "REJECTED")
            ) or 0,
        )
        activity_summary = [
            DashboardCountItem(label=action_type, count=count)
            for action_type, count in self.session.execute(
                select(ActivityLog.action_type, func.count(ActivityLog.id))
                .group_by(ActivityLog.action_type)
                .order_by(desc(func.count(ActivityLog.id)))
                .limit(8)
            )
        ]

        attention_items: list[DashboardAttentionItem] = []
        if latest_sync and latest_sync.status == "failed":
            attention_items.append(DashboardAttentionItem(label="Latest sync failed", count=1, route="/sync-candidates"))
        if pending_duplicates:
            attention_items.append(
                DashboardAttentionItem(label="Duplicate matches to review", count=pending_duplicates, route="/duplicates")
            )
        if screening_candidates:
            attention_items.append(
                DashboardAttentionItem(label="Candidates waiting for screening", count=screening_candidates, route="/candidates")
            )

        return DashboardStatsResponse(
            total_candidates=total_candidates,
            last_sync_at=integration.last_successful_sync_at,
            current_shortlist_size=current_shortlist_size,
            saved_filter_count=saved_filter_count,
            new_candidates=new_candidates,
            shortlisted_candidates=shortlisted_candidates,
            interview_candidates=interview_candidates,
            pending_duplicates=pending_duplicates,
            last_sync_status=latest_sync.status if latest_sync else None,
            last_sync_new=latest_sync.records_new if latest_sync else 0,
            last_sync_updated=latest_sync.records_updated if latest_sync else 0,
            last_sync_errors=1 if latest_sync and latest_sync.status == "failed" else 0,
            pipeline=[
                DashboardCountItem(label="New", count=new_candidates),
                DashboardCountItem(label="Screening", count=screening_candidates),
                DashboardCountItem(label="Shortlisted", count=shortlisted_candidates),
                DashboardCountItem(label="Interview", count=interview_candidates),
                DashboardCountItem(label="Selected", count=selected_candidates),
            ],
            source_breakdown=self._get_source_breakdown(),
            needs_attention=attention_items,
            resume_enrichment=enrichment,
            activity_summary=activity_summary,
        )

    def get_recent_activity(self, recruiter_id: UUID, limit: int = 5) -> DashboardRecentActivityResponse:
        statement = (
            select(ActivityLog)
            .where(ActivityLog.actor_id == recruiter_id)
            .order_by(desc(ActivityLog.occurred_at), desc(ActivityLog.id))
            .limit(limit)
        )
        items = [
            DashboardActivityItemResponse(
                id=row.id,
                actor_id=row.actor_id,
                action_type=row.action_type,
                description=row.description,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                result=row.result,
                metadata=row.audit_metadata,
                occurred_at=row.occurred_at,
            )
            for row in self.session.scalars(statement).all()
        ]
        return DashboardRecentActivityResponse(items=items)

    def get_analytics(self, recruiter_id: UUID, days: int = 7) -> DashboardAnalyticsResponse:
        start = datetime.now(UTC) - timedelta(days=days - 1)
        growth_rows = self.session.execute(
            select(func.date(Candidate.created_at), func.count(Candidate.id))
            .where(Candidate.created_at >= start)
            .group_by(func.date(Candidate.created_at))
            .order_by(func.date(Candidate.created_at))
        )
        growth = [DashboardSeriesPoint(label=str(label), value=count) for label, count in growth_rows]
        pipeline = [
            DashboardCountItem(label="New", count=self._count_candidates_with_statuses("new", "active")),
            DashboardCountItem(label="Screening", count=self._count_candidates_with_statuses("screening", "open_to_opportunities")),
            DashboardCountItem(label="Interview", count=self._count_candidates_with_statuses("interview", "interview_scheduled")),
            DashboardCountItem(label="Selected", count=self._count_candidates_with_statuses("selected", "hired")),
        ]
        source_label = func.coalesce(Candidate.source, "Unknown").label("source_label")
        source_rows = self.session.execute(
            select(source_label, func.count(Candidate.id))
            .group_by(source_label)
            .order_by(desc(func.count(Candidate.id)))
            .limit(8)
        )
        sources = [DashboardCountItem(label=label or "Unknown", count=count) for label, count in source_rows]
        sync_rows = self.session.execute(
            select(SyncLog.status, func.count(SyncLog.id))
            .where(SyncLog.started_at >= start)
            .group_by(SyncLog.status)
        )
        sync_outcomes = [DashboardCountItem(label=status, count=count) for status, count in sync_rows]
        enrichment_rows = self.session.execute(
            select(CandidateReview.approval_status, func.count(CandidateReview.id))
            .where(CandidateReview.updated_at >= start)
            .group_by(CandidateReview.approval_status)
        )
        enrichment_outcomes = [DashboardCountItem(label=status, count=count) for status, count in enrichment_rows]
        activity_statement = select(ActivityLog.action_type, func.count(ActivityLog.id)).where(ActivityLog.occurred_at >= start)
        if recruiter_id:
            activity_statement = activity_statement.where(ActivityLog.actor_id == recruiter_id)
        activity_rows = self.session.execute(
            activity_statement.group_by(ActivityLog.action_type).order_by(desc(func.count(ActivityLog.id))).limit(10)
        )
        activity_by_action = [DashboardCountItem(label=action, count=count) for action, count in activity_rows]
        return DashboardAnalyticsResponse(
            days=days,
            candidate_growth=growth,
            pipeline=pipeline,
            sources=sources,
            sync_outcomes=sync_outcomes,
            enrichment_outcomes=enrichment_outcomes,
            activity_by_action=activity_by_action,
        )

    def _get_current_shortlist_size(self, recruiter_id: UUID) -> int:
        shortlist_id = self.session.scalar(
            select(Shortlist.id)
            .where(Shortlist.recruiter_id == recruiter_id)
            .order_by(desc(Shortlist.created_at), desc(Shortlist.id))
            .limit(1)
        )
        if shortlist_id is None:
            return 0

        return self.session.scalar(
            select(func.count(ShortlistCandidate.candidate_id)).where(ShortlistCandidate.shortlist_id == shortlist_id)
        ) or 0

    def _count_candidates_with_statuses(self, *statuses: str) -> int:
        return self.session.scalar(
            select(func.count(Candidate.id)).where(func.lower(func.coalesce(Candidate.status, "")).in_(statuses))
        ) or 0

    def _get_source_breakdown(self) -> list[DashboardCountItem]:
        source_label = func.coalesce(Candidate.source, "Unknown").label("source_label")
        statement = (
            select(source_label, func.count(Candidate.id).label("count"))
            .group_by(source_label)
            .order_by(desc("count"), source_label)
            .limit(6)
        )
        return [DashboardCountItem(label=source or "Unknown", count=count) for source, count in self.session.execute(statement)]
