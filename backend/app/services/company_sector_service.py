from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

from app.core.config import settings
from app.repositories.company_sector_repository import CompanySectorRepository
from app.services.ollama_service import generate_json


_ALLOWED_SECTORS = {
    "Technology",
    "Financial Services",
    "Healthcare",
    "Manufacturing",
    "Retail",
    "Energy",
    "Telecommunications",
    "Transportation",
    "Consumer Goods",
    "Real Estate",
    "Education",
    "Media",
    "Hospitality",
    "Agriculture",
    "Utilities",
    "Construction",
    "Pharmaceuticals",
    "Automotive",
    "Mining",
    "Aerospace & Defense",
    "Logistics",
    "Insurance",
    "Government",
    "Non-Profit",
    "Other",
    "Unknown",
}


class CompanySectorService:
    def __init__(self, repository: CompanySectorRepository) -> None:
        self.repository = repository

    def enrich(self, resume_data: dict[str, Any], raw_text: str = "") -> None:
        if not settings.sector_enrichment_enabled:
            return
        experience = resume_data.get("experience")
        if not isinstance(experience, list):
            return

        for item in experience:
            if not isinstance(item, dict):
                continue
            company = str(item.get("company_name") or item.get("company") or "").strip()
            key = self.company_key(company)
            if not key:
                item["company_sector"] = "Industry Not Determined"
                continue

            cached = self.repository.get(key)
            if cached:
                item["company_sector"] = cached.sector
                continue

            context = self._public_context(company)
            if not context:
                context = raw_text[:2000]
            try:
                classification = self._classify(company, context)
            except Exception:
                item["company_sector"] = "Industry Not Determined"
                continue

            sector = classification["sector"]
            item["company_sector"] = sector if sector != "Unknown" else "Industry Not Determined"
            if sector != "Unknown":
                self.repository.upsert(
                    company_key=key,
                    company_name=company,
                    sector=sector,
                    industry=classification["industry"],
                    confidence_score=classification["confidence"],
                    source="ollama-web" if context else "ollama",
                )

    @staticmethod
    def company_key(company_name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", company_name.casefold())

    def _classify(self, company: str, context: str) -> dict[str, Any]:
        allowed = "\n".join(f"- {sector}" for sector in sorted(_ALLOWED_SECTORS))
        prompt = f"""You are a business intelligence company-classification assistant.
Classify the company into exactly one allowed primary sector. If uncertain, return Unknown. Never guess at low confidence.
Return only JSON: {{"company_name":"","sector":"","industry":"","confidence":0.0}}

Allowed sectors:
{allowed}

Company: {company}
Context: {context[:3500]}"""
        model = settings.ollama_sector_model or settings.ollama_model
        payload, _ = generate_json(prompt, model)
        sector = str(payload.get("sector") or "Unknown").strip()
        industry = str(payload.get("industry") or "Unknown").strip() or "Unknown"
        try:
            confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        if sector not in _ALLOWED_SECTORS or confidence < settings.sector_minimum_confidence:
            sector = "Unknown"
        return {"sector": sector, "industry": industry, "confidence": confidence}

    def _public_context(self, company: str) -> str:
        if not settings.sector_web_context_enabled:
            return ""
        snippets: list[str] = []
        try:
            params = urllib.parse.urlencode(
                {"q": f"{company} company industry sector", "format": "json", "no_html": "1"}
            )
            request = urllib.request.Request(
                f"https://api.duckduckgo.com/?{params}",
                headers={"User-Agent": "ta-candidate-screening/1.0"},
            )
            with urllib.request.urlopen(request, timeout=settings.sector_web_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            abstract = str(payload.get("AbstractText") or "").strip()
            if abstract:
                snippets.append(abstract)
        except Exception:
            pass
        try:
            title = urllib.parse.quote(company, safe="")
            request = urllib.request.Request(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                headers={"User-Agent": "ta-candidate-screening/1.0"},
            )
            with urllib.request.urlopen(request, timeout=settings.sector_web_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            extract = str(payload.get("extract") or "").strip()
            if extract:
                snippets.append(extract)
        except Exception:
            pass
        return "\n".join(dict.fromkeys(snippets))[:3000]