"""Add structured fields to activity log.

Revision ID: 202609280001
Revises: 202609250004
"""

from alembic import op
import sqlalchemy as sa


revision = "202609280001"
down_revision = "202609250004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activity_log", sa.Column("entity_type", sa.String(length=64), nullable=True))
    op.add_column("activity_log", sa.Column("entity_id", sa.String(length=128), nullable=True))
    op.add_column("activity_log", sa.Column("result", sa.String(length=32), nullable=False, server_default="success"))
    op.add_column("activity_log", sa.Column("metadata", sa.JSON(), nullable=True))
    op.create_index("ix_activity_log_entity_type", "activity_log", ["entity_type"])
    op.create_index("ix_activity_log_entity_id", "activity_log", ["entity_id"])
    op.create_index("ix_activity_log_result", "activity_log", ["result"])


def downgrade() -> None:
    op.drop_index("ix_activity_log_result", table_name="activity_log")
    op.drop_index("ix_activity_log_entity_id", table_name="activity_log")
    op.drop_index("ix_activity_log_entity_type", table_name="activity_log")
    op.drop_column("activity_log", "metadata")
    op.drop_column("activity_log", "result")
    op.drop_column("activity_log", "entity_id")
    op.drop_column("activity_log", "entity_type")