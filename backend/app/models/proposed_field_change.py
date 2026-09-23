from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProposedFieldChange(Base):
    """Represents a proposed field change for a candidate based on resume extraction."""

    __tablename__ = "proposed_field_changes"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    candidate_review_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidate_reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zoho_field_api_name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g., "Email", "Phone"
    zoho_field_display_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Email Address"
    existing_zoho_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Original Zoho value (for audit)
    extracted_resume_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # What Ollama extracted
    proposed_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # What will be sent if approved
    change_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, APPROVED, REJECTED
    field_approval_notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"ProposedFieldChange(id={self.id!s}, field={self.zoho_field_api_name!r}, status={self.change_status!r})"
