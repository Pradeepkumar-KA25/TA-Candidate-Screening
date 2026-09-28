from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.models.template_spec import TemplateSpec
from app.services.ollama_service import generate_json


class TemplateGenerationError(RuntimeError):
    pass


_PROMPT = """You design reusable professional resume templates.
Create a design specification inspired only by the sample's section organization and content structure.
Return only valid JSON matching this schema, with no markdown, HTML, CSS, JavaScript, URLs, assets, executable code, or resume content:
{
  "page":{"size":"A4","orientation":"portrait","margin_inches":0.65},
  "typography":{"font_family":"Calibri","base_size_pt":10,"heading_size_pt":14},
  "colors":{"text":"#1F2937","accent":"#0072B4","muted":"#64748B"},
  "header":{"layout":"centered","contact_layout":"inline","show_divider":true},
  "layout":{"columns":1,"sidebar_position":"none","section_alignment":"left"},
  "sections":["summary","skills","experience","projects","education","certifications","achievements"],
  "spacing":{"section_gap_pt":12,"line_height":1.35,"divider_style":"solid","skill_style":"inline"}
}
Use only fields and values accepted by the schema. Do not repeat sections. Include at least one section."""


def generate_template_spec(extracted_data: dict[str, Any]) -> TemplateSpec:
    prompt = f"{_PROMPT}\n\nSample resume structure:\n{json.dumps(extracted_data, ensure_ascii=False)[:14000]}"
    payload, _ = generate_json(prompt)
    try:
        return TemplateSpec.model_validate(payload)
    except ValidationError as exc:
        details = "; ".join(error["msg"] for error in exc.errors()[:3])
        raise TemplateGenerationError(f"Generated template specification is invalid: {details}") from exc