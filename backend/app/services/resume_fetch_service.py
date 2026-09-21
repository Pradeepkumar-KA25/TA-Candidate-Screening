"""Resume Fetch Service - Download and save candidate resumes from Zoho Recruit."""
from __future__ import annotations

from pathlib import Path
import logging
from datetime import UTC, datetime

from app.core.config import settings
from app.integrations.zoho_recruit import ZohoRecruitClient, ZohoRecruitClientError
from app.repositories.candidate_repository import CandidateRepository

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
    ):
        self.candidate_repository = candidate_repository
        self.zoho_recruit_client = zoho_recruit_client
        self.resume_storage_path = Path(settings.zoho_resume_storage_path)

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
            resume_url, saved_file_name = self._save_resume_locally(
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

    def _save_resume_locally(
        self,
        candidate_id: str,
        file_name: str,
        file_content: bytes,
    ) -> tuple[str, str]:
        """Save resume file to local storage."""
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not file_content:
            raise ResumeFetchError("Downloaded file is empty")

        logger.info(f"Resume content size: {len(file_content)} bytes")
        logger.info(f"Resume file name: {file_name}")
        logger.info(f"First 20 bytes (hex): {file_content[:20].hex()}")

        # Get storage path - remove 'backend/' prefix if present to avoid double path
        storage_path = str(self.resume_storage_path)
        if storage_path.startswith("backend/"):
            storage_path = storage_path[8:]  # Remove "backend/" prefix
        
        resume_storage = Path(storage_path)
        
        # If relative path, make it absolute from current working directory
        if not resume_storage.is_absolute():
            resume_storage = Path.cwd() / resume_storage
        
        logger.info(f"Resume storage path (absolute): {resume_storage}")
        
        candidate_dir = resume_storage / str(candidate_id)
        
        logger.info(f"Creating directory: {candidate_dir}")
        try:
            candidate_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            error = f"Failed to create resume directory {candidate_dir}: {str(exc)}"
            logger.error(error)
            raise ResumeFetchError(error)

        # Clean file name - keep extension, sanitize name
        file_ext = Path(file_name).suffix.lower() or ".pdf"
        safe_file_name = f"resume{file_ext}"

        # Save file
        file_path = candidate_dir / safe_file_name
        logger.info(f"Saving resume to: {file_path}")
        
        try:
            with open(str(file_path), 'wb') as f:
                bytes_written = f.write(file_content)
                logger.info(f"Wrote {bytes_written} bytes to {file_path}")
            
            # Verify file was written
            if not file_path.exists():
                raise ResumeFetchError(f"File was not saved: {file_path}")
            
            size = file_path.stat().st_size
            logger.info(f"Successfully saved {size} bytes to {file_path}")
            
            # Verify file can be read back
            with open(str(file_path), 'rb') as f:
                verify_content = f.read(20)
                logger.info(f"Verification read first 20 bytes (hex): {verify_content.hex()}")
        except OSError as exc:
            error = f"Failed to write resume file {file_path}: {str(exc)}"
            logger.error(error)
            raise ResumeFetchError(error)

        # Return relative URL path and filename
        resume_url = f"uploads/resumes/{candidate_id}/{safe_file_name}"
        logger.info(f"Resume URL: {resume_url}")
        return resume_url, safe_file_name

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
            # Get storage path
            storage_path = str(self.resume_storage_path)
            if storage_path.startswith("backend/"):
                storage_path = storage_path[8:]  # Remove "backend/" prefix
            
            resume_storage = Path(storage_path)
            
            # If relative path, make it absolute from current working directory
            if not resume_storage.is_absolute():
                resume_storage = Path.cwd() / resume_storage
            
            candidate_dir = resume_storage / str(candidate_id)
            
            # Delete directory if it exists
            if candidate_dir.exists():
                import shutil
                shutil.rmtree(candidate_dir)
                logger.info(f"Deleted resume folder for candidate {candidate_id}: {candidate_dir}")
            else:
                logger.debug(f"Resume folder not found for candidate {candidate_id}: {candidate_dir}")
        
        except Exception as exc:
            logger.error(f"Failed to delete resume folder for candidate {candidate_id}: {str(exc)}", exc_info=True)
            # Don't raise - deletion of resumes should not block candidate deletion
