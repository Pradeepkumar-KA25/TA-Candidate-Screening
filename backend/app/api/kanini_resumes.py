"""
Kanini Resume API endpoints - Upload, parse, render, download resumes
"""

import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Body,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db_session
from app.core.dependencies import get_current_recruiter
from app.core.dependencies import get_activity_log_repository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.models.user import User
from app.repositories.kanini_resume_repository import (
    KaniniResumeRepository,
    KaniniUserTemplateRepository,
)
from app.services.kanini_resume_models import KaniniResumeData
from app.services.kanini_resume_renderer import KaniniResumeRenderer
from app.services.ollama_service import get_model_options
from app.services.resume_ai_pipeline import parse_resume_completely
from app.services.kanini_resume_parser import parse_resume
from app.repositories.company_sector_repository import CompanySectorRepository
from app.services.company_sector_service import CompanySectorService
from app.core.config import settings
from app.models.template_spec import TemplateSpec
from app.services.template_spec_renderer import (
    render_docx as render_template_spec_docx,
    render_html as render_template_spec_html,
    render_pdf as render_template_spec_pdf,
)
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(tags=["kanini_resume"])

BUILTIN_TEMPLATES = {
    "template1": {
        "name": "Kanini Format 1",
        "description": "Professional Kanini Resume Format 1",
        "category": "builtin",
    },
    "template2": {
        "name": "Kanini Format 2 (Deloitte)",
        "description": "Deloitte-style Kanini Resume Format 2",
        "category": "builtin",
    },
}


