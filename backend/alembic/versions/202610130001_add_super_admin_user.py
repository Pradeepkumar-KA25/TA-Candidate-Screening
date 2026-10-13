"""Add the hidden Super Admin account."""

from alembic import op
import sqlalchemy as sa


revision = "202610130001"
down_revision = "202610080001"
branch_labels = None
depends_on = None


SUPER_ADMIN_EMAIL = "ta@talent.com"
SUPER_ADMIN_PASSWORD_HASH = "$2b$12$a4iiVcFU7j2owmPY088tsek5xOLfdSGhZ89Y9fPbei6F4L83asKLG"


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO users (id, full_name, email, password_hash, role, is_active) "
            "SELECT CAST(:id AS uuid), :full_name, :email, :password_hash, :role, true "
            "WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = :email)"
        ).bindparams(
            id="7f8c2d1e-6b4a-4c9f-8e12-3a5d7b9c0f21",
            full_name="Talent Acquisition Super Admin",
            email=SUPER_ADMIN_EMAIL,
            password_hash=SUPER_ADMIN_PASSWORD_HASH,
            role="Super Admin",
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE email = :email AND role = :role").bindparams(
            email=SUPER_ADMIN_EMAIL,
            role="Super Admin",
        )
    )
