"""
Template API Endpoints - Create, manage, and use custom templates
"""

import uuid
import json
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.dependencies import get_current_recruiter
from app.models.user import User
from app.models.template_spec import TemplateSpec
from app.repositories.template_repository import KaniniUserTemplateRepository
from app.services.kanini_resume_parser import parse_resume
from app.services.kanini_resume_renderer import KaniniResumeRenderer
from app.services.template_generation_service import TemplateGenerationError, generate_template_spec
from app.services.template_spec_renderer import render_html as render_template_spec_html
from app.storage import StorageBackend, get_storage_backend
from app.services.ollama_service import OllamaUnavailableError
from starlette.concurrency import run_in_threadpool

router = APIRouter(tags=["templates"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _draft_prefix(user_id: uuid.UUID, draft_id: str) -> str:
    return f"template-drafts/{user_id}/{draft_id}"


# ============================================================================
# TEMPLATE CREATION FLOW
# ============================================================================


@router.post("/drafts")
async def create_template_draft(
    file: UploadFile = File(...),
    current_recruiter: User = Depends(get_current_recruiter),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Step 1: Upload a sample PDF to create a template draft.
    Extracts resume data from the PDF for template generation.
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sample resume must be a PDF file")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded PDF is empty")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    draft_id = str(uuid.uuid4())
    draft_prefix = _draft_prefix(current_recruiter.id, draft_id)
    
    try:
        original_reference = storage.write_bytes(f"{draft_prefix}/original.pdf", content)
        with storage.materialize(original_reference) as pdf_path:
            parsed_data = parse_resume(str(pdf_path), "pdf")
        
        if not parsed_data:
            raise ValueError("Could not extract readable data from the PDF")

        # Save extracted data
        draft_data = {
            "draft_id": draft_id,
            "status": "uploaded",
            "filename": filename,
            "extracted_data": parsed_data,
        }
        storage.write_bytes(
            f"{draft_prefix}/extracted_data.json",
            json.dumps(draft_data, ensure_ascii=False, indent=2).encode("utf-8"),
        )

        return {
            "draft_id": draft_id,
            "status": "uploaded",
            "filename": filename,
            "extracted_data": parsed_data,
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template draft: {str(e)}")


@router.post("/drafts/{draft_id}/generate")
async def generate_template_from_draft(
    draft_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Step 2: Generate a template specification from the draft.
    Currently uses a default template spec (can be enhanced with AI).
    """
    try:
        normalized_draft_id = str(uuid.UUID(draft_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Template draft not found")

    draft_prefix = _draft_prefix(current_recruiter.id, normalized_draft_id)
    extracted_reference = f"{draft_prefix}/extracted_data.json"
    
    if not storage.exists(extracted_reference):
        raise HTTPException(status_code=404, detail="Template draft not found")

    try:
        draft_data = json.loads(storage.read_bytes(extracted_reference).decode("utf-8"))
        extracted_data = draft_data.get("extracted_data", {})

        template_spec = await run_in_threadpool(generate_template_spec, extracted_data)
        
        # Save template spec
        storage.write_bytes(
            f"{draft_prefix}/template_spec.json",
            json.dumps(template_spec.model_dump(), indent=2).encode("utf-8"),
        )

        # Generate preview HTML using the template spec
        preview_html = render_template_spec_html(extracted_data, template_spec)
        storage.write_bytes(f"{draft_prefix}/preview.html", preview_html.encode("utf-8"))

        return {
            "draft_id": normalized_draft_id,
            "status": "generated",
            "filename": draft_data.get("filename", "sample.pdf"),
            "extracted_data": extracted_data,
            "template_spec": template_spec.model_dump(),
            "preview_html": preview_html,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Template draft data is invalid")
    except OllamaUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except TemplateGenerationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")


@router.post("/drafts/{draft_id}/save")
async def save_template_from_draft(
    draft_id: str,
    name: str = Form(...),
    description: str = Form(""),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Step 3: Save the generated template draft as a reusable template.
    Template becomes available for use on future resumes.
    """
    try:
        normalized_draft_id = str(uuid.UUID(draft_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Template draft not found")

    # Validate name
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Template name is required")
    if len(name) > 100:
        raise HTTPException(status_code=400, detail="Template name is too long (max 100 characters)")

    draft_prefix = _draft_prefix(current_recruiter.id, normalized_draft_id)
    spec_reference = f"{draft_prefix}/template_spec.json"
    if not storage.exists(spec_reference):
        raise HTTPException(status_code=404, detail="Generated template draft not found")

    try:
        # Load and validate spec
        spec_data = json.loads(storage.read_bytes(spec_reference).decode("utf-8"))
        template_spec = TemplateSpec(**spec_data)

        # Save to database
        repo = KaniniUserTemplateRepository(db)
        template = repo.create(
            user_id=current_recruiter.id,
            name=name.strip(),
            description=description.strip(),
            template_spec=template_spec.model_dump(),
        )

        storage.delete_prefix(draft_prefix)

        return {
            "id": str(template.id),
            "name": template.template_name,
            "description": template.description,
            "template_spec": template.template_spec,
            "created_at": template.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save template: {str(e)}")


# ============================================================================
# TEMPLATE MANAGEMENT
# ============================================================================


@router.get("/")
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """List all templates for the current user"""
    repo = KaniniUserTemplateRepository(db)
    templates = repo.list_by_user(current_recruiter.id, skip=skip, limit=limit)
    
    return {
        "data": [
            {
                "id": str(t.id),
                "name": t.template_name,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in templates
        ],
        "total": len(templates),
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Get a specific template by ID"""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    repo = KaniniUserTemplateRepository(db)
    template = repo.get_by_id(template_uuid, current_recruiter.id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.template_name,
        "description": template.description,
        "template_spec": template.template_spec,
        "created_at": template.created_at.isoformat(),
    }


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Update template metadata (name and description)"""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    if name is not None and (not name.strip() or len(name) > 100):
        raise HTTPException(status_code=400, detail="Invalid template name")

    repo = KaniniUserTemplateRepository(db)
    template = repo.update(
        template_uuid,
        current_recruiter.id,
        name=name.strip() if name else None,
        description=description.strip() if description else None,
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.template_name,
        "description": template.description,
        "created_at": template.created_at.isoformat(),
    }


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db_session),
):
    """Delete a template"""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    repo = KaniniUserTemplateRepository(db)
    if not repo.delete(template_uuid, current_recruiter.id):
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}
