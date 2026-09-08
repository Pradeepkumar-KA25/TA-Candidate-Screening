from __future__ import annotations

from dataclasses import dataclass

from app.repositories.normalization_rule_repository import NormalizationRuleRepository


@dataclass(slots=True)
class NormalizationService:
    repository: NormalizationRuleRepository

    def normalize_location(self, value: str | None) -> str | None:
        return self._apply_rule(field_type="location", value=value)

    def normalize_skill(self, value: str) -> str:
        normalized = self._apply_rule(field_type="skill", value=value)
        return normalized if normalized is not None else value.strip()

    def normalize_degree(self, value: str | None) -> str | None:
        return self._apply_rule(field_type="degree", value=value)

    def normalize_notice_period(self, value: str | None) -> str | None:
        return self._apply_rule(field_type="notice_period", value=value)

    def _apply_rule(self, *, field_type: str, value: str | None) -> str | None:
        if value is None:
            return None

        trimmed = value.strip()
        if not trimmed:
            return None

        mapped = self.repository.find_normalized_value(field_type=field_type, raw_value=trimmed)
        return mapped if mapped is not None else trimmed
