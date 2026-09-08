from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.user import User


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        statement = select(User).where(func.lower(User.email) == normalized_email)
        return self.session.scalar(statement)

    def update_last_login(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        statement = update(User).where(User.id == user_id).values(last_login_at=now, updated_at=now)
        self.session.execute(statement)
        self.session.commit()

    def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)
