from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from app.core.config import settings


class OllamaUnavailableError(RuntimeError):
    pass


class OllamaResponseError(RuntimeError):
    pass


_RESUME_SYSTEM_PROMPT = """You are an expert resume parser. Read the entire resume carefully and extract every piece of information into the JSON structure below.

STRICT RULES:
- contact.name is the candidate's full name and must not be placed in summary.
- summary contains only professional narrative, never contact details, headings, skills, or bullets.
- skills is a dictionary of categories to arrays of atomic skills. Never include companies, roles, projects, durations, locations, labels, or sentences.
- experience is an array of employment records. Each record contains title, company, location, dates, responsibilities, and only the projects performed during that employment.
- Keep title and company in the correct fields. For table-like text, pair Company/Employer with company, Designation/Role/Position with title, and Duration/Period with dates.
- A project contains name, client, duration, role, description, technologies, and responsibilities. Keep client separate from the employer and project role separate from job title.
- Preserve each responsibility as one complete item. Do not merge unrelated bullets or invent missing details.
- education entries contain degree, institution, year, and gpa.
- certifications and achievements are arrays of strings.
- Top-level projects contains projects that cannot be reliably associated with one employment record. Do not duplicate nested projects there.
- Use an empty string for uncertain scalar values. Do not guess.

Return ONLY valid JSON with this exact shape and no markdown or explanation:
{
  "contact":{"name":"","email":"","phone":"","location":"","linkedin":"","github":""},
  "summary":"",
  "skills":{"Category":["skill1"]},
    "experience":[{"title":"","company":"","location":"","dates":"","responsibilities":[],"projects":[{"name":"","client":"","duration":"","role":"","description":"","technologies":[],"responsibilities":[]}]}],
  "education":[{"degree":"","institution":"","year":"","gpa":""}],
  "certifications":[],
    "projects":[{"name":"","client":"","duration":"","role":"","description":"","technologies":[],"responsibilities":[]}],
  "achievements":[]
}

Before returning, verify every experience title is a role, every company is an employer, no labels appear as values, projects are associated with the correct job when the resume provides that relationship, and skills contain only atomic skills."""


def _configured_model_names() -> list[str]:
    names = [item.strip() for item in settings.ollama_models.split(",") if item.strip()]
    if settings.ollama_model and settings.ollama_model not in names:
        names.append(settings.ollama_model)
    return names


def get_model_options() -> list[dict[str, Any]]:
    configured = bool(settings.ollama_base_url and settings.ollama_model)
    options: list[dict[str, Any]] = [
        {
            "label": "Auto (configured provider)",
            "value": "auto",
            "available": configured,
            "provider": "auto",
            "reason": "Ollama is not configured" if not configured else "",
        }
    ]
    for model in _configured_model_names():
        options.append(
            {
                "label": model,
                "value": f"ollama:{model}",
                "available": bool(settings.ollama_base_url),
                "provider": "ollama",
                "provider_label": "Ollama",
                "reason": "Ollama is not configured" if not settings.ollama_base_url else "",
            }
        )
    return options


def resolve_model(selected_model: str | None) -> str:
    selected = str(selected_model or "auto").strip()
    if not selected or selected.lower() == "auto":
        if not settings.ollama_model:
            raise OllamaUnavailableError("OLLAMA_MODEL is not configured")
        return settings.ollama_model
    if selected.lower().startswith("ollama:"):
        selected = selected.split(":", 1)[1].strip()
    if not selected:
        raise OllamaUnavailableError("An Ollama model is required")
    return selected


