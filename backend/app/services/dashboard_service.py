from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.duplicate_review import DuplicateReview
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
                occurred_at=row.occurred_at,
            )
            for row in self.session.scalars(statement).all()
        ]
        return DashboardRecentActivityResponse(items=items)

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
        source_label = func.coalesce(Candidate.source, "Unknown")
        statement = (
            select(source_label, func.count(Candidate.id).label("count"))
            .group_by(source_label)
            .order_by(desc("count"), source_label)
            .limit(6)
        )
        return [DashboardCountItem(label=source or "Unknown", count=count) for source, count in self.session.execute(statement)]
