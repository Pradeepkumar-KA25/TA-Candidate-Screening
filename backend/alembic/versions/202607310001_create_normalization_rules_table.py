"""create normalization rules table

Revision ID: 202607310001
Revises: 202607290001
Create Date: 2026-07-31 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202607310001"
down_revision = "202607290001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "normalization_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("field_type", sa.String(length=64), nullable=False),
        sa.Column("raw_value", sa.String(length=255), nullable=False),
        sa.Column("normalized_value", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_type", "raw_value", name="uq_normalization_rules_field_raw"),
    )
    op.create_index("ix_normalization_rules_field_type", "normalization_rules", ["field_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_normalization_rules_field_type", table_name="normalization_rules")
    op.drop_table("normalization_rules")