def generate_json(
    prompt: str,
    selected_model: str | None = None,
    num_predict: int | None = None,
    timeout_seconds: float | None = None,
) -> tuple[dict[str, Any], str]:
    if not settings.ollama_base_url:
        raise OllamaUnavailableError("OLLAMA_BASE_URL is not configured")

    model = resolve_model(selected_model)
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": num_predict or settings.ollama_num_predict,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{settings.ollama_base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds or settings.ollama_request_timeout_seconds,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyboardInterrupt) as exc:
        raise OllamaUnavailableError(f"Ollama request failed: {exc}") from exc

    response_text = str(body.get("response") or "").strip()
    if not response_text:
        raise OllamaResponseError("Ollama returned an empty response")
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise OllamaResponseError("Ollama returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise OllamaResponseError("Ollama response must be a JSON object")
    return result, model


def parse_resume_with_ollama(
    raw_text: str,
    selected_model: str | None = None,
    timeout_seconds: float | None = None,
) -> tuple[dict[str, Any], str]:
    prompt = f"{_RESUME_SYSTEM_PROMPT}\n\nParse this resume completely:\n\n{raw_text[:14000]}"
    result, model = generate_json(prompt, selected_model, timeout_seconds=timeout_seconds)
    return _normalise_resume(result, raw_text), model


def parse_experience_chunks_with_ollama(
    experience_lines: list[str],
    selected_model: str | None = None,
    timeout_seconds: float | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    continue_on_error: bool = False,
) -> tuple[dict[str, Any], str]:
    all_experience: list[dict[str, Any]] = []
    all_projects: list[dict[str, Any]] = []
    model_used = ""
    chunk_size = max(1, settings.ollama_section_chunk_lines)
    overlap = min(max(0, settings.ollama_section_overlap_lines), chunk_size - 1)
    step = max(1, chunk_size - overlap)
    starts = list(range(0, len(experience_lines), step))
    for chunk_index, start in enumerate(starts, 1):
        chunk = "\n".join(experience_lines[start : start + chunk_size])
        prompt = f"""Extract work experience and projects from this resume excerpt.
Return ONLY JSON:
{{
  "experience":[{{"title":"","company":"","location":"","dates":"","responsibilities":[]}}],
  "projects":[{{"name":"","description":"","technologies":[]}}]
}}
Do not use labels as values. Keep title and company correctly assigned. Treat named client/project work inside a job as projects.

Excerpt:
{chunk}"""
        try:
            payload, model_used = generate_json(
                prompt,
                selected_model,
                num_predict=settings.ollama_section_num_predict,
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            if not continue_on_error:
                raise
            if progress_callback:
                progress_callback(chunk_index, len(starts))
            continue
        normalized = _normalise_resume(payload, chunk)
        all_experience.extend(normalized["experience"])
        all_projects.extend(normalized["projects"])
        if progress_callback:
            progress_callback(chunk_index, len(starts))
    if not model_used and not all_experience and not all_projects:
        raise OllamaResponseError("Ollama could not extract any experience chunks")
    return {
        "experience": _dedupe_experience(all_experience),
        "projects": _dedupe_projects(all_projects),
    }, model_used


def _identity(*values: Any) -> str:
    return "|".join(re.sub(r"[^a-z0-9]+", "", _text(value).casefold()) for value in values)


def _dedupe_experience(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for value in values:
        key = _identity(value.get("company"), value.get("title"), value.get("dates"))
        if not key.strip("|"):
            continue
        if key not in merged:
            merged[key] = value
            continue
        responsibilities = [
            *merged[key].get("responsibilities", []),
            *value.get("responsibilities", []),
        ]
        merged[key]["responsibilities"] = list(dict.fromkeys(responsibilities))
    return list(merged.values())


def _dedupe_projects(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for value in values:
        key = _identity(value.get("name"))
        if not key:
            continue
        if key not in merged:
            merged[key] = value
            continue
        technologies = [*merged[key].get("technologies", []), *value.get("technologies", [])]
        merged[key]["technologies"] = list(dict.fromkeys(technologies))
        if not merged[key].get("description") and value.get("description"):
            merged[key]["description"] = value["description"]
    return list(merged.values())


def _text(value: Any) -> str:
    return str(value or "").strip()


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _normalise_project(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    project = {
        "name": _text(value.get("name")),
        "client": _text(value.get("client")),
        "duration": _text(value.get("duration") or value.get("dates")),
        "role": _text(value.get("role")),
        "description": _text(value.get("description")),
        "technologies": list(dict.fromkeys(_text_list(value.get("technologies")))),
        "responsibilities": list(dict.fromkeys(_text_list(value.get("responsibilities")))),
    }
    return project if any(project.values()) else None


def _normalise_resume(raw: dict[str, Any], raw_text: str) -> dict[str, Any]:
    contact = raw.get("contact") if isinstance(raw.get("contact"), dict) else {}
    name = _text(contact.get("name")) or _guess_name(raw_text)
    skills_raw = raw.get("skills")
    if isinstance(skills_raw, list):
        skills_raw = {"Technical Skills": skills_raw}
    skills: dict[str, list[str]] = {}
    if isinstance(skills_raw, dict):
        for category, values in skills_raw.items():
            category_name = _text(category).rstrip(":") or "Technical Skills"
            items = values if isinstance(values, list) else re.split(r"[,;\n]", values) if isinstance(values, str) else []
            deduped = list(dict.fromkeys(_text(item) for item in items if _text(item)))
            if deduped:
                skills[category_name] = deduped

    experience = []
    for value in raw.get("experience") or []:
        if not isinstance(value, dict):
            continue
        title, company = _normalise_title_company(value.get("title"), value.get("company"))
        nested_projects = [
            project
            for project in (_normalise_project(item) for item in value.get("projects") or [])
            if project is not None
        ]
        experience.append(
            {
                "title": title,
                "company": company,
                "company_name": company,
                "company_sector": "",
                "location": _text(value.get("location")),
                "dates": _text(value.get("dates")),
                "responsibilities": list(dict.fromkeys(_text_list(value.get("responsibilities")))),
                "projects": nested_projects,
            }
        )

    projects = [
        project
        for project in (_normalise_project(value) for value in raw.get("projects") or [])
        if project is not None
    ]

    education = []
    for value in raw.get("education") or []:
        if isinstance(value, dict):
            education.append({key: _text(value.get(key)) for key in ("degree", "institution", "year", "gpa")})

    return {
        "contact": {
            "name": name,
            "email": _text(contact.get("email")),
            "phone": _text(contact.get("phone")),
            "location": _text(contact.get("location")),
            "linkedin": _text(contact.get("linkedin")),
            "github": _text(contact.get("github")),
        },
        "summary": _clean_summary(_text(raw.get("summary")), name),
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": _text_list(raw.get("certifications")),
        "projects": projects,
        "achievements": _text_list(raw.get("achievements")),
    }


_ROLE_RE = re.compile(r"\b(?:engineer|developer|manager|analyst|architect|consultant|lead|director|tester|qa|devops|scrum)\b", re.I)
_LABEL_RE = re.compile(r"^(?:company(?:\s+name)?|client|employer|designation|role|position|title)\s*[:\-]\s*", re.I)


def _normalise_title_company(title_value: Any, company_value: Any) -> tuple[str, str]:
    title = _LABEL_RE.sub("", _text(title_value)).strip()
    company = _LABEL_RE.sub("", _text(company_value)).strip()
    if _ROLE_RE.search(company) and not _ROLE_RE.search(title):
        title, company = company, title
    return title, company


def _guess_name(raw_text: str) -> str:
    for line in raw_text.splitlines()[:20]:
        candidate = line.strip()
        words = candidate.split()
        if 2 <= len(words) <= 5 and len(candidate) <= 60 and all(re.fullmatch(r"[A-Za-z'\-]+", word) for word in words):
            if not re.search(r"resume|summary|profile|skills|experience", candidate, re.I):
                return candidate.title()
    return ""


def _clean_summary(summary: str, name: str) -> str:
    lines = []
    for line in summary.splitlines():
        cleaned = re.sub(r"^[\s•◦\-*]+", "", line).strip()
        if not cleaned or (name and cleaned.casefold() == name.casefold()):
            continue
        if re.search(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}|linkedin\.com|github\.com", cleaned, re.I):
            continue
        lines.append(cleaned)
    return "\n".join(lines)