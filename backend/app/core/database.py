from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass




@lru_cache(maxsize=None)
def get_engine(database_url: str | None = None):
    return create_engine(database_url or settings.database_url, future=True)


def get_session_factory(database_url: str | None = None):
    return sessionmaker(bind=get_engine(database_url), autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()