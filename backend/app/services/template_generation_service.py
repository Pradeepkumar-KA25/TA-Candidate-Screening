from __future__ import annotations

from typing import Any

from app.models.template_spec import TemplateSpec


class TemplateGenerationError(RuntimeError):
    pass


def generate_template_spec(extracted_data: dict[str, Any]) -> TemplateSpec:
    """Build a valid template immediately from the uploaded resume structure.

    Template generation does not need semantic AI: the extracted section order and
    available content are sufficient to produce a reusable, safe layout.
    """
    section_order = (
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "achievements",
    )
    sections = [
        section
        for section in section_order
        if extracted_data.get(section)
    ] or ["summary"]

    try:
        return TemplateSpec.model_validate(
            {
                "page": {"size": "A4", "orientation": "portrait", "margin_inches": 0.65},
                "typography": {"font_family": "Calibri", "base_size_pt": 10, "heading_size_pt": 14},
                "colors": {"text": "#1F2937", "accent": "#0072B4", "muted": "#64748B"},
                "header": {"layout": "centered", "contact_layout": "inline", "show_divider": True},
                "layout": {"columns": 1, "sidebar_position": "none", "section_alignment": "left"},
                "sections": sections,
                "spacing": {"section_gap_pt": 12, "line_height": 1.35, "divider_style": "solid", "skill_style": "inline"},
            }
        )
    except ValueError as exc:
        raise TemplateGenerationError(f"Generated template specification is invalid: {exc}") from exc