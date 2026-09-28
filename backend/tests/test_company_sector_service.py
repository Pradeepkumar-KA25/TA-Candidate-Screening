from app.core.config import settings
from app.repositories.company_sector_repository import CompanySectorRepository
from app.services.company_sector_service import CompanySectorService


def test_sector_enrichment_uses_postgres_cache(sqlite_session, monkeypatch) -> None:
    service = CompanySectorService(CompanySectorRepository(sqlite_session))
    monkeypatch.setattr(settings, "sector_enrichment_enabled", True)
    monkeypatch.setattr(service, "_public_context", lambda _company: "Acme builds enterprise software")
    monkeypatch.setattr(
        service,
        "_classify",
        lambda _company, _context: {"sector": "Technology", "industry": "Software", "confidence": 0.9},
    )
    first = {"experience": [{"company": "Acme, Inc."}]}
    service.enrich(first)
    sqlite_session.flush()

    assert first["experience"][0]["company_sector"] == "Technology"

    monkeypatch.setattr(service, "_classify", lambda *_args: (_ for _ in ()).throw(AssertionError("cache missed")))
    second = {"experience": [{"company": "ACME INC"}]}
    service.enrich(second)

    assert second["experience"][0]["company_sector"] == "Technology"