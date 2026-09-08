from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.ranking_criteria_repository import RankingCriteriaRepository
from app.schemas.ranking_criteria import (
    GetRankingCriteriaResponse,
    RankingCriteriaItemResponse,
    SetRankingCriteriaRequest,
)


class RankingCriteriaError(Exception):
    status_code = 400
    code = "RANKING_CRITERIA_ERROR"
    detail = "Ranking criteria request could not be processed"


class RankingCriteriaNotFoundError(RankingCriteriaError):
    status_code = 404
    code = "JD_NOT_FOUND"

    def __init__(self, jd_id: UUID) -> None:
        self.detail = f"Job description with id '{jd_id}' not found"


class RankingCriteriaWeightValidationError(RankingCriteriaError):
    status_code = 422
    code = "INVALID_WEIGHT_SUM"

    def __init__(self, total_weight: float) -> None:
        self.detail = f"Total weight points must equal 100, got {total_weight}"


@dataclass(slots=True)
class RankingCriteriaService:
    repository: RankingCriteriaRepository
    job_description_repository: JobDescriptionRepository

    def get_criteria_for_jd(self, jd_id: UUID) -> GetRankingCriteriaResponse:
        """Get all ranking criteria for a job description."""
        # Verify JD exists
        jd = self.job_description_repository.get_by_id(jd_id)
        if jd is None:
            raise RankingCriteriaNotFoundError(jd_id)

        criteria_list = self.repository.get_by_jd_id(jd_id)
        items = [
            RankingCriteriaItemResponse(
                id=criterion.id,
                jd_id=criterion.jd_id,
                criteria_name=criterion.criteria_name,
                weight_points=criterion.weight_points,
                created_at=criterion.created_at,
            )
            for criterion in criteria_list
        ]

        total_weight = sum(item.weight_points for item in items)
        return GetRankingCriteriaResponse(jd_id=jd_id, criteria=items, total_weight=total_weight)

    def set_criteria_for_jd(self, jd_id: UUID, request: SetRankingCriteriaRequest) -> GetRankingCriteriaResponse:
        """Replace all ranking criteria for a job description.
        
        This method:
        1. Verifies the JD exists
        2. Validates that weights sum to exactly 100
        3. Deletes all existing criteria
        4. Creates new criteria
        5. Returns the updated criteria list
        """
        # Verify JD exists
        jd = self.job_description_repository.get_by_id(jd_id)
        if jd is None:
            raise RankingCriteriaNotFoundError(jd_id)

        # Validate weight sum
        total_weight = sum(item.weight_points for item in request.criteria)
        if total_weight != 100.0:
            raise RankingCriteriaWeightValidationError(total_weight)

        # Delete existing criteria and create new ones
        self.repository.delete_by_jd_id(jd_id)
        criteria_data = [
            {
                "criteria_name": item.criteria_name,
                "weight_points": item.weight_points,
            }
            for item in request.criteria
        ]
        created_items = self.repository.create_batch(jd_id, criteria_data)

        items = [
            RankingCriteriaItemResponse(
                id=criterion.id,
                jd_id=criterion.jd_id,
                criteria_name=criterion.criteria_name,
                weight_points=criterion.weight_points,
                created_at=criterion.created_at,
            )
            for criterion in created_items
        ]

        total_weight = sum(item.weight_points for item in items)
        return GetRankingCriteriaResponse(jd_id=jd_id, criteria=items, total_weight=total_weight)
