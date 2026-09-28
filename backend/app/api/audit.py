from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_activity_log_repository, require_roles
from app.models.user import User
from app.repositories.activity_log_repository import ActivityLogRepository
from app.schemas.audit import AuditLogItemResponse, AuditLogResponse


audit_router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@audit_router.get("", response_model=AuditLogResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    action_type: str | None = Query(None, min_length=1, max_length=64),
    actor_id: UUID | None = None,
    actor: str | None = Query(None, min_length=1, max_length=255),
    entity_type: str | None = Query(None, min_length=1, max_length=64),
    result: str | None = Query(None, min_length=1, max_length=32),
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    _: User = Depends(require_roles("Recruiter", "Admin")),
    repository: ActivityLogRepository = Depends(get_activity_log_repository),
) -> AuditLogResponse:
    entries, total = repository.list_audit_entries(
        page=page,
        page_size=page_size,
        action_type=action_type,
        actor_id=actor_id,
        actor_query=actor,
        entity_type=entity_type,
        result=result,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
    return AuditLogResponse(
        items=[
            AuditLogItemResponse(
                id=entry.id,
                actor_id=entry.actor_id,
                actor_name=actor_name,
                action_type=entry.action_type,
                description=entry.description,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                result=entry.result,
                metadata=entry.audit_metadata,
                occurred_at=entry.occurred_at,
            )
            for entry, actor_name in entries
        ],
        total=total,
        page=page,
        page_size=page_size,
    )