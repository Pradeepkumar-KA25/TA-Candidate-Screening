from app.services.template_generation_service import generate_template_spec
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


def test_generate_and_render_template_spec() -> None:
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


def test_template_spec_uses_only_available_sections() -> None:
    spec = generate_template_spec({"experience": [{"title": "Developer"}], "projects": []})

    assert spec.sections == ["experience"]
    assert spec.layout.columns == 1
    assert spec.header.layout == "centered"