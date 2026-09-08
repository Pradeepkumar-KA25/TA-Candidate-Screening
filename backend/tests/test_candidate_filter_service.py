from __future__ import annotations

from uuid import uuid4

from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping

from app.services.candidate_filter_service import CandidateFilterCriteria, CandidateFilterQueryComposer


def test_compose_returns_empty_when_no_filters() -> None:
    criteria = CandidateFilterCriteria()

    result = CandidateFilterQueryComposer.compose(criteria)

    assert result == []


def test_compose_builds_single_and_clause_with_all_filters() -> None:
    criteria = CandidateFilterCriteria(
        skills=["Java", "Spring Boot"],
        experience_min=4,
        experience_max=8,
        location="Bengaluru",
        preferred_location="Pune",
        notice_period_max=30,
        status="active",
    )

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BooleanClauseList)

    expressions = list(result[0].clauses)
    assert len(expressions) == 8
    assert all(isinstance(item, BinaryExpression) for item in expressions)


def test_compose_builds_single_and_clause_with_advanced_filters() -> None:
    criteria = CandidateFilterCriteria(
        degree="Bachelor",
        certification="AWS",
        resume_updated_since=30,
        source="zoho_recruit",
        relevant_experience=4,
        current_ctc=8,
        expected_ctc=12,
        previous_company="Infosys",
        employment_status="employed",
    )

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BooleanClauseList)

    expressions = list(result[0].clauses)
    assert len(expressions) == 9
    assert all(isinstance(item, BinaryExpression) for item in expressions)


def test_compose_uses_only_recruiter_skills_when_no_jd_selected() -> None:
    criteria = CandidateFilterCriteria(skills=["Python", "FastAPI"])

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    expressions = list(result[0].clauses)
    assert len(expressions) == 2
    assert all(isinstance(item, BinaryExpression) for item in expressions)


def test_compose_combines_jd_required_and_recruiter_skills_without_duplicates() -> None:
    criteria = CandidateFilterCriteria(
        jd_id=uuid4(),
        jd_required_skills=["Java", "Microservices"],
        skills=["Java", "Spring Boot"],
    )

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    expressions = list(result[0].clauses)
    assert len(expressions) == 3
    assert isinstance(expressions[0], Grouping)
    assert all(isinstance(item, BinaryExpression) for item in expressions[1:])


def test_compose_location_with_single_value() -> None:
    criteria = CandidateFilterCriteria(location="Bengaluru")

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BinaryExpression)


def test_compose_location_with_comma_separated_values_uses_or_logic() -> None:
    criteria = CandidateFilterCriteria(location="Bengaluru, Chennai, Pune")

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BooleanClauseList)
    location_matchers = list(result[0].clauses)
    assert len(location_matchers) == 3


def test_compose_preferred_location_with_comma_separated_values_uses_or_logic() -> None:
    criteria = CandidateFilterCriteria(preferred_location="Bengaluru, Hyderabad, Chennai")

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BooleanClauseList)
    location_matchers = list(result[0].clauses)
    assert len(location_matchers) == 3


def test_compose_location_with_whitespace_handling() -> None:
    criteria = CandidateFilterCriteria(location="  Bengaluru  ,  Chennai  ,  Pune  ")

    result = CandidateFilterQueryComposer.compose(criteria)

    assert len(result) == 1
    assert isinstance(result[0], BooleanClauseList)
    location_matchers = list(result[0].clauses)
    assert len(location_matchers) == 3
