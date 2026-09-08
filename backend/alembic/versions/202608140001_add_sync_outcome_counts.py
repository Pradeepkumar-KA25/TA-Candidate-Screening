"""add sync outcome counts

Revision ID: 202608140001
Revises: 202608110001
Create Date: 2026-08-14 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608140001"
down_revision = "202608110001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sync_logs", sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("sync_logs", sa.Column("duplicate_matches", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("sync_logs", "duplicate_matches")
    op.drop_column("sync_logs", "records_failed")