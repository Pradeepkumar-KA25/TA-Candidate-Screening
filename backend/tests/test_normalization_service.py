from __future__ import annotations

from app.models.normalization_rule import NormalizationRule
from app.repositories.normalization_rule_repository import NormalizationRuleRepository
from app.services.normalization_service import NormalizationService


def _build_service(sqlite_session) -> NormalizationService:
    return NormalizationService(repository=NormalizationRuleRepository(sqlite_session))


def _seed_rule(sqlite_session, *, field_type: str, raw_value: str, normalized_value: str) -> None:
    sqlite_session.add(
        NormalizationRule(
            field_type=field_type,
            raw_value=raw_value,
            normalized_value=normalized_value,
        )
    )
    sqlite_session.commit()


def test_normalization_service_applies_location_mapping(sqlite_session) -> None:
    _seed_rule(
        sqlite_session,
        field_type="location",
        raw_value="Bangalore",
        normalized_value="Bengaluru",
    )
    service = _build_service(sqlite_session)

    assert service.normalize_location("Bangalore") == "Bengaluru"


def test_normalization_service_applies_notice_period_mapping(sqlite_session) -> None:
    _seed_rule(
        sqlite_session,
        field_type="notice_period",
        raw_value="1 Month",
        normalized_value="30 Days",
    )
    service = _build_service(sqlite_session)

    assert service.normalize_notice_period("1 Month") == "30 Days"


def test_normalization_service_applies_skill_mapping(sqlite_session) -> None:
    _seed_rule(
        sqlite_session,
        field_type="skill",
        raw_value="JAVA",
        normalized_value="Java",
    )
    service = _build_service(sqlite_session)

    assert service.normalize_skill("JAVA") == "Java"


def test_normalization_service_applies_degree_mapping(sqlite_session) -> None:
    _seed_rule(
        sqlite_session,
        field_type="degree",
        raw_value="B.E. Computer Science",
        normalized_value="Bachelor Degree - Computer Science",
    )
    service = _build_service(sqlite_session)

    assert service.normalize_degree("B.E. Computer Science") == "Bachelor Degree - Computer Science"


def test_normalization_service_preserves_unmapped_values(sqlite_session) -> None:
    service = _build_service(sqlite_session)

    assert service.normalize_location("Coimbatore") == "Coimbatore"
    assert service.normalize_notice_period("75 Days") == "75 Days"
    assert service.normalize_skill("Go") == "Go"
    assert service.normalize_degree("BCA") == "BCA"
