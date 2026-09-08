from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog


class SyncLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def has_running_sync(self) -> bool:
        statement = select(SyncLog.id).where(SyncLog.status == "running").limit(1)
        return self.session.scalar(statement) is not None

    def list_stale_running_syncs(self, *, started_before: datetime) -> list[SyncLog]:
        statement = (
            select(SyncLog)
            .where(SyncLog.status == "running")
            .where(SyncLog.started_at < started_before)
            .order_by(desc(SyncLog.started_at))
        )
        return list(self.session.scalars(statement).all())

    def mark_stale_running_syncs_failed(self, *, started_before: datetime, reason: str) -> int:
        stale_logs = self.list_stale_running_syncs(started_before=started_before)
        updated = 0
        for log in stale_logs:
            log.status = "failed"
            log.completed_at = datetime.now(UTC)
            log.error_message = reason
            self.session.add(log)
            updated += 1

        if updated:
            self.session.commit()

        return updated

    def create_running(self, triggered_by: UUID) -> SyncLog:
        log = SyncLog(
            triggered_by=triggered_by,
            status="running",
            started_at=datetime.now(UTC),
            records_fetched=0,
            records_new=0,
            records_updated=0,
            normalized_records=0,
            normalization_examples=[],
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_by_id(self, sync_id: UUID) -> SyncLog | None:
        statement = select(SyncLog).where(SyncLog.id == sync_id)
        return self.session.scalar(statement)

    def get_latest_for_user(self, user_id: UUID) -> SyncLog | None:
        statement = (
            select(SyncLog)
            .where(SyncLog.triggered_by == user_id)
            .order_by(desc(SyncLog.started_at))
            .limit(1)
        )
        return self.session.scalar(statement)

    def list_for_user(self, user_id: UUID, limit: int) -> list[SyncLog]:
        statement = (
            select(SyncLog)
            .where(SyncLog.triggered_by == user_id)
            .order_by(desc(SyncLog.started_at), desc(SyncLog.id))
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def mark_running_progress(
        self,
        *,
        sync_id: UUID,
        records_fetched: int,
        records_new: int,
        records_updated: int,
        normalized_records: int,
        normalization_examples: list[dict],
    ) -> SyncLog:
        log = self.get_by_id(sync_id)
        if log is None:
            raise ValueError("Sync log not found")

        log.records_fetched = records_fetched
        log.records_new = records_new
        log.records_updated = records_updated
        log.normalized_records = normalized_records
        log.normalization_examples = normalization_examples

        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def mark_completed(
        self,
        *,
        sync_id: UUID,
        records_fetched: int,
        records_new: int,
        records_updated: int,
        normalized_records: int,
        normalization_examples: list[dict],
    ) -> SyncLog:
        log = self.get_by_id(sync_id)
        if log is None:
            raise ValueError("Sync log not found")

        log.status = "completed"
        log.completed_at = datetime.now(UTC)
        log.records_fetched = records_fetched
        log.records_new = records_new
        log.records_updated = records_updated
        log.normalized_records = normalized_records
        log.normalization_examples = normalization_examples
        log.error_message = None

        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def mark_failed(self, *, sync_id: UUID, error_message: str) -> SyncLog:
        log = self.get_by_id(sync_id)
        if log is None:
            raise ValueError("Sync log not found")

        log.status = "failed"
        log.completed_at = datetime.now(UTC)
        log.error_message = error_message

        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def set_outcome_counts(self, *, sync_id: UUID, records_failed: int, duplicate_matches: int) -> SyncLog:
        log = self.get_by_id(sync_id)
        if log is None:
            raise ValueError("Sync log not found")

        log.records_failed = records_failed
        log.duplicate_matches = duplicate_matches
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
