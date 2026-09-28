from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

from app.services.kanini_resume_models import KaniniResumeData
from app.core.config import settings
from app.services.kanini_resume_parser import extract_text, parse_resume_text
from app.services.ollama_service import parse_resume_with_ollama


logger = logging.getLogger(__name__)


def parse_resume_completely(
    file_path: str,
    file_type: str,
    selected_model: str | None,
    progress_callback: Callable[[int], None] | None = None,
) -> tuple[dict[str, Any], str]:
    raw_text = extract_text(file_path, file_type)
    if not raw_text.strip():
        raise ValueError("Could not extract readable text from the resume")
    deterministic = parse_resume_text(raw_text)

    if progress_callback:
        progress_callback(20)
    try:
        ai_result, model = parse_resume_with_ollama(
            raw_text,
            selected_model,
            timeout_seconds=settings.ollama_background_chunk_timeout_seconds,
        )
        result = _merge_resume_sections(ai_result, deterministic)
        used_model = f"ollama:{model}"
    except Exception as exc:
        logger.warning("Complete Ollama extraction failed; preserving deterministic result: %s", exc)
        result = _merge_resume_sections({}, deterministic)
        used_model = "deterministic"

    if progress_callback:
        progress_callback(90)
    return KaniniResumeData.model_validate(result).model_dump(), used_model


def parse_resume_with_fallback(
    file_path: str,
    file_type: str,
    selected_model: str | None,
) -> tuple[dict[str, Any], str]:
    raw_text = extract_text(file_path, file_type)
    if not raw_text.strip():
        raise ValueError("Could not extract readable text from the resume")

    deterministic = parse_resume_text(raw_text)
    try:
        ai_result, model = parse_resume_with_ollama(
            raw_text,
            selected_model,
            timeout_seconds=settings.ollama_upload_timeout_seconds,
        )
        result = _merge_resume_sections(ai_result, deterministic)
        used_model = f"ollama:{model}"
    except Exception as exc:
        logger.warning("Ollama resume extraction failed; using deterministic parser: %s", exc)
        result = _merge_resume_sections({}, deterministic)
        used_model = "deterministic"

    validated = KaniniResumeData.model_validate(result)
    return validated.model_dump(), used_model


