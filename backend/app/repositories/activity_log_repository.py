from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from datetime import datetime

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


class ActivityLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        actor_id: UUID | None,
        action_type: str,
        description: str,
        entity_type: str | None = None,
        entity_id: str | UUID | None = None,
        result: str = "success",
        metadata: dict | None = None,
    ) -> ActivityLog:
        entry = ActivityLog(
            actor_id=actor_id,
            action_type=action_type,
            description=description,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            result=result,
            audit_metadata=metadata,
            occurred_at=datetime.now(UTC),
        )
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list_audit_entries(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        action_type: str | None = None,
        actor_id: UUID | None = None,
        actor_query: str | None = None,
        entity_type: str | None = None,
        result: str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
    ) -> tuple[list[tuple[ActivityLog, str | None]], int]:
        filters = []
        if action_type:
            filters.append(ActivityLog.action_type == action_type)
        if actor_id:
            filters.append(ActivityLog.actor_id == actor_id)
        if actor_query:
            actor_pattern = f"%{actor_query.strip().lower()}%"
            filters.append(or_(func.lower(User.full_name).like(actor_pattern), func.lower(User.email).like(actor_pattern)))
        if entity_type:
            filters.append(ActivityLog.entity_type == entity_type)
        if result:
            filters.append(ActivityLog.result == result)
        if occurred_from:
            filters.append(ActivityLog.occurred_at >= occurred_from)
        if occurred_to:
            filters.append(ActivityLog.occurred_at < occurred_to)

        count_statement = select(func.count(ActivityLog.id)).outerjoin(User, User.id == ActivityLog.actor_id)
        if filters:
            count_statement = count_statement.where(*filters)
        total = self.session.scalar(count_statement) or 0

        statement = (
            select(ActivityLog, User.full_name)
            .outerjoin(User, User.id == ActivityLog.actor_id)
            .order_by(desc(ActivityLog.occurred_at), desc(ActivityLog.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if filters:
            statement = statement.where(*filters)
        return list(self.session.execute(statement).all()), total
