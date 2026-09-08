"""add candidate sync page cursor

Revision ID: 202608170002
Revises: 202608170001
Create Date: 2026-08-17 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608170002"
down_revision = "202608170001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_settings",
        sa.Column("next_candidate_sync_page", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("integration_settings", "next_candidate_sync_page")