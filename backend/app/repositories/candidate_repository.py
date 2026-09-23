from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session

from app.models.candidate import Candidate


ALLOWED_SORT_FIELDS: dict[str, tuple] = {
    "full_name": (Candidate.full_name, "full_name"),
    "current_company": (Candidate.current_company, "current_company"),
    "current_location": (Candidate.current_location, "current_location"),
    "total_experience_years": (Candidate.total_experience_years, "total_experience_years"),
    "notice_period_days": (Candidate.notice_period_days, "notice_period_days"),
    "status": (Candidate.status, "status"),
    "created_at": (Candidate.created_at, "created_at"),
    "updated_at": (Candidate.updated_at, "updated_at"),
}


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, candidate_id: UUID) -> Candidate | None:
        statement = select(Candidate).where(Candidate.id == candidate_id)
        return self.session.scalar(statement)

    def get_by_zoho_candidate_id(self, zoho_candidate_id: str) -> Candidate | None:
        statement = select(Candidate).where(Candidate.zoho_candidate_id == zoho_candidate_id)
        return self.session.scalar(statement)

    def get_by_zoho_record_id(self, zoho_record_id: str) -> Candidate | None:
        statement = select(Candidate).where(Candidate.zoho_record_id == zoho_record_id)
        return self.session.scalar(statement)

    def get_latest_synced_candidate(self) -> Candidate | None:
        statement = select(Candidate).order_by(Candidate.updated_at.desc(), Candidate.created_at.desc())
        return self.session.scalar(statement)

    def find_existing_by_zoho_ids(self, zoho_record_id: str, zoho_candidate_id: str | None) -> Candidate | None:
        existing = self.get_by_zoho_record_id(zoho_record_id)
        if existing is None and isinstance(zoho_candidate_id, str) and zoho_candidate_id.strip():
            existing = self.get_by_zoho_candidate_id(zoho_candidate_id.strip())
        if existing is None:
            statement = select(Candidate).where(Candidate.zoho_candidate_id == zoho_record_id)
            existing = self.session.scalar(statement)
        return existing

    def list_all_for_duplicate_detection(self) -> list[Candidate]:
        statement = select(Candidate).order_by(Candidate.created_at.asc(), Candidate.id.asc())
        return list(self.session.scalars(statement).all())

    def create_or_update(self, payload: dict, *, commit: bool = True) -> tuple[Candidate, bool]:
        zoho_record_id = str(payload["zoho_record_id"])
        zoho_candidate_id = payload.get("zoho_candidate_id")

        existing = self.find_existing_by_zoho_ids(zoho_record_id, zoho_candidate_id)

        if existing is None:
            candidate = Candidate(**payload)
            self.session.add(candidate)
            if commit:
                self.session.commit()
                self.session.refresh(candidate)
            else:
                self.session.flush()
            return candidate, True

        for key, value in payload.items():
            setattr(existing, key, value)

        self.session.add(existing)
        if commit:
            self.session.commit()
            self.session.refresh(existing)
        else:
            self.session.flush()
        return existing, False

    def list_candidates(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None,
        sort_by: str,
        sort_order: str,
        filter_clauses: list[ColumnElement[bool]] | None = None,
    ) -> tuple[list[Candidate], int]:
        filters = []
        keyword = q.strip().lower() if q else ""
        if keyword:
            # Check if this contains a comma (indicating multi-skill search)
            if "," in q.strip():
                # Multi-skill search: split by comma and filter empty entries
                skills_to_search = [s.strip().lower() for s in q.strip().split(",") if s.strip()]
                
                # Apply AND logic: each skill must match in the skills array
                for skill in skills_to_search:
                    skill_pattern = f"%{skill}%"
                    # Match skill in the skills JSON array - ALL skills must match
                    filters.append(func.lower(cast(Candidate.skills, String)).like(skill_pattern))
            else:
                # Single keyword search across multiple fields including Zoho IDs
                pattern = f"%{keyword}%"
                search_conditions = [
                    func.lower(Candidate.full_name).like(pattern),
                    func.lower(Candidate.current_company).like(pattern),
                    func.lower(cast(Candidate.skills, String)).like(pattern),
                    func.lower(Candidate.email).like(pattern),
                ]
                
                # Handle Zoho ID searches - cast coalesced NULL values to string for proper comparison
                # This allows searching for numeric Zoho IDs and formatted IDs like "ZR_55776_CAND"
                zoho_candidate_id_pattern = func.lower(cast(func.coalesce(Candidate.zoho_candidate_id, ""), String)).like(pattern)
                zoho_record_id_pattern = func.lower(cast(func.coalesce(Candidate.zoho_record_id, ""), String)).like(pattern)
                candidate_id_pattern = func.lower(cast(func.coalesce(Candidate.candidate_id, ""), String)).like(pattern)
                
                search_conditions.append(zoho_candidate_id_pattern)
                search_conditions.append(zoho_record_id_pattern)
                search_conditions.append(candidate_id_pattern)
                
                filters.append(or_(*search_conditions))

        if filter_clauses:
            filters.extend(filter_clauses)

        sort_column = ALLOWED_SORT_FIELDS.get(sort_by, ALLOWED_SORT_FIELDS["full_name"])[0]
        order_expression = sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc()

        count_statement = select(func.count(Candidate.id))
        if filters:
            count_statement = count_statement.where(*filters)
        total_items = self.session.scalar(count_statement) or 0

        statement = select(Candidate)
        if filters:
            statement = statement.where(*filters)
        statement = statement.order_by(order_expression, Candidate.id).offset((page - 1) * page_size).limit(page_size)

        candidates = list(self.session.scalars(statement).all())
        return candidates, total_items

    def delete(self, candidate_id: UUID) -> None:
        """Delete a candidate by ID."""
        statement = select(Candidate).where(Candidate.id == candidate_id)
        candidate = self.session.scalar(statement)
        if candidate:
            self.session.delete(candidate)
            self.session.commit()

    def get_unreviewed_candidates(self, limit: int = 20) -> list[Candidate]:
        """Get candidates that haven't been reviewed for resume enrichment yet."""
        # Get candidates that have a resume and haven't been added to any review batch yet
        from sqlalchemy import not_, exists
        from app.models.candidate_review import CandidateReview

        subquery = select(CandidateReview.candidate_id)
        statement = (
            select(Candidate)
            .where(
                Candidate.resume_url.isnot(None),  # Must have a resume
                not_(exists(subquery.where(CandidateReview.candidate_id == Candidate.id))),  # Not yet reviewed
            )
            .order_by(Candidate.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
