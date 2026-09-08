"""seed default admin user

Revision ID: 202608250001
Revises: 202608170002
Create Date: 2026-08-25 00:01:00.000000
"""

from uuid import uuid5, NAMESPACE_DNS

from alembic import op
import sqlalchemy as sa


revision = "202608250001"
down_revision = "202608170002"
branch_labels = None
depends_on = None


ADMIN_EMAIL = "admin@talent.com"
ADMIN_USER_ID = str(uuid5(NAMESPACE_DNS, "talent-acquisition-default-admin"))
ADMIN_PASSWORD_HASH = "$2b$12$a4iiVcFU7j2owmPY088tsek5xOLfdSGhZ89Y9fPbei6F4L83asKLG"


def upgrade() -> None:
    bind = op.get_bind()
    existing_admin = bind.execute(
        sa.text("SELECT 1 FROM users WHERE email = :email"),
        {"email": ADMIN_EMAIL},
    ).scalar()

    if existing_admin is None:
        bind.execute(
            sa.text(
                "INSERT INTO users (id, full_name, email, password_hash, role, is_active) "
                "VALUES (:id, :full_name, :email, :password_hash, :role, :is_active)"
            ),
            {
                "id": ADMIN_USER_ID,
                "full_name": "Admin User",
                "email": ADMIN_EMAIL,
                "password_hash": ADMIN_PASSWORD_HASH,
                "role": "Admin",
                "is_active": True,
            },
        )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE email = :email").bindparams(email=ADMIN_EMAIL))