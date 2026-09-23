from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.models.candidate import Candidate
from app.models.candidate_review import CandidateReview
from app.models.review_batch import ReviewBatch
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_review_repository import CandidateReviewRepository
from app.repositories.proposed_field_change_repository import ProposedFieldChangeRepository
from app.repositories.review_batch_repository import ReviewBatchRepository
from app.services.resume_fetch_service import ResumeFetchService

logger = logging.getLogger("resume_enrichment")


class ResumeEnrichmentError(Exception):
    """Base exception for resume enrichment errors."""

    pass


class ResumeEnrichmentService:
    """Service for Phase 1: Resume extraction, comparison, and review batch management."""

    # Field mapping: Zoho field name → (Resume extraction data path, Display name)
    FIELD_MAPPING = {
        "Email": ("email", "contact.email", "Email Address"),
        "Phone": ("phone", "contact.phone", "Phone Number"),
        "Designation": ("title", "experience[0].title", "Designation / Job Title"),
        "Current_Company": ("company", "experience[0].company", "Current Company"),
        "Degree": ("degree", "education[0].degree", "Degree"),
        "Institution": ("institution", "education[0].institution", "Institution / University"),
        "Skills": ("skills", "skills", "Technical Skills"),
        "Summary": ("summary", "summary", "Professional Summary"),
    }

    def __init__(
        self,
        review_batch_repository: ReviewBatchRepository,
        candidate_review_repository: CandidateReviewRepository,
        proposed_field_change_repository: ProposedFieldChangeRepository,
        candidate_repository: CandidateRepository,
        zoho_recruit_client: ZohoRecruitClient,
        resume_fetch_service: ResumeFetchService,
    ):
        self.review_batch_repository = review_batch_repository
        self.candidate_review_repository = candidate_review_repository
        self.proposed_field_change_repository = proposed_field_change_repository
        self.candidate_repository = candidate_repository
        self.zoho_recruit_client = zoho_recruit_client
        self.resume_fetch_service = resume_fetch_service

    def create_review_batch(
        self, batch_size: int | None = None, access_token: str | None = None, created_by_user_id: UUID | None = None
    ) -> ReviewBatch:
        """
        Create a new review batch and process candidates.

        1. Select batch_size candidates (or from config)
        2. For each candidate, fetch Zoho data + resume
        3. Extract resume data via Ollama
        4. Compare Zoho vs extracted values
        5. Create proposed changes (only for empty Zoho fields with resume data)
        6. Save to database

        Args:
            batch_size: Number of candidates to process (uses REVIEW_BATCH_SIZE config if None)
            access_token: Zoho API access token (optional for testing)
            created_by_user_id: User who created the batch

        Returns:
            ReviewBatch with status and counts

        Raises:
            ResumeEnrichmentError: If batch creation fails
        """
        if batch_size is None:
            batch_size = settings.review_batch_size

        try:
            # Generate batch number
            batch_number = self.review_batch_repository.get_next_batch_number()
            logger.info(f"Creating review batch: {batch_number}, size: {batch_size}")

            # Create batch record
            batch = self.review_batch_repository.create(
                batch_number=batch_number,
                batch_size=batch_size,
                total_candidates=batch_size,
                created_by_user_id=created_by_user_id,
            )

            # Get candidates without review yet (select up to batch_size)
            candidates_to_review = self.candidate_repository.get_unreviewed_candidates(limit=batch_size)

            if not candidates_to_review:
                logger.warning(f"No unreviewed candidates found for batch {batch_number}")
                batch.status = "COMPLETED"
                batch.total_candidates = 0
                return batch

            logger.info(f"Processing {len(candidates_to_review)} candidates in batch {batch_number}")

            # Update batch status
            batch.status = "PROCESSING"
            batch.processing_started_at = datetime.now(timezone.utc)
            self.review_batch_repository.session.flush()

            # Process each candidate
            successful_count = 0
            error_count = 0

            for candidate in candidates_to_review:
                try:
                    self._process_candidate(batch.id, candidate, access_token)
                    successful_count += 1
                except Exception as exc:
                    logger.error(f"Error processing candidate {candidate.full_name} ({candidate.id}): {str(exc)}")
                    error_count += 1
                    # Continue processing other candidates instead of stopping

            # Update batch counts
            batch.processed_candidates = successful_count
            batch.status = "COMPLETED"
            batch.processing_completed_at = datetime.now(timezone.utc)
            self.review_batch_repository.session.flush()

            logger.info(
                f"Batch {batch_number} completed: {successful_count} processed, {error_count} errors"
            )

            return batch

        except Exception as exc:
            logger.error(f"Failed to create review batch: {str(exc)}")
            raise ResumeEnrichmentError(f"Failed to create review batch: {str(exc)}") from exc

    def get_review_batch(self, batch_id: UUID) -> ReviewBatch | None:
        """Get batch by ID."""
        return self.review_batch_repository.get_by_id(batch_id)

    def get_candidate_review(self, candidate_review_id: UUID) -> CandidateReview | None:
        """Get candidate review with all proposed changes."""
        return self.candidate_review_repository.get_by_id(candidate_review_id)

    def approve_proposed_changes(
        self,
        candidate_review_id: UUID,
        field_ids: list[UUID] | None = None,
        user_id: UUID | None = None,
        notes: str | None = None,
    ) -> int:
        """
        Approve proposed changes for a candidate.

        Args:
            candidate_review_id: The candidate review ID
            field_ids: Specific field IDs to approve (None = approve all PENDING)
            user_id: User approving the changes
            notes: Optional approval notes

        Returns:
            Number of fields approved
        """
        if field_ids is None:
            # Approve all PENDING fields
            pending_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
                candidate_review_id, "PENDING"
            )
            field_ids = [change.id for change in pending_changes]

        if not field_ids:
            return 0

        count = self.proposed_field_change_repository.bulk_update_status(field_ids, "APPROVED", notes)

        # Update candidate review status if all fields approved
        candidate_review = self.candidate_review_repository.get_by_id(candidate_review_id)
        if candidate_review:
            all_changes = self.proposed_field_change_repository.get_by_candidate_review_id(candidate_review_id)
            if all(change.change_status == "APPROVED" for change in all_changes):
                self.candidate_review_repository.update_approval_status(
                    candidate_review_id, "APPROVED", user_id, notes
                )

        logger.info(f"Approved {count} proposed changes for candidate review {candidate_review_id}")
        return count

    def reject_proposed_changes(
        self,
        candidate_review_id: UUID,
        field_ids: list[UUID] | None = None,
        user_id: UUID | None = None,
        notes: str | None = None,
    ) -> int:
        """
        Reject proposed changes for a candidate.

        Args:
            candidate_review_id: The candidate review ID
            field_ids: Specific field IDs to reject (None = reject all PENDING)
            user_id: User rejecting the changes
            notes: Optional rejection notes

        Returns:
            Number of fields rejected
        """
        if field_ids is None:
            # Reject all PENDING fields
            pending_changes = self.proposed_field_change_repository.get_by_candidate_review_id_and_status(
                candidate_review_id, "PENDING"
            )
            field_ids = [change.id for change in pending_changes]

        if not field_ids:
            return 0

        count = self.proposed_field_change_repository.bulk_update_status(field_ids, "REJECTED", notes)

        # Update candidate review status if all fields rejected
        candidate_review = self.candidate_review_repository.get_by_id(candidate_review_id)
        if candidate_review:
            all_changes = self.proposed_field_change_repository.get_by_candidate_review_id(candidate_review_id)
            if all(change.change_status == "REJECTED" for change in all_changes):
                self.candidate_review_repository.update_approval_status(
                    candidate_review_id, "REJECTED", user_id, notes
                )

        logger.info(f"Rejected {count} proposed changes for candidate review {candidate_review_id}")
        return count

    # Private helper methods

    def _process_candidate(self, batch_id: UUID, candidate: Candidate, access_token: str | None = None) -> None:
        """
        Process a single candidate:
        1. Create candidate_review record
        2. Extract data from resume
        3. Get Zoho candidate data
        4. Compare values
        5. Create proposed changes
        """
        logger.info(f"Processing candidate: {candidate.full_name} ({candidate.id})")

        # Create candidate review record
        candidate_review = self.candidate_review_repository.create(
            batch_id=batch_id,
            candidate_id=candidate.id,
            candidate_name=candidate.full_name,
            zoho_candidate_id=candidate.zoho_candidate_id,
        )

        # Get candidate's resume file
        if not candidate.resume_url:
            logger.warning(f"No resume available for {candidate.full_name}")
            return

        # Extract resume data using Ollama
        try:
            extracted_data = self._extract_resume_data(candidate.resume_url)
            logger.debug(f"Extracted resume data for {candidate.full_name}: {extracted_data}")
        except Exception as exc:
            logger.error(f"Failed to extract resume data for {candidate.full_name}: {str(exc)}")
            return

        # Get current Zoho candidate data
        zoho_candidate_data = self._get_zoho_candidate_data(candidate)

        # Compare values and create proposed changes
        for zoho_field_name, (_, extracted_field_path, display_name) in self.FIELD_MAPPING.items():
            existing_zoho_value = zoho_candidate_data.get(zoho_field_name)
            extracted_value = self._get_extracted_value(extracted_data, extracted_field_path)

            # Apply business rule: only propose change if Zoho is empty and resume has value
            comparison = self._compare_values(existing_zoho_value, extracted_value)

            if comparison["action"] == "PROPOSE_UPDATE":
                self.proposed_field_change_repository.create(
                    candidate_review_id=candidate_review.id,
                    zoho_field_api_name=zoho_field_name,
                    zoho_field_display_name=display_name,
                    existing_zoho_value=existing_zoho_value,
                    extracted_resume_value=extracted_value,
                    proposed_value=extracted_value,
                )
                logger.debug(f"Created proposed change for {display_name}: {extracted_value}")

    def _extract_resume_data(self, resume_file_path: str) -> dict[str, Any]:
        """Extract structured data from resume using Ollama."""
        try:
            from pathlib import Path as PathlibPath

            if not PathlibPath(resume_file_path).exists():
                raise ResumeEnrichmentError(f"Resume file not found: {resume_file_path}")

            # Determine file type from extension
            file_ext = PathlibPath(resume_file_path).suffix.lower()
            file_type_map = {
                ".pdf": "pdf",
                ".docx": "docx",
                ".doc": "doc",
            }
            file_type = file_type_map.get(file_ext, "pdf")

            # Use existing Kanini parser
            from app.services.kanini_resume_parser import parse_resume

            extracted = parse_resume(resume_file_path, file_type)

            return extracted if isinstance(extracted, dict) else extracted.__dict__

        except Exception as exc:
            raise ResumeEnrichmentError(f"Resume extraction failed: {str(exc)}") from exc

    def _get_zoho_candidate_data(self, candidate: Candidate) -> dict[str, Any]:
        """Get candidate's current Zoho data (from local candidate record)."""
        return {
            "Email": candidate.email,
            "Phone": candidate.phone,
            "Designation": candidate.raw_payload.get("Designation") if candidate.raw_payload else None,
            "Current_Company": candidate.current_company,
            "Degree": candidate.degree,
            "Institution": candidate.raw_payload.get("Institution") if candidate.raw_payload else None,
            "Skills": candidate.skills,
            "Summary": candidate.raw_payload.get("Summary") if candidate.raw_payload else None,
        }

    def _get_extracted_value(self, extracted_data: dict[str, Any], field_path: str) -> Any:
        """Get nested value from extracted data using dot notation (e.g., 'contact.email')."""
        keys = field_path.split(".")
        value = extracted_data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.startswith("0"):
                value = value[0] if value else None
            else:
                return None

        return value

    def _compare_values(self, zoho_value: Any, extracted_value: Any) -> dict[str, Any]:
        """
        Apply business rule for field comparison.

        Logic:
        1. If Zoho has a real non-empty value → KEEP it (never propose update)
        2. If Zoho is empty AND resume has value → PROPOSE update  
        3. If both are empty → NO_CHANGE

        Returns:
            {
                "action": "KEEP_ZOHO" | "PROPOSE_UPDATE" | "NO_CHANGE",
                "existing_zoho_value": zoho_value,
                "extracted_value": extracted_value,
                "proposed_change": extracted_value or None
            }
        """
        # Check if Zoho value is real (not None, empty string, or whitespace)
        zoho_has_value = (
            zoho_value is not None 
            and zoho_value != "" 
            and str(zoho_value).strip() != ""
        )
        
        # Check if extracted value is real
        extracted_has_value = (
            extracted_value is not None 
            and extracted_value != "" 
            and str(extracted_value).strip() != ""
        )

        # Zoho has existing value → NEVER create proposed change
        if zoho_has_value:
            return {
                "action": "KEEP_ZOHO",
                "existing_zoho_value": zoho_value,
                "extracted_value": extracted_value,
                "proposed_change": None,
            }

        # Zoho empty, resume has value → Create proposed change
        if extracted_has_value:
            return {
                "action": "PROPOSE_UPDATE",
                "existing_zoho_value": None,
                "extracted_value": extracted_value,
                "proposed_change": extracted_value,
            }

        # Both empty → No change
        return {
            "action": "NO_CHANGE",
            "existing_zoho_value": None,
            "extracted_value": None,
            "proposed_change": None,
        }

    def delete_review_batch(self, batch_id: UUID) -> bool:
        """Delete a review batch and all related records (candidate reviews, proposed changes)."""
        try:
            batch = self.review_batch_repository.get_by_id(batch_id)
            if not batch:
                logger.warning(f"Batch {batch_id} not found")
                return False

            # Delete is handled by cascade delete due to foreign key constraints
            success = self.review_batch_repository.delete(batch_id)
            if success:
                logger.info(f"Deleted batch {batch_id} and all related records")
            return success
        except Exception as exc:
            logger.error(f"Failed to delete batch {batch_id}: {str(exc)}")
            return False
