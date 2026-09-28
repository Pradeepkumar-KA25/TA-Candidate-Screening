from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_sector import CompanySector


class CompanySectorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, company_key: str) -> CompanySector | None:
        return self.session.scalar(select(CompanySector).where(CompanySector.company_key == company_key))

    def upsert(
        self,
        *,
        company_key: str,
        company_name: str,
        sector: str,
        industry: str,
        confidence_score: float,
        source: str,
    ) -> CompanySector:
        record = self.get(company_key)
        if record is None:
            record = CompanySector(company_key=company_key, company_name=company_name)
            self.session.add(record)
        record.company_name = company_name
        record.sector = sector
        record.industry = industry
        record.confidence_score = confidence_score
        record.source = source
        self.session.flush()
        return record