# ============================================================================
# RESUME UPLOAD & PARSING
# ============================================================================


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    llm_model: str = Form(default="auto"),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
):
    """Upload and parse a resume (PDF or DOCX)."""
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".pdf", ".docx", ".doc"]:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail="Uploaded resume is empty")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

        # The parser accepts a path, so use a temporary file and remove it immediately.
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)
        try:
            parsed_data = await run_in_threadpool(
                parse_resume,
                str(temporary_path),
                file_ext[1:],
            )
        finally:
            temporary_path.unlink(missing_ok=True)

        resume_id = uuid.uuid4()
        repo = KaniniResumeRepository(db)
        resume = repo.create(
            id=resume_id,
            user_id=current_recruiter.id,
            filename=file.filename,
            parsed_data=parsed_data,
            extraction_status="completed",
            extraction_progress=100,
            extraction_model="deterministic",
        )
        activity_log_repository.create(
            actor_id=current_recruiter.id,
            action_type="resume_uploaded",
            description="Uploaded and extracted a resume",
            entity_type="resume",
            entity_id=resume.id,
            metadata={"filename": resume.filename, "extraction_model": "deterministic"},
        )

        return {
            "resume_id": str(resume.id),
            "filename": resume.filename,
            "parsed_data": resume.parsed_data,
            "llm_requested": llm_model,
            "llm_used": "deterministic",
            "extraction_status": resume.extraction_status,
            "extraction_progress": resume.extraction_progress,
            "message": "Resume uploaded and extracted successfully",
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/llm-models")
async def get_llm_models(
    current_recruiter: User = Depends(get_current_recruiter),
):
    return {"models": get_model_options()}


# ============================================================================
# RESUME RETRIEVAL & MANAGEMENT
# ============================================================================


@router.get("/resumes")
async def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """List all uploaded resumes for current user."""
    repo = KaniniResumeRepository(db)
    resumes = repo.list_by_user(current_recruiter.id, skip=skip, limit=limit)
    
    return {
        "total": len(resumes),
        "resumes": [
            {
                "id": str(resume.id),
                "filename": resume.filename,
                "extraction_status": resume.extraction_status,
                "extraction_progress": resume.extraction_progress,
                "created_at": resume.created_at.isoformat(),
                "updated_at": resume.updated_at.isoformat(),
            }
            for resume in resumes
        ],
    }


@router.get("/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Get a specific resume."""
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    repo = KaniniResumeRepository(db)
    resume = repo.get_by_id(resume_uuid, current_recruiter.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.extraction_status in {"pending", "processing"}:
        resume = repo.update_extraction(
            resume.id,
            status="completed",
            progress=100,
            error=None,
        ) or resume

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    if resume.parsed_data and 'experience' in resume.parsed_data:
        exp_count = len(resume.parsed_data['experience'])
        logger.info(f"Resume {resume_id}: Returning {exp_count} experiences")
        for i, exp in enumerate(resume.parsed_data['experience']):
            has_title = bool(exp.get('title'))
            logger.info(f"  Experience {i+1}: title={has_title}, company={exp.get('company', 'N/A')}")

    return {
        "id": str(resume.id),
        "filename": resume.filename,
        "parsed_data": resume.parsed_data,
        "extraction_status": resume.extraction_status,
        "extraction_progress": resume.extraction_progress,
        "extraction_error": resume.extraction_error,
        "extraction_model": resume.extraction_model,
        "created_at": resume.created_at.isoformat(),
    }


@router.post("/resumes/{resume_id}/extract")
async def retry_resume_extraction(
    resume_id: str,
    llm_model: str = Form(default="auto"),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
    storage: StorageBackend = Depends(get_storage_backend),
):
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid resume ID") from exc
    repository = KaniniResumeRepository(db)
    resume = repository.get_by_id(resume_uuid, current_recruiter.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.source_reference:
        raise HTTPException(status_code=409, detail="Uploaded source is no longer available")
    with storage.materialize(resume.source_reference) as source_path:
        parsed_data, model_used = await run_in_threadpool(
            parse_resume_completely,
            str(source_path),
            resume.source_file_type,
            llm_model,
        )
    repository.update_extraction(
        resume.id,
        status="completed",
        progress=100,
        parsed_data=parsed_data,
        model=model_used,
        error=None,
    )
    storage.delete_prefix(f"resume-jobs/{resume.id}")
    resume.source_reference = None
    resume.source_file_type = None
    db.commit()
    return {
        "resume_id": resume_id,
        "parsed_data": parsed_data,
        "extraction_status": "completed",
        "extraction_progress": 100,
        "extraction_model": model_used,
    }


@router.put("/resumes/{resume_id}")
async def update_resume(
    resume_id: str,
    request_body: dict = Body(...),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Update resume parsed data."""
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    # Extract parsed_data from request body
    parsed_data = request_body.get("parsed_data") if isinstance(request_body, dict) else request_body
    
    if not parsed_data:
        raise HTTPException(status_code=400, detail="parsed_data is required")

    repo = KaniniResumeRepository(db)
    resume = repo.update(resume_uuid, current_recruiter.id, parsed_data)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "id": str(resume.id),
        "message": "Resume updated successfully",
    }


@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
    storage: StorageBackend = Depends(get_storage_backend),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
):
    """Delete a resume."""
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    repo = KaniniResumeRepository(db)
    resume = repo.get_by_id(resume_uuid, current_recruiter.id)
    if resume and resume.source_reference:
        storage.delete_prefix(f"resume-jobs/{resume_uuid}")
    if not repo.delete(resume_uuid, current_recruiter.id):
        raise HTTPException(status_code=404, detail="Resume not found")

    activity_log_repository.create(
        actor_id=current_recruiter.id,
        action_type="resume_deleted",
        description="Deleted generated resume",
        entity_type="resume",
        entity_id=resume_uuid,
    )

    return {"message": "Resume deleted successfully"}


# ============================================================================
# TEMPLATES
# ============================================================================


@router.get("/templates")
async def list_templates(
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """List all available templates (builtin + user-created)."""
    # Builtin templates
    templates = [
        {
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "category": "builtin",
        }
        for k, v in BUILTIN_TEMPLATES.items()
    ]

    # User-created templates
    user_template_repo = KaniniUserTemplateRepository(db)
    user_templates = user_template_repo.list_by_user(current_recruiter.id)
    
    templates.extend([
        {
            "id": str(t.id),
            "name": t.template_name,
            "description": t.description,
            "category": "user",
        }
        for t in user_templates
    ])

    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Get template details."""
    # Check builtin templates
    if template_id in BUILTIN_TEMPLATES:
        return {
            "id": template_id,
            **BUILTIN_TEMPLATES[template_id],
        }

    # Check user templates
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    user_template_repo = KaniniUserTemplateRepository(db)
    template = user_template_repo.get_by_id(template_uuid, current_recruiter.id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.template_name,
        "description": template.description,
        "category": "user",
        "template_spec": template.template_spec,
    }


# ============================================================================
# RENDERING & DOWNLOAD (Placeholder - will implement with actual renderers)
# ============================================================================


@router.post("/render")
async def render_resume(
    resume_id: str = Form(...),
    template_id: str = Form(...),
    format: str = Form("html"),  # 'html', 'docx', 'pdf'
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
    activity_log_repository: ActivityLogRepository = Depends(get_activity_log_repository),
):
    """Render resume in specified template and format."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Validate inputs
        if not format or format not in ["html", "docx", "pdf"]:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'html', 'docx', or 'pdf'")
        
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid resume ID format")

        # Get resume from database
        try:
            repo = KaniniResumeRepository(db)
            resume = repo.get_by_id(resume_uuid, current_recruiter.id)
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching resume from database: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch resume from database")

        # Validate parsed_data exists
        if not resume.parsed_data:
            raise HTTPException(status_code=400, detail="Resume has no parsed data")

        # Render in memory. Generated downloads are not retained on the server.
        try:
            user_template = None
            if template_id not in BUILTIN_TEMPLATES:
                try:
                    user_template = KaniniUserTemplateRepository(db).get_by_id(
                        uuid.UUID(template_id), current_recruiter.id
                    )
                except ValueError:
                    pass
                if not user_template:
                    raise HTTPException(status_code=404, detail="Template not found")
            template_spec = TemplateSpec.model_validate(user_template.template_spec) if user_template else None

            if template_spec and format == "html":
                content = render_template_spec_html(resume.parsed_data, template_spec).encode("utf-8")
            elif template_spec and format == "docx":
                content = render_template_spec_docx(resume.parsed_data, template_spec)
            elif template_spec and format == "pdf":
                content = render_template_spec_pdf(resume.parsed_data, template_spec)
            elif format == "html":
                content = KaniniResumeRenderer.render_html(resume.parsed_data, template_id)
                if not isinstance(content, str):
                    raise ValueError(f"Expected HTML string, got {type(content)}")
                content = content.encode("utf-8")
            elif format == "docx":
                content = KaniniResumeRenderer.render_docx(resume.parsed_data, template_id)
                if not isinstance(content, bytes):
                    raise ValueError(f"Expected DOCX bytes, got {type(content)}")
            elif format == "pdf":
                content = await KaniniResumeRenderer.render_pdf(resume.parsed_data, template_id)
                if not isinstance(content, bytes):
                    raise ValueError(f"Expected PDF bytes, got {type(content)}")
                # Verify PDF has valid header
                if not content.startswith(b'%PDF'):
                    raise ValueError("PDF generation produced invalid output")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error rendering resume to {format}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to render {format}: {str(e)}")

        candidate_name = resume.parsed_data.get("contact", {}).get("name", "Resume") if isinstance(resume.parsed_data, dict) else "Resume"
        candidate_name_clean = re.sub(r"[^a-zA-Z0-9]+", "_", str(candidate_name or "").strip()).strip("_")
        candidate_name_clean = "_".join(word.capitalize() for word in candidate_name_clean.split("_")) or "Resume"
        format_num = "2" if template_id == "template2" else "1"
        media_types = {
            "html": "text/html; charset=utf-8",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
        }
        filename = f"{candidate_name_clean}_KANINI_Format_{format_num}.{format}"
        activity_log_repository.create(
            actor_id=current_recruiter.id,
            action_type="resume_rendered",
            description=f"Rendered resume as {format.upper()}",
            entity_type="resume",
            entity_id=resume_uuid,
            metadata={"template_id": template_id, "format": format},
        )
        return Response(
            content=content,
            media_type=media_types[format],
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in render_resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during rendering")


@router.get("/preview/{resume_id}/{template_id}")
async def preview_resume(
    resume_id: str,
    template_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Get HTML preview of resume with template."""
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    # Get resume
    repo = KaniniResumeRepository(db)
    resume = repo.get_by_id(resume_uuid, current_recruiter.id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if template_id in BUILTIN_TEMPLATES:
        html_content = KaniniResumeRenderer.render_html(resume.parsed_data, template_id)
    else:
        try:
            template_uuid = uuid.UUID(template_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid template ID") from exc
        template = KaniniUserTemplateRepository(db).get_by_id(template_uuid, current_recruiter.id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        html_content = render_template_spec_html(
            resume.parsed_data,
            TemplateSpec.model_validate(template.template_spec),
        )
    
    return {
        "resume_id": resume_id,
        "template_id": template_id,
        "html": html_content,
        "preview_html": html_content,  # For compatibility
    }


# ============================================================================
# CUSTOM TEMPLATES
# ============================================================================


@router.post("/templates")
async def save_template(
    template_name: str = Form(...),
    description: str = Form(...),
    template_spec: dict = Form(...),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Save a custom template."""
    repo = KaniniUserTemplateRepository(db)
    template = repo.create(
        user_id=current_recruiter.id,
        template_name=template_name,
        description=description,
        template_spec=template_spec,
    )

    return {
        "id": str(template.id),
        "message": "Template saved successfully",
    }


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template_name: str = Form(...),
    description: str = Form(...),
    template_spec: dict = Form(...),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Update a custom template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    repo = KaniniUserTemplateRepository(db)
    template = repo.update(
        template_uuid,
        current_recruiter.id,
        template_name,
        description,
        template_spec,
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template updated successfully"}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Delete a custom template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    repo = KaniniUserTemplateRepository(db)
    if not repo.delete(template_uuid, current_recruiter.id):
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}
