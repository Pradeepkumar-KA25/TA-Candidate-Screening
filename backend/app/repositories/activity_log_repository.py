from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


class ActivityLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        actor_id: UUID | None,
        action_type: str,
        description: str,
    ) -> ActivityLog:
        entry = ActivityLog(
            actor_id=actor_id,
            action_type=action_type,
            description=description,
            occurred_at=datetime.now(UTC),
        )
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry
