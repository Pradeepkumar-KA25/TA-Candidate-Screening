"""Resume Fetch Service - Download and save candidate resumes from Zoho Recruit."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from app.integrations.zoho_recruit import ZohoRecruitClient, ZohoRecruitClientError
from app.repositories.candidate_repository import CandidateRepository
from app.storage import StorageBackend, get_storage_backend

logger = logging.getLogger("resume_fetch")


class ResumeFetchError(Exception):
    """Base exception for resume fetch errors."""
    pass


class ResumeFetchService:
    """Service for fetching and saving candidate resumes from Zoho Recruit."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        zoho_recruit_client: ZohoRecruitClient,
        storage: StorageBackend | None = None,
    ):
        self.candidate_repository = candidate_repository
        self.zoho_recruit_client = zoho_recruit_client
        self.storage = storage or get_storage_backend()

    def fetch_and_save_resume(
        self,
        access_token: str,
        candidate_id: str,
        zoho_candidate_id: str,
        full_name: str,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Fetch candidate resume from Zoho and save locally.

        Args:
            access_token: Zoho API access token
            candidate_id: Our internal candidate UUID
            zoho_candidate_id: Zoho candidate ID
            full_name: Candidate name for logging

        Returns:
            Tuple of (resume_url, resume_file_name, error_message)
            If successful, error_message is None.
            If failed, both resume_url and resume_file_name are None.
        """
        try:
            # Fetch attachments for candidate
            logger.info(f"Fetching attachments for {full_name} (Zoho ID: {zoho_candidate_id})")
            attachments = self.zoho_recruit_client.fetch_candidate_attachments(
                access_token=access_token,
                candidate_id=zoho_candidate_id,
            )
            logger.info(f"Got {len(attachments)} attachments for {full_name}")

            if not attachments:
                logger.info(f"No attachments found for candidate {full_name} ({zoho_candidate_id})")
                return None, None, None

            # Find resume attachment (PDF, DOCX, DOC)
            resume_attachment = self._find_resume_attachment(attachments)
            if not resume_attachment:
                logger.info(f"No resume file found in attachments for candidate {full_name} ({zoho_candidate_id})")
                return None, None, None

            attachment_id = resume_attachment.get("id")
            file_name = resume_attachment.get("name", "resume")

            # Download attachment (need candidate_id in endpoint)
            file_content = self.zoho_recruit_client.download_attachment(
                access_token=access_token,
                candidate_id=zoho_candidate_id,
                attachment_id=attachment_id,
            )

            # Save to local storage
            resume_url, saved_file_name = self._save_resume(
                candidate_id=candidate_id,
                file_name=file_name,
                file_content=file_content,
            )

            logger.info(f"Successfully saved resume for {full_name}: {resume_url}")
            return resume_url, saved_file_name, None

        except ZohoRecruitClientError as exc:
            error_msg = f"Failed to fetch resume from Zoho: {str(exc)}"
            logger.error(f"Resume fetch error for {full_name} ({zoho_candidate_id}): {error_msg}")
            return None, None, error_msg
        except ResumeFetchError as exc:
            error_msg = str(exc)
            logger.error(f"Resume save error for {full_name} ({zoho_candidate_id}): {error_msg}")
            return None, None, error_msg
        except Exception as exc:
            error_msg = f"Unexpected error: {str(exc)}"
            logger.error(f"Unexpected error fetching resume for {full_name} ({zoho_candidate_id}): {error_msg}", exc_info=True)
            return None, None, error_msg

    @staticmethod
    def _find_resume_attachment(attachments: list[dict]) -> dict | None:
        """Find resume attachment from list of attachments."""
        resume_extensions = {".pdf", ".docx", ".doc", ".txt"}

        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            file_name = attachment.get("name", "").lower()
            # Check if file has resume-like extension
            for ext in resume_extensions:
                if file_name.endswith(ext):
                    return attachment

        # If no obvious resume file, return first attachment
        return attachments[0] if attachments else None

    def _save_resume(
        self,
        candidate_id: str,
        file_name: str,
        file_content: bytes,
    ) -> tuple[str, str]:
        """Save a resume using the configured storage backend."""
        if not file_content:
            raise ResumeFetchError("Downloaded file is empty")

        extension = Path(file_name).suffix.lower()
        if extension not in {".pdf", ".docx", ".doc", ".txt"}:
            extension = ".pdf"
        safe_file_name = f"resume{extension}"
        storage_key = f"resumes/{candidate_id}/{safe_file_name}"
        try:
            reference = self.storage.write_bytes(storage_key, file_content)
        except Exception as exc:
            raise ResumeFetchError(f"Failed to store resume: {str(exc)}") from exc

        logger.info("Saved %s bytes for candidate %s", len(file_content), candidate_id)
        return reference, safe_file_name

    def update_candidate_resume_url(
        self,
        candidate_id: str,
        resume_url: str,
        resume_file_name: str,
    ) -> None:
        """Update candidate record with resume URL and metadata."""
        candidate = self.candidate_repository.get_by_id(candidate_id)
        if not candidate:
            raise ResumeFetchError(f"Candidate {candidate_id} not found")

        candidate.resume_url = resume_url
        candidate.resume_file_name = resume_file_name
        candidate.resume_last_fetched_at = datetime.now(UTC)

        self.candidate_repository.save(candidate)
        logger.debug(f"Updated resume URL for candidate {candidate_id}: {resume_url}")

    def delete_candidate_resumes(self, candidate_id: str) -> None:
        """Delete resume folder for a candidate when candidate is deleted."""
        try:
            self.storage.delete_prefix(f"resumes/{candidate_id}")
            logger.info("Deleted stored resumes for candidate %s", candidate_id)
        except Exception as exc:
            logger.error(f"Failed to delete resume folder for candidate {candidate_id}: {str(exc)}", exc_info=True)
            # Don't raise - deletion of resumes should not block candidate deletion
