from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from uuid import UUID

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.shortlist_repository import ShortlistRepository
from app.services.candidate_filter_service import CandidateFilterCriteria, CandidateFilterQueryComposer
from app.services.field_normalizer import CandidateFieldNormalizer
from app.schemas.candidates import (
    CandidateDetailResponse,
    CandidateExtendedFieldsResponse,
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


from app.repositories.shortlist_repository import ShortlistRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository


@dataclass(slots=True)
class CandidateService:
    repository: CandidateRepository
    job_description_repository: JobDescriptionRepository
    shortlist_repository: ShortlistRepository | None = None
    duplicate_review_repository: DuplicateReviewRepository | None = None
    resume_fetch_service: "ResumeFetchService | None" = None
    duplicate_review_repository: DuplicateReviewRepository | None = None

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
        
        # Build candidate fields dict to pass to normalizer
        candidate_fields = {
            'First_Name': candidate.full_name.split()[0] if candidate.full_name else None,
            'Last_Name': ' '.join(candidate.full_name.split()[1:]) if candidate.full_name and len(candidate.full_name.split()) > 1 else '',
            'Email': candidate.email,
            'Phone': candidate.phone,
            'Total_Experience_Years': candidate.total_experience_years,
            'Current_Company': candidate.current_company,
            'Current_Location': candidate.current_location,
            'Skills': candidate.skills,
            'Degree': candidate.degree,
            'Status': candidate.status,
            'Source': candidate.source,
        }
        # Filter out None values
        candidate_fields = {k: v for k, v in candidate_fields.items() if v is not None}
        
        extended_fields = self._extract_extended_fields(candidate.raw_payload or {}, candidate_fields)

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
            resume_url=candidate.resume_url,
            resume_file_name=candidate.resume_file_name,
            resume_last_fetched_at=candidate.resume_last_fetched_at,
            normalized_data=normalized_data,
            match_context=self._build_match_context(candidate.match_metadata),
            extended_fields=extended_fields,
        )

    def delete_candidate(self, candidate_id: UUID) -> None:
        """Delete a candidate by ID."""
        candidate = self.repository.get_by_id(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError()
        
        # Delete resume folder if service available
        if self.resume_fetch_service:
            try:
                self.resume_fetch_service.delete_candidate_resumes(str(candidate_id))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to delete resume for candidate {candidate_id}: {str(e)}")
                # Continue with candidate deletion even if resume deletion fails
        
        self.repository.delete(candidate_id)

    def delete_candidates_batch(self, candidate_ids: list[UUID]) -> int:
        """Delete multiple candidates by ID. Returns the number of deleted candidates."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting batch delete for {len(candidate_ids)} candidates: {candidate_ids}")
        deleted_count = 0
        
        for candidate_id in candidate_ids:
            try:
                logger.debug(f"Attempting to find candidate {candidate_id}")
                candidate = self.repository.get_by_id(candidate_id)
                
                if candidate is not None:
                    logger.debug(f"Found candidate {candidate_id} (name={candidate.full_name})")
                    
                    # Delete resume folder if service available
                    if self.resume_fetch_service:
                        try:
                            self.resume_fetch_service.delete_candidate_resumes(str(candidate_id))
                            logger.debug(f"Deleted resume folder for candidate {candidate_id}")
                        except Exception as e:
                            logger.warning(f"Failed to delete resume for candidate {candidate_id}: {str(e)}")
                    
                    # Delete dependent records first to avoid foreign key constraint violations
                    if self.shortlist_repository:
                        try:
                            removed_count = self.shortlist_repository.remove_candidate_from_all_shortlists(candidate_id)
                            logger.debug(f"Removed candidate {candidate_id} from {removed_count} shortlist(s)")
                        except Exception as e:
                            logger.warning(f"Failed to remove shortlist references for {candidate_id}: {str(e)}")
                    
                    if self.duplicate_review_repository:
                        try:
                            review_count = self.duplicate_review_repository.remove_candidate_reviews(candidate_id)
                            logger.debug(f"Removed {review_count} duplicate review(s) involving {candidate_id}")
                        except Exception as e:
                            logger.warning(f"Failed to remove duplicate reviews for {candidate_id}: {str(e)}")
                    
                    # Now delete the candidate
                    logger.debug(f"Deleting candidate {candidate_id}...")
                    self.repository.delete(candidate_id)
                    deleted_count += 1
                    logger.info(f"Successfully deleted candidate {candidate_id}")
                else:
                    logger.warning(f"Candidate {candidate_id} not found in database")
            except Exception as e:
                logger.error(f"Error deleting candidate {candidate_id}: {str(e)}", exc_info=True)
        
        logger.info(f"Batch delete completed. Successfully deleted {deleted_count} out of {len(candidate_ids)} candidates")
        return deleted_count

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

    @staticmethod
    def _extract_extended_fields(raw_payload: dict, candidate_fields: dict = None) -> CandidateExtendedFieldsResponse:
        """
        Extract and organize extended Zoho fields into logical business categories.
        Uses CandidateFieldNormalizer to ensure consistent structure.
        
        Args:
            raw_payload: Raw Zoho API response fields
            candidate_fields: Regular candidate model fields to include (First_Name, Email, etc.)
        """
        # Normalize the raw payload into organized categories
        normalized = CandidateFieldNormalizer.normalize(raw_payload, candidate_fields)
        
        # Convert normalized dict to CandidateExtendedFieldsResponse
        # The response object stores the entire normalized dict
        return CandidateExtendedFieldsResponse(
            personal_contact=normalized.get('Personal Information', {}),
            employment=normalized.get('Employment Details', {}),
            interview_process=normalized.get('Interview Process', {}),
            candidate_lifecycle=normalized.get('Candidate Lifecycle', {}),
            salary_benefits=normalized.get('Salary & Benefits', {}),
            referral_vendor_sourcing=normalized.get('Referral & Sourcing', {}),
            contact_address=normalized.get('Contact & Address', {}),
            professional_details=normalized.get('Professional Details', {}),
            education_qualifications=normalized.get('Education & Qualifications', {}),
            application_recruitment=normalized.get('Application & Recruitment', {}),
            system_metadata=normalized.get('System & Metadata', {}),
            other_fields=normalized.get('Other Fields', {}),
        )
