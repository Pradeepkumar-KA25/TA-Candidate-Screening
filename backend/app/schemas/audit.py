from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogItemResponse(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    actor_name: str | None = None
    action_type: str
    description: str
    entity_type: str | None = None
    entity_id: str | None = None
    result: str
    metadata: dict | None = None
    occurred_at: datetime


class AuditLogResponse(BaseModel):
    items: list[AuditLogItemResponse]
    total: int
    page: int
    page_size: int