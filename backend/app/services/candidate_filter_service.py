from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import String, and_, cast, func, or_
from sqlalchemy.sql.elements import ColumnElement

from app.models.candidate import Candidate


@dataclass(slots=True)
class CandidateFilterCriteria:
    jd_id: UUID | None = None
    jd_required_skills: list[str] | None = None
    skills: list[str] | None = None
    experience_min: float | None = None
    experience_max: float | None = None
    location: str | None = None
    preferred_location: str | None = None
    notice_period_max: int | None = None
    status: str | None = None
    degree: str | None = None
    certification: str | None = None
    resume_updated_since: int | None = None
    source: str | None = None
    relevant_experience: float | None = None
    current_ctc: float | None = None
    expected_ctc: float | None = None
    previous_company: str | None = None
    employment_status: str | None = None


class CandidateFilterQueryComposer:
    @staticmethod
    def _normalized_column(value):
        return func.lower(func.trim(func.coalesce(value, "")))

    @staticmethod
    def compose(criteria: CandidateFilterCriteria) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []

        jd_skill_terms = CandidateFilterQueryComposer._normalized_terms(criteria.jd_required_skills)
        if criteria.jd_id and jd_skill_terms:
            # JD-driven filtering should surface partially relevant candidates when exact matches are scarce.
            jd_skill_matchers = [
                func.lower(cast(Candidate.skills, String)).like(f"%{term}%")
                for term in jd_skill_terms
            ]
            filters.append(jd_skill_matchers[0] if len(jd_skill_matchers) == 1 else or_(*jd_skill_matchers))

        user_skill_terms = CandidateFilterQueryComposer._normalized_terms(criteria.skills)
        for term in user_skill_terms:
            filters.append(func.lower(cast(Candidate.skills, String)).like(f"%{term}%"))

        if criteria.experience_min is not None:
            filters.append(Candidate.total_experience_years >= criteria.experience_min)

        if criteria.experience_max is not None:
            filters.append(Candidate.total_experience_years <= criteria.experience_max)

        if criteria.location:
            # Split by comma and match any location (OR logic)
            location_terms = [term.strip().lower() for term in criteria.location.split(',') if term.strip()]
            if location_terms:
                location_matchers = [
                    CandidateFilterQueryComposer._normalized_column(Candidate.current_location).like(f"%{term}%")
                    for term in location_terms
                ]
                filters.append(
                    location_matchers[0] if len(location_matchers) == 1 else or_(*location_matchers)
                )

        if criteria.preferred_location:
            # Split by comma and match any location (OR logic)
            preferred_terms = [term.strip().lower() for term in criteria.preferred_location.split(',') if term.strip()]
            if preferred_terms:
                preferred_matchers = [
                    CandidateFilterQueryComposer._normalized_column(Candidate.preferred_location).like(f"%{term}%")
                    for term in preferred_terms
                ]
                filters.append(
                    preferred_matchers[0] if len(preferred_matchers) == 1 else or_(*preferred_matchers)
                )

        if criteria.notice_period_max is not None:
            filters.append(Candidate.notice_period_days <= criteria.notice_period_max)

        if criteria.status:
            status_terms = CandidateFilterQueryComposer._normalized_terms(criteria.status.split(","))
            if status_terms:
                filters.append(CandidateFilterQueryComposer._normalized_column(Candidate.status).in_(status_terms))

        if criteria.degree:
            filters.append(
                CandidateFilterQueryComposer._normalized_column(Candidate.normalized_degree).like(
                    f"%{criteria.degree.strip().lower()}%"
                )
            )

        if criteria.certification:
            filters.append(func.lower(cast(Candidate.raw_payload, String)).like(f"%{criteria.certification.strip().lower()}%"))

        if criteria.resume_updated_since is not None:
            threshold = datetime.now(UTC) - timedelta(days=int(criteria.resume_updated_since))
            filters.append(Candidate.updated_at >= threshold)

        if criteria.source:
            filters.append(CandidateFilterQueryComposer._normalized_column(Candidate.source) == criteria.source.strip().lower())

        if criteria.relevant_experience is not None:
            filters.append(Candidate.relevant_experience_years >= criteria.relevant_experience)

        if criteria.current_ctc is not None:
            filters.append(Candidate.current_ctc >= criteria.current_ctc)

        if criteria.expected_ctc is not None:
            filters.append(Candidate.expected_ctc >= criteria.expected_ctc)

        if criteria.previous_company:
            filters.append(
                func.lower(cast(Candidate.raw_payload, String)).like(f"%{criteria.previous_company.strip().lower()}%")
            )

        if criteria.employment_status:
            filters.append(
                func.lower(cast(Candidate.raw_payload, String)).like(f"%{criteria.employment_status.strip().lower()}%")
            )

        if not filters:
            return []

        return [and_(*filters)]

    @staticmethod
    def _normalized_terms(values: list[str] | None) -> list[str]:
        if not values:
            return []

        terms: list[str] = []
        seen: set[str] = set()
        for item in values:
            term = str(item).strip().lower()
            if not term or term in seen:
                continue
            seen.add(term)
            terms.append(term)
        return terms
