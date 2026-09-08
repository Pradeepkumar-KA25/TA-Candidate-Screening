from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    path: str
    timestamp: datetime
    details: list[dict[str, str]] | None = None
