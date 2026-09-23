from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.proposed_field_change import ProposedFieldChange


class ProposedFieldChangeRepository:
    """Repository for managing proposed field changes."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        candidate_review_id: UUID,
        zoho_field_api_name: str,
        zoho_field_display_name: str,
        existing_zoho_value: str | None = None,
        extracted_resume_value: str | None = None,
        proposed_value: str | None = None,
    ) -> ProposedFieldChange:
        """Create a new proposed field change."""
        change = ProposedFieldChange(
            candidate_review_id=candidate_review_id,
            zoho_field_api_name=zoho_field_api_name,
            zoho_field_display_name=zoho_field_display_name,
            existing_zoho_value=existing_zoho_value,
            extracted_resume_value=extracted_resume_value,
            proposed_value=proposed_value,
        )
        self.session.add(change)
        self.session.flush()
        return change

    def get_by_id(self, change_id: UUID) -> ProposedFieldChange | None:
        """Get proposed change by ID."""
        return self.session.query(ProposedFieldChange).filter(ProposedFieldChange.id == change_id).first()

    def get_by_candidate_review_id(self, candidate_review_id: UUID) -> list[ProposedFieldChange]:
        """Get all proposed changes for a candidate review."""
        return (
            self.session.query(ProposedFieldChange)
            .filter(ProposedFieldChange.candidate_review_id == candidate_review_id)
            .all()
        )

    def get_by_candidate_review_id_and_status(
        self, candidate_review_id: UUID, status: str
    ) -> list[ProposedFieldChange]:
        """Get proposed changes with specific status."""
        return (
            self.session.query(ProposedFieldChange)
            .filter(
                ProposedFieldChange.candidate_review_id == candidate_review_id,
                ProposedFieldChange.change_status == status,
            )
            .all()
        )

    def update_status(self, change_id: UUID, status: str, notes: str | None = None) -> ProposedFieldChange | None:
        """Update change status."""
        change = self.get_by_id(change_id)
        if change:
            change.change_status = status
            if notes:
                change.field_approval_notes = notes
            self.session.flush()
        return change

    def bulk_update_status(
        self, change_ids: list[UUID], status: str, notes: str | None = None
    ) -> int:
        """Update status for multiple changes."""
        if not change_ids:
            return 0
        count = (
            self.session.query(ProposedFieldChange)
            .filter(ProposedFieldChange.id.in_(change_ids))
            .update({ProposedFieldChange.change_status: status})
        )
        if notes:
            self.session.query(ProposedFieldChange).filter(ProposedFieldChange.id.in_(change_ids)).update(
                {ProposedFieldChange.field_approval_notes: notes}
            )
        self.session.flush()
        return count
