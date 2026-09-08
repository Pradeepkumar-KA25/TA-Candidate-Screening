from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.ranking_criterion import RankingCriterion
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
from app.schemas.ranking import RankedCandidateResponse, RankingResponse, RankingScoreBreakdownResponse
from app.services.candidate_filter_service import CandidateFilterCriteria, CandidateFilterQueryComposer


class RankingError(Exception):
    status_code = 400
    code = "RANKING_ERROR"
    detail = "Ranking request could not be processed"


class RankingJDNotFoundError(RankingError):
    status_code = 404
    code = "JD_NOT_FOUND"

    def __init__(self, jd_id: UUID) -> None:
        self.detail = f"Job description with id '{jd_id}' not found"


class RankingNoCriteriaError(RankingError):
    status_code = 400
    code = "NO_RANKING_CRITERIA"

    def __init__(self, jd_id: UUID) -> None:
        self.detail = f"No ranking criteria defined for job description '{jd_id}'"


class RankingCandidateNotFoundError(RankingError):
    status_code = 404
    code = "CANDIDATE_NOT_FOUND"

    def __init__(self, candidate_id: UUID) -> None:
        self.detail = f"Candidate with id '{candidate_id}' not found"


@dataclass(slots=True)
class RankingService:
    session: Session
    job_description_repository: JobDescriptionRepository
    ranking_criteria_repository: RankingCriteriaRepository
    candidate_repository: CandidateRepository

    def rank_candidates(
        self,
        jd_id: UUID,
        filter_criteria: CandidateFilterCriteria | None = None,
    ) -> RankingResponse:
        """Rank candidates for a job description based on weighted criteria.
        
        Args:
            jd_id: Job description ID
            filter_criteria: Optional filtering criteria to apply to candidates
            
        Returns:
            RankingResponse with ranked candidates sorted by score descending
            
        Raises:
            RankingJDNotFoundError: If JD doesn't exist
            RankingNoCriteriaError: If no criteria are defined for the JD
        """
        # Verify JD exists
        jd = self.job_description_repository.get_by_id(jd_id)
        if jd is None:
            raise RankingJDNotFoundError(jd_id)

        # Get ranking criteria for the JD
        criteria_list = self.ranking_criteria_repository.get_by_jd_id(jd_id)
        if not criteria_list:
            raise RankingNoCriteriaError(jd_id)

        # Build criteria name -> weight mapping
        criteria_weights = {c.criteria_name: c.weight_points for c in criteria_list}

        # Get candidates (optionally filtered)
        candidates = self._get_filtered_candidates(jd_id, filter_criteria)

        # Compute scores for each candidate
        scored_candidates: list[tuple[Candidate, float]] = []
        for candidate in candidates:
            score = self._compute_candidate_score(candidate, criteria_weights)
            scored_candidates.append((candidate, score))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Convert to response objects with rank numbers
        ranked_responses = [
            RankedCandidateResponse(
                id=candidate.id,
                rank=idx + 1,
                full_name=candidate.full_name,
                zoho_candidate_id=candidate.zoho_candidate_id,
                email=candidate.email,
                phone=candidate.phone,
                current_location=candidate.current_location,
                current_company=candidate.current_company,
                skills=candidate.skills or [],
                total_experience_years=candidate.total_experience_years,
                notice_period_days=candidate.notice_period_days,
                score=score,
                match_percentage=score,  # score is already 0-100, match % is the same
                status=candidate.status,
            )
            for idx, (candidate, score) in enumerate(scored_candidates)
        ]

        return RankingResponse(
            jd_id=jd_id,
            jd_title=jd.title,
            total_candidates=len(candidates),
            ranked_candidates=ranked_responses,
            filter_summary=self._build_filter_summary(filter_criteria),
        )

    def _get_filtered_candidates(
        self,
        jd_id: UUID,
        filter_criteria: CandidateFilterCriteria | None = None,
    ) -> list[Candidate]:
        """Get candidates filtered by criteria."""
        # Start with base filter criteria including the JD
        criteria = filter_criteria or CandidateFilterCriteria()
        criteria.jd_id = jd_id

        # Compose filter query
        filters = CandidateFilterQueryComposer.compose(criteria)

        # Build query
        query = self.session.query(Candidate)
        for filter_expr in filters:
            query = query.filter(filter_expr)

        return list(query.all())

    def _compute_candidate_score(self, candidate: Candidate, criteria_weights: dict[str, float]) -> float:
        """Compute weighted score for a candidate.
        
        Score = sum(criterion_weight * criterion_match_score)
        
        Each criterion has its own matching logic:
        - "skills matched": count of matched required skills / total required skills
        - "experience": normalized experience (capped at 1.0)
        - "notice period": inverse score (lower notice period = higher score)
        """
        total_score = 0.0

        for criterion_name, weight in criteria_weights.items():
            match_score = self._compute_criterion_match_score(candidate, criterion_name)
            total_score += weight * match_score

        return total_score

    def _compute_criterion_match_score(self, candidate: Candidate, criterion_name: str) -> float:
        """Compute match score (0-1) for a single criterion.
        
        Returns:
            Match score between 0 and 1 (will be multiplied by weight)
        """
        criterion_name_lower = criterion_name.lower()

        # Skills matching
        if "skill" in criterion_name_lower:
            return self._score_skills(candidate)

        # Experience matching
        if "experience" in criterion_name_lower:
            return self._score_experience(candidate)

        # Notice period matching
        if "notice" in criterion_name_lower:
            return self._score_notice_period(candidate)

        # Location matching
        if "location" in criterion_name_lower:
            return self._score_location(candidate)

        # CTC/Salary matching
        if "ctc" in criterion_name_lower or "salary" in criterion_name_lower:
            return self._score_ctc(candidate)

        # Education matching
        if "education" in criterion_name_lower or "degree" in criterion_name_lower:
            return self._score_education(candidate)

        # Default: 0.5 if no specific logic
        return 0.5

    def _score_skills(self, candidate: Candidate) -> float:
        """Score skills: penalize if no skills at all, give credit for having skills."""
        if not candidate.skills:
            return 0.2  # Penalize missing skills
        # If they have any skills, consider it a partial match
        # (full match would require knowing required skills from JD)
        return min(1.0, len(candidate.skills) / 5.0)  # 5 skills = perfect score

    def _score_experience(self, candidate: Candidate) -> float:
        """Score total experience: normalize to 0-1 scale.
        
        Assumes 10+ years = full match (1.0).
        """
        if candidate.total_experience_years is None:
            return 0.2  # Penalize missing experience data
        
        # 10+ years = 1.0, 0 years = 0.0, scale linearly
        score = min(1.0, candidate.total_experience_years / 10.0)
        return max(0.0, score)  # Ensure non-negative

    def _score_notice_period(self, candidate: Candidate) -> float:
        """Score notice period: lower is better.
        
        Assumes 30 days or less = full match (1.0).
        Assumes 90+ days = poor match (0.2).
        """
        if candidate.notice_period_days is None:
            return 0.5  # Neutral if unknown

        # 0-30 days = 1.0, 30-60 days = 0.5, 60+ days = 0.2
        if candidate.notice_period_days <= 30:
            return 1.0
        elif candidate.notice_period_days <= 60:
            return 0.5
        else:
            return 0.2

    def _score_location(self, candidate: Candidate) -> float:
        """Score location: any location present is a positive signal."""
        if candidate.current_location or candidate.preferred_location:
            return 1.0
        return 0.3

    def _score_ctc(self, candidate: Candidate) -> float:
        """Score CTC/salary: if we have CTC data, consider it a positive signal."""
        if candidate.current_ctc is not None or candidate.expected_ctc is not None:
            return 0.8  # Having salary info is valuable
        return 0.3

    def _score_education(self, candidate: Candidate) -> float:
        """Score education: if we have degree info, consider it a positive signal."""
        if candidate.degree or candidate.normalized_degree:
            return 0.8  # Having education info is valuable
        return 0.3

    def _build_filter_summary(self, filter_criteria: CandidateFilterCriteria | None) -> dict[str, str | int | float | None] | None:
        """Build a summary of applied filters for the response."""
        if not filter_criteria:
            return None

        summary = {}
        if filter_criteria.status:
            summary["status"] = filter_criteria.status
        if filter_criteria.source:
            summary["source"] = filter_criteria.source
        if filter_criteria.location:
            summary["location"] = filter_criteria.location
        if filter_criteria.experience_min is not None:
            summary["experience_min_years"] = filter_criteria.experience_min
        if filter_criteria.notice_period_max is not None:
            summary["notice_period_max_days"] = filter_criteria.notice_period_max

        return summary if summary else None

    def get_score_breakdown(
        self,
        candidate_id: UUID,
        jd_id: UUID,
    ) -> list[RankingScoreBreakdownResponse]:
        """Get detailed breakdown of how score was computed for a candidate.
        
        Useful for debugging and understanding why a candidate ranked high/low.
        
        Args:
            candidate_id: Candidate ID
            jd_id: Job description ID
            
        Returns:
            List of breakdown entries for each criterion
            
        Raises:
            RankingCandidateNotFoundError: If candidate doesn't exist
            RankingJDNotFoundError: If JD doesn't exist
            RankingNoCriteriaError: If no criteria are defined for the JD
        """
        # Get candidate and JD
        candidate = self.candidate_repository.get_by_id(candidate_id)
        if candidate is None:
            raise RankingCandidateNotFoundError(candidate_id)

        jd = self.job_description_repository.get_by_id(jd_id)
        if jd is None:
            raise RankingJDNotFoundError(jd_id)

        # Get ranking criteria
        criteria_list = self.ranking_criteria_repository.get_by_jd_id(jd_id)
        if not criteria_list:
            raise RankingNoCriteriaError(jd_id)

        # Compute breakdown for each criterion
        breakdowns = []
        for criterion in criteria_list:
            match_score = self._compute_criterion_match_score(candidate, criterion.criteria_name)
            weighted_contribution = criterion.weight_points * match_score

            breakdowns.append(
                RankingScoreBreakdownResponse(
                    candidate_id=candidate_id,
                    candidate_name=candidate.full_name,
                    criterion_name=criterion.criteria_name,
                    weight_points=criterion.weight_points,
                    match_score=match_score,
                    weighted_contribution=weighted_contribution,
                )
            )

        return breakdowns
