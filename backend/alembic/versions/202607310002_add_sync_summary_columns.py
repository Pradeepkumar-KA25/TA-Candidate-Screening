"""add sync summary columns

Revision ID: 202607310002
Revises: 202607310001
Create Date: 2026-07-31 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202607310002"
down_revision = "202607310001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sync_logs", sa.Column("normalized_records", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_logs", sa.Column("normalization_examples", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("sync_logs", "normalization_examples")
    op.drop_column("sync_logs", "normalized_records")
