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

    def list_users(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.created_at.desc())).all())

    def create_user(self, *, full_name: str, email: str, password_hash: str, role: str) -> User:
        user = User(full_name=full_name, email=email.strip().lower(), password_hash=password_hash, role=role)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user(self, user_id: UUID, *, full_name: str | None = None, role: str | None = None, is_active: bool | None = None) -> User | None:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_password(self, user_id: UUID, password_hash: str) -> User | None:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None
        user.password_hash = password_hash
        self.session.commit()
        self.session.refresh(user)
        return user