def _merge_resume_sections(ai_data: dict[str, Any], deterministic_data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(deterministic_data)
    merged.update({key: value for key, value in ai_data.items() if value not in (None, "", [], {})})
    merged["experience"] = _merge_experience_sections(
        deterministic_data.get("experience"),
        ai_data.get("experience"),
    )
    nested_projects = [
        project
        for experience in merged["experience"]
        for project in experience.get("projects", [])
        if isinstance(project, dict)
    ]
    merged["projects"] = _merge_project_sections(
        deterministic_data.get("projects"),
        [*(ai_data.get("projects") or []), *nested_projects],
    )
    if _skills_score(deterministic_data.get("skills")) > _skills_score(ai_data.get("skills")):
        merged["skills"] = deterministic_data.get("skills", {})
    if _summary_score(deterministic_data.get("summary")) > _summary_score(ai_data.get("summary")):
        merged["summary"] = deterministic_data.get("summary", "")

    ai_contact = ai_data.get("contact") if isinstance(ai_data.get("contact"), dict) else {}
    deterministic_contact = (
        deterministic_data.get("contact") if isinstance(deterministic_data.get("contact"), dict) else {}
    )
    merged["contact"] = {
        key: ai_contact.get(key) or deterministic_contact.get(key) or ""
        for key in ("name", "email", "phone", "location", "linkedin", "github")
    }
    for field in ("certifications", "achievements"):
        values = [*(deterministic_data.get(field) or []), *(ai_data.get(field) or [])]
        merged[field] = list(dict.fromkeys(value for value in values if value))
    if not ai_data.get("education"):
        merged["education"] = deterministic_data.get("education", [])
    return merged


def _normalised_identity(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _valid_experience(value: dict[str, Any]) -> bool:
    title = str(value.get("title") or "").strip()
    company = str(value.get("company") or value.get("company_name") or "").strip()
    dates = str(value.get("dates") or "").strip()
    invalid_labels = {"company", "companyname", "designation", "role", "position", "duration"}
    if _normalised_identity(title) in invalid_labels or _normalised_identity(company) in invalid_labels:
        return False
    return bool((company and title) or (dates and (company or title)))


def _merge_experience_sections(deterministic_values: Any, ai_values: Any) -> list[dict[str, Any]]:
    deterministic = [
        dict(item) for item in deterministic_values or []
        if isinstance(item, dict) and _valid_experience(item)
    ]
    ai_items = [
        dict(item) for item in ai_values or []
        if isinstance(item, dict) and _valid_experience(item)
    ]
    merged = deterministic
    for ai_item in ai_items:
        ai_company = _normalised_identity(ai_item.get("company") or ai_item.get("company_name"))
        ai_title = _normalised_identity(ai_item.get("title"))
        ai_dates = _normalised_identity(ai_item.get("dates"))
        match = next(
            (
                item
                for item in merged
                if (
                    ai_company
                    and ai_title
                    and ai_company == _normalised_identity(item.get("company") or item.get("company_name"))
                    and ai_title == _normalised_identity(item.get("title"))
                )
                or (
                    ai_dates
                    and ai_dates == _normalised_identity(item.get("dates"))
                    and (
                        (ai_company and ai_company == _normalised_identity(item.get("company") or item.get("company_name")))
                        or (ai_title and ai_title == _normalised_identity(item.get("title")))
                    )
                )
            ),
            None,
        )
        if match is None:
            merged.append(ai_item)
            continue
        for field in ("title", "company", "company_name", "location", "dates"):
            if ai_item.get(field):
                match[field] = ai_item[field]
        responsibilities = [*match.get("responsibilities", []), *ai_item.get("responsibilities", [])]
        match["responsibilities"] = list(dict.fromkeys(value for value in responsibilities if value))
        if ai_item.get("projects"):
            match["projects"] = ai_item["projects"]
    return merged


def _project_key(value: dict[str, Any]) -> str:
    name = re.sub(
        r"^project(?:name)?(?:[ivx]+|\d+)?",
        "",
        _normalised_identity(value.get("name")),
    )
    return name or _normalised_identity(value.get("name"))


def _valid_project(value: dict[str, Any]) -> bool:
    if not str(value.get("name") or "").strip():
        return False
    return any(
        value.get(field)
        for field in ("client", "duration", "role", "description", "technologies", "responsibilities")
    )


def _merge_project_sections(deterministic_values: Any, ai_values: Any) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for raw_value in [*(deterministic_values or []), *(ai_values or [])]:
        if not isinstance(raw_value, dict) or not _valid_project(raw_value):
            continue
        value = dict(raw_value)
        key = _project_key(value)
        match = next((item for item in merged if key and _project_key(item) == key), None)
        if match is None:
            merged.append(value)
            continue
        for field in ("name", "client", "duration", "role", "description"):
            if value.get(field) and (not match.get(field) or len(str(value[field])) > len(str(match[field]))):
                match[field] = value[field]
        for field in ("technologies", "responsibilities"):
            combined = [*match.get(field, []), *value.get(field, [])]
            match[field] = list(dict.fromkeys(item for item in combined if item))
    return merged


def _skills_score(value: Any) -> int:
    if not isinstance(value, dict):
        return 0
    score = 0
    noise = re.compile(r"\b(?:company|designation|duration|responsibilities|project\s+[ivx]+)\b", re.I)
    for items in value.values():
        if not isinstance(items, list):
            continue
        for item in items:
            text = str(item or "").strip()
            score += 1 if text and len(text.split()) <= 6 and not noise.search(text) else -2
    return score


def _summary_score(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    score = min(len(text.split()), 40)
    if re.search(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}|company\s+name|designation|duration", text, re.I):
        score -= 10
    return max(score, 0)