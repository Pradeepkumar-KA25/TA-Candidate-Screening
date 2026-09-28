"""add resume extraction job fields

Revision ID: 202609250003
Revises: 202609250002
Create Date: 2026-09-25 00:03:00.000000
"""

revision = "202609250003"
down_revision = "202609250002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kept as a no-op because historical databases may already be stamped here.
    pass


def downgrade() -> None:
    pass