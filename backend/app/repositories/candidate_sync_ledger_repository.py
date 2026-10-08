from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_sync_ledger import CandidateSyncLedger


class CandidateSyncLedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_zoho_record_id(self, zoho_record_id: str) -> CandidateSyncLedger | None:
        statement = select(CandidateSyncLedger).where(CandidateSyncLedger.zoho_record_id == zoho_record_id)
        return self.session.scalar(statement)

    def mark_processing(
        self,
        *,
        zoho_record_id: str,
        payload_hash: str,
    ) -> CandidateSyncLedger:
        entry = self.get_by_zoho_record_id(zoho_record_id)
        if entry is None:
            entry = CandidateSyncLedger(
                zoho_record_id=zoho_record_id,
                payload_hash=payload_hash,
                status="processing",
                attempt_count=0,
            )

        entry.status = "processing"
        entry.attempt_count += 1
        entry.last_error = None
        entry.processing_started_at = datetime.now(UTC)
        self.session.add(entry)
        self.session.flush()
        return entry

    def record_completed(
        self,
        *,
        zoho_record_id: str,
        modified_time: datetime | None,
        payload_hash: str,
    ) -> CandidateSyncLedger:
        entry = self.get_by_zoho_record_id(zoho_record_id)
        if entry is None:
            entry = CandidateSyncLedger(
                zoho_record_id=zoho_record_id,
                payload_hash=payload_hash,
                status="processing",
                attempt_count=0,
            )
        self.mark_completed(entry, modified_time=modified_time, payload_hash=payload_hash)
        return entry

    def mark_completed(
        self,
        entry: CandidateSyncLedger,
        *,
        modified_time: datetime | None,
        payload_hash: str,
    ) -> None:
        entry.status = "completed"
        entry.last_processed_modified_time = modified_time
        entry.payload_hash = payload_hash
        entry.processing_started_at = None
        entry.last_processed_at = datetime.now(UTC)
        entry.last_error = None
        self.session.add(entry)
        self.session.flush()
