import json

import pytest

from app.core.config import settings
from app.services import ollama_service
from app.services.template_generation_service import TemplateGenerationError, generate_template_spec
from app.services.template_spec_renderer import render_docx, render_html, render_pdf


VALID_SPEC = {
    "page": {"size": "A4", "orientation": "portrait", "margin_inches": 0.65},
    "typography": {"font_family": "Calibri", "base_size_pt": 10, "heading_size_pt": 14},
    "colors": {"text": "#1F2937", "accent": "#0072B4", "muted": "#64748B"},
    "header": {"layout": "left", "contact_layout": "inline", "show_divider": True},
    "layout": {"columns": 1, "sidebar_position": "none", "section_alignment": "left"},
    "sections": ["summary", "experience", "projects"],
    "spacing": {"section_gap_pt": 12, "line_height": 1.35, "divider_style": "accent", "skill_style": "tags"},
}


def test_generate_and_render_template_spec(monkeypatch) -> None:
    monkeypatch.setattr(ollama_service.settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(ollama_service.settings, "ollama_model", "llama3.1")
    monkeypatch.setattr(
        "app.services.template_generation_service.generate_json",
        lambda *_args, **_kwargs: (VALID_SPEC, "llama3.1"),
    )
    spec = generate_template_spec({"summary": "Engineer"})
    resume = {
        "contact": {"name": "Asha Sharma"},
        "summary": "Engineer",
        "experience": [{"title": "Developer", "company": "Acme"}],
        "projects": [{"name": "Portal", "description": "Built portal"}],
    }

    assert "Asha Sharma" in render_html(resume, spec)
    assert render_docx(resume, spec).startswith(b"PK")
    assert render_pdf(resume, spec).startswith(b"%PDF")


def test_generated_template_rejects_unsafe_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.template_generation_service.generate_json",
        lambda *_args, **_kwargs: ({**VALID_SPEC, "script": "alert(1)"}, "llama3.1"),
    )

    with pytest.raises(TemplateGenerationError):
        generate_template_spec({})