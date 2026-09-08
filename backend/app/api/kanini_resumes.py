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

from app.core.database import get_db_session
from app.core.dependencies import get_current_recruiter
from app.models.user import User
from app.repositories.kanini_resume_repository import (
    KaniniResumeRepository,
    KaniniUserTemplateRepository,
)
from app.services.kanini_resume_parser import parse_resume
from app.services.kanini_resume_models import KaniniResumeData
from app.services.kanini_resume_renderer import KaniniResumeRenderer

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

        # The parser accepts a path, so use a temporary file and remove it immediately.
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)
        try:
            parsed_data = parse_resume(str(temporary_path), file_ext[1:])
        finally:
            temporary_path.unlink(missing_ok=True)

        # Save to database
        repo = KaniniResumeRepository(db)
        resume = repo.create(
            user_id=current_recruiter.id,
            filename=file.filename,
            parsed_data=parsed_data,
        )

        return {
            "resume_id": str(resume.id),
            "filename": resume.filename,
            "parsed_data": resume.parsed_data,
            "llm_model": llm_model,
            "message": "Resume uploaded and parsed successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/llm-models")
async def get_llm_models():
    """Get available LLM models for resume parsing."""
    return {
        "models": [
            {"label": "Auto (default)", "value": "auto", "available": True},
            {"label": "Qwen3 32B", "value": "ollama:qwen3:32b", "available": True, "provider": "ollama", "provider_label": "Ollama"},
            {"label": "Qwen3 14B", "value": "ollama:qwen3:14b", "available": True, "provider": "ollama", "provider_label": "Ollama"},
            {"label": "Llama 3.3 70B", "value": "ollama:llama3.3:70b", "available": True, "provider": "ollama", "provider_label": "Ollama"},
            {"label": "Devstral", "value": "ollama:devstral", "available": True, "provider": "ollama", "provider_label": "Ollama"},
            {"label": "Gemma 3 27B", "value": "ollama:gemma3:27b", "available": True, "provider": "ollama", "provider_label": "Ollama"},
            {"label": "Mistral Small 3.2", "value": "ollama:mistral-small3.2", "available": True, "provider": "ollama", "provider_label": "Ollama"},
        ]
    }


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

    return {
        "id": str(resume.id),
        "filename": resume.filename,
        "parsed_data": resume.parsed_data,
        "created_at": resume.created_at.isoformat(),
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
):
    """Delete a resume."""
    try:
        resume_uuid = uuid.UUID(resume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resume ID")

    repo = KaniniResumeRepository(db)
    if not repo.delete(resume_uuid, current_recruiter.id):
        raise HTTPException(status_code=404, detail="Resume not found")

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
            if format == "html":
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

    # Render HTML preview
    html_content = KaniniResumeRenderer.render_html(resume.parsed_data, template_id)
    
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
