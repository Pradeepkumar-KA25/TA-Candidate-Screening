from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from uuid import UUID

from app.repositories.job_description_repository import JobDescriptionRepository
from app.services.candidate_filter_service import CandidateFilterCriteria, CandidateFilterQueryComposer
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidates import (
    CandidateDetailResponse,
    CandidateListItemResponse,
    CandidateListResponse,
    CandidateMatchContextResponse,
    CandidateNormalizedPairResponse,
)


class CandidateError(Exception):
    status_code = 400
    code = "CANDIDATE_ERROR"
    detail = "Candidate request could not be processed"


class CandidateNotFoundError(CandidateError):
    status_code = 404
    code = "CANDIDATE_NOT_FOUND"
    detail = "Candidate was not found"


class CandidateFilterValidationError(CandidateError):
    status_code = 422
    code = "INVALID_FILTER_CRITERIA"
    detail = "Experience minimum must be less than or equal to experience maximum"


@dataclass(slots=True)
class CandidateService:
    repository: CandidateRepository
    job_description_repository: JobDescriptionRepository

    def list_candidates(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None,
        sort_by: str,
        sort_order: str,
        jd_id: UUID | None = None,
        skills: str | None = None,
        experience_min: float | None = None,
        experience_max: float | None = None,
        location: str | None = None,
        preferred_location: str | None = None,
        notice_period_max: int | None = None,
        status: str | None = None,
        degree: str | None = None,
        certification: str | None = None,
        resume_updated_since: int | None = None,
        source: str | None = None,
        relevant_experience: float | None = None,
        current_ctc: float | None = None,
        expected_ctc: float | None = None,
        previous_company: str | None = None,
        employment_status: str | None = None,
    ) -> CandidateListResponse:
        if experience_min is not None and experience_max is not None and experience_min > experience_max:
            raise CandidateFilterValidationError()

        parsed_skills = [item.strip() for item in skills.split(",")] if skills else []
        jd_required_skills: list[str] = []
        if jd_id is not None:
            job_description = self.job_description_repository.get_by_id(jd_id)
            if job_description and isinstance(job_description.required_skills, list):
                jd_required_skills = [str(item).strip() for item in job_description.required_skills if str(item).strip()]

        criteria = CandidateFilterCriteria(
            jd_id=jd_id,
            jd_required_skills=jd_required_skills,
            skills=[item for item in parsed_skills if item],
            experience_min=experience_min,
            experience_max=experience_max,
            location=location.strip() if location else None,
            preferred_location=preferred_location.strip() if preferred_location else None,
            notice_period_max=notice_period_max,
            status=status.strip() if status else None,
            degree=degree.strip() if degree else None,
            certification=certification.strip() if certification else None,
            resume_updated_since=resume_updated_since,
            source=source.strip() if source else None,
            relevant_experience=relevant_experience,
            current_ctc=current_ctc,
            expected_ctc=expected_ctc,
            previous_company=previous_company.strip() if previous_company else None,
            employment_status=employment_status.strip() if employment_status else None,
        )
        filter_clauses = CandidateFilterQueryComposer.compose(criteria)

        candidates, total_items = self.repository.list_candidates(
            page=page,
            page_size=page_size,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            filter_clauses=filter_clauses,
        )
        total_pages = max(1, ceil(total_items / page_size))

        return CandidateListResponse(
            items=[self._to_item(candidate) for candidate in candidates],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            q=q.strip() if q and q.strip() else None,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_candidate_details(self, candidate_id: UUID) -> CandidateDetailResponse:
        candidate = self.repository.get_by_id(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError()

        normalized_data = self._extract_normalized_data(candidate.raw_payload or {}, candidate)

        return CandidateDetailResponse(
            id=candidate.id,
            zoho_candidate_id=candidate.zoho_candidate_id,
            full_name=candidate.full_name,
            email=candidate.email,
            phone=candidate.phone,
            total_experience_years=candidate.total_experience_years,
            relevant_experience_years=candidate.relevant_experience_years,
            current_company=candidate.current_company,
            current_location=candidate.current_location,
            preferred_location=candidate.preferred_location,
            notice_period_days=candidate.notice_period_days,
            skills=candidate.skills,
            degree=candidate.degree,
            normalized_degree=candidate.normalized_degree,
            current_ctc=candidate.current_ctc,
            expected_ctc=candidate.expected_ctc,
            status=candidate.status,
            source=candidate.source,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            normalized_data=normalized_data,
            match_context=self._build_match_context(candidate.match_metadata),
        )

    @staticmethod
    def _to_item(candidate) -> CandidateListItemResponse:
        match_percentage = None
        if isinstance(candidate.match_metadata, dict):
            match_value = candidate.match_metadata.get("match_percentage")
            if isinstance(match_value, (int, float)):
                match_percentage = float(match_value)

        return CandidateListItemResponse(
            id=candidate.id,
            zoho_candidate_id=candidate.zoho_candidate_id,
            full_name=candidate.full_name,
            skills=candidate.skills,
            total_experience_years=candidate.total_experience_years,
            current_location=candidate.current_location,
            current_company=candidate.current_company,
            notice_period_days=candidate.notice_period_days,
            status=candidate.status,
            match_percentage=match_percentage,
            updated_at=candidate.updated_at,
        )

    @staticmethod
    def _build_match_context(match_metadata: dict | None) -> CandidateMatchContextResponse:
        metadata = match_metadata if isinstance(match_metadata, dict) else None

        def read_float(value) -> float | None:
            if isinstance(value, (int, float)):
                return float(value)
            return None

        matched_criteria: list[str] | None = None
        if isinstance(metadata, dict):
            raw_criteria = metadata.get("matched_criteria")
            if isinstance(raw_criteria, list):
                matched_criteria = [str(item).strip() for item in raw_criteria if str(item).strip()]

        jd_id = str(metadata.get("jd_id")).strip() if isinstance(metadata, dict) and metadata.get("jd_id") else None
        jd_title = (
            str(metadata.get("jd_title")).strip() if isinstance(metadata, dict) and metadata.get("jd_title") else None
        )

        return CandidateMatchContextResponse(
            jd_id=jd_id,
            jd_title=jd_title,
            match_percentage=read_float(metadata.get("match_percentage")) if metadata else None,
            match_score=read_float(metadata.get("match_score")) if metadata else None,
            matched_criteria=matched_criteria,
            metadata=metadata,
        )

    @staticmethod
    def _extract_normalized_data(raw_payload: dict, candidate) -> list[CandidateNormalizedPairResponse]:
        pairs: list[CandidateNormalizedPairResponse] = []

        def add_pair(field: str, raw_value: str | None, normalized_value: str | None) -> None:
            if raw_value is None or normalized_value is None:
                return
            raw_text = raw_value.strip()
            normalized_text = normalized_value.strip()
            if not raw_text or not normalized_text or raw_text == normalized_text:
                return
            pairs.append(
                CandidateNormalizedPairResponse(
                    field=field,
                    raw_value=raw_text,
                    normalized_value=normalized_text,
                )
            )

        add_pair(
            "current_location",
            CandidateService._extract_first_from_keys(
                raw_payload,
                "Current_Location",
                "Current_Work_Location",
                "Current_Location_of_Candidate_KANINI_Work_Locati",
            )
            or CandidateService._compose_location(raw_payload),
            candidate.current_location,
        )
        add_pair(
            "preferred_location",
            CandidateService._extract_first_from_keys(raw_payload, "Preferred_Location", "Preferred_Work_Location"),
            candidate.preferred_location,
        )
        add_pair(
            "degree",
            CandidateService._extract_first_from_keys(raw_payload, "Highest_Qualification", "Highest_Qualification_Held"),
            candidate.normalized_degree,
        )
        add_pair(
            "notice_period",
            CandidateService._extract_first(raw_payload.get("Notice_Period")),
            CandidateService._format_notice_period(candidate.notice_period_days),
        )

        raw_skills = CandidateService._extract_skills(raw_payload)
        normalized_skills = candidate.skills if isinstance(candidate.skills, list) else []
        for index, raw_skill in enumerate(raw_skills):
            if index >= len(normalized_skills):
                break
            add_pair("skill", raw_skill, str(normalized_skills[index]))

        return pairs

    @staticmethod
    def _extract_first(value) -> str | None:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, list) and value:
            text = str(value[0]).strip()
            return text or None
        return None

    @staticmethod
    def _extract_skills(raw_payload: dict) -> list[str]:
        skills_raw = raw_payload.get("Skill_Set") or raw_payload.get("Skills")
        if isinstance(skills_raw, str):
            return [item.strip() for item in skills_raw.split(",") if item.strip()]
        if isinstance(skills_raw, list):
            return [str(item).strip() for item in skills_raw if str(item).strip()]
        return []

    @classmethod
    def _extract_first_from_keys(cls, raw_payload: dict, *keys: str) -> str | None:
        for key in keys:
            value = cls._extract_first(raw_payload.get(key))
            if value is not None:
                return value
        return None

    @classmethod
    def _compose_location(cls, raw_payload: dict) -> str | None:
        parts = [
            cls._extract_first(raw_payload.get("City")),
            cls._extract_first(raw_payload.get("State")),
            cls._extract_first(raw_payload.get("Country")),
        ]
        location = ", ".join(part for part in parts if part)
        return location or None

    @staticmethod
    def _format_notice_period(value: int | None) -> str | None:
        if value is None:
            return None
        return f"{value} Days"
