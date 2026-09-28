from __future__ import annotations

import logging
from uuid import UUID

from app.core.database import get_session_factory
from app.repositories.kanini_resume_repository import KaniniResumeRepository
from app.services.resume_ai_pipeline import parse_resume_completely
from app.storage import get_storage_backend


logger = logging.getLogger(__name__)


def process_resume_extraction_job(resume_id: UUID) -> None:
    session = get_session_factory()()
    repository = KaniniResumeRepository(session)
    storage = get_storage_backend()
    try:
        resume = repository.get_job(resume_id)
        if not resume or resume.extraction_status == "completed":
            return
        if not resume.source_reference or not resume.source_file_type:
            repository.update_extraction(
                resume_id,
                status="failed",
                progress=100,
                error="Uploaded source file is unavailable",
            )
            return

        selected_model = resume.extraction_model or "auto"
        repository.update_extraction(resume_id, status="processing", progress=10, error=None)

        def update_progress(progress: int) -> None:
            repository.update_extraction(
                resume_id,
                status="processing",
                progress=progress,
            )

        with storage.materialize(resume.source_reference) as source_path:
            parsed_data, model_used = parse_resume_completely(
                str(source_path),
                resume.source_file_type,
                selected_model,
                progress_callback=update_progress,
            )

        repository.update_extraction(
            resume_id,
            status="completed",
            progress=100,
            parsed_data=parsed_data,
            model=model_used,
            error=None,
        )
        storage.delete_prefix(f"resume-jobs/{resume_id}")
        completed = repository.get_job(resume_id)
        if completed:
            completed.source_reference = None
            completed.source_file_type = None
            session.commit()
    except BaseException as exc:
        session.rollback()
        logger.exception("Resume extraction job %s failed", resume_id)
        try:
            repository.update_extraction(
                resume_id,
                status="failed",
                progress=100,
                error=str(exc)[:1000],
            )
        except Exception:
            session.rollback()
    finally:
        session.close()