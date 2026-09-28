"""remove legacy default admin user

Revision ID: 202609250001
Revises: 202609221005
Create Date: 2026-09-25 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202609250001"
down_revision = "202609221005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM users WHERE email = :email AND full_name = :full_name "
            "AND role = :role AND password_hash = :password_hash"
        ).bindparams(
            email="admin@talent.com",
            full_name="Admin User",
            role="Admin",
            password_hash="$2b$12$a4iiVcFU7j2owmPY088tsek5xOLfdSGhZ89Y9fPbei6F4L83asKLG",
        )
    )


def downgrade() -> None:
    pass