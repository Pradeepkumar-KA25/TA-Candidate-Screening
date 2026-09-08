from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.normalization_rule import NormalizationRule


class NormalizationRuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_normalized_value(self, *, field_type: str, raw_value: str) -> str | None:
        normalized_field = field_type.strip().lower()
        normalized_raw = raw_value.strip().lower()

        statement = select(NormalizationRule.normalized_value).where(
            func.lower(NormalizationRule.field_type) == normalized_field,
            func.lower(NormalizationRule.raw_value) == normalized_raw,
        )
        return self.session.scalar(statement)
