from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.models.user import User


DEFAULT_ADMIN_EMAIL = "admin@talent.com"
DEFAULT_ADMIN_PASSWORD = "Secret123!"


def provision_admin() -> None:
    email = settings.initial_admin_email or DEFAULT_ADMIN_EMAIL
    password = settings.initial_admin_password or DEFAULT_ADMIN_PASSWORD
    if settings.initial_admin_password and len(password) < 12:
        raise ValueError("INITIAL_ADMIN_PASSWORD must contain at least 12 characters")

    session = get_session_factory()()
    try:
        existing_user = session.scalar(select(User).where(User.email == email))
        if existing_user:
            print(f"Initial admin already exists: {email}")
            return

        session.add(
            User(
                full_name=settings.initial_admin_name,
                email=email,
                password_hash=hash_password(password),
                role="Admin",
                is_active=True,
            )
        )
        session.commit()
        print(f"Initial admin created: {email}")
    finally:
        session.close()


if __name__ == "__main__":
    provision_admin()