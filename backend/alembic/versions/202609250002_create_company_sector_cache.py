"""create company sector cache

Revision ID: 202609250002
Revises: 202609250001
Create Date: 2026-09-25 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202609250002"
down_revision = "202609250001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_sectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_key", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=500), nullable=False),
        sa.Column("sector", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_key", name="uq_company_sectors_company_key"),
    )
    op.create_index("ix_company_sectors_company_key", "company_sectors", ["company_key"], unique=False)
    op.create_index("ix_company_sectors_sector", "company_sectors", ["sector"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_company_sectors_sector", table_name="company_sectors")
    op.drop_index("ix_company_sectors_company_key", table_name="company_sectors")
    op.drop_table("company_sectors")