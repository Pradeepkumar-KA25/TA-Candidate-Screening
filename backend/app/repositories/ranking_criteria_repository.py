from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.ranking_criterion import RankingCriterion


class RankingCriteriaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_jd_id(self, jd_id: UUID) -> list[RankingCriterion]:
        """Get all ranking criteria for a specific job description."""
        statement = select(RankingCriterion).where(RankingCriterion.jd_id == jd_id)
        return list(self.session.scalars(statement).all())

    def create(self, *, jd_id: UUID, criteria_name: str, weight_points: float) -> RankingCriterion:
        """Create a single ranking criterion."""
        item = RankingCriterion(
            jd_id=jd_id,
            criteria_name=criteria_name,
            weight_points=weight_points,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete_by_jd_id(self, jd_id: UUID) -> None:
        """Delete all ranking criteria for a specific job description."""
        statement = delete(RankingCriterion).where(RankingCriterion.jd_id == jd_id)
        self.session.execute(statement)
        self.session.commit()

    def create_batch(self, jd_id: UUID, criteria_list: list[dict[str, str | float]]) -> list[RankingCriterion]:
        """Create multiple ranking criteria in a batch."""
        items = [
            RankingCriterion(
                jd_id=jd_id,
                criteria_name=item["criteria_name"],
                weight_points=item["weight_points"],
            )
            for item in criteria_list
        ]
        self.session.add_all(items)
        self.session.commit()
        for item in items:
            self.session.refresh(item)
        return items
