from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.security import hash_password
from app.models.candidate import Candidate
from app.models.user import User


@pytest.fixture()
def sqlite_session(temp_sqlite_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite+pysqlite:///{temp_sqlite_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def temp_sqlite_path(tmp_path: Path) -> Path:
    return tmp_path / "migration.db"


@pytest.fixture()
def user_factory(sqlite_session: Session):
    def create_user(**overrides):
        defaults = {
            "full_name": "Asha Sharma",
            "email": "asha.sharma@example.com",
            "password_hash": hash_password("Secret123!"),
            "role": "Recruiter",
            "is_active": True,
        }
        defaults.update(overrides)
        user = User(**defaults)
        sqlite_session.add(user)
        sqlite_session.commit()
        sqlite_session.refresh(user)
        return user

    return create_user


@pytest.fixture()
def candidate_factory(sqlite_session: Session):
    counter = {"count": 0}

    def create_candidate(**overrides):
        counter["count"] += 1
        defaults = {
            "full_name": f"Candidate {counter['count']}",
            "zoho_record_id": f"zoho_{uuid4()}",
            "email": f"candidate{counter['count']}@example.com",
            "phone": "1234567890",
            "total_experience_years": 5.0,
            "current_location": "Bengaluru",
            "preferred_location": "Bengaluru",
            "status": "active",
            "source": "zoho_recruit",
        }
        defaults.update(overrides)
        candidate = Candidate(**defaults)
        sqlite_session.add(candidate)
        sqlite_session.commit()
        sqlite_session.refresh(candidate)
        return candidate

    return create_candidate
