"""Add zoho_candidate_id_formatted column for ZR_ format Zoho IDs

Revision ID: 202609221001
Revises: 202609210003
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202609221001"
down_revision = "202609210003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new column for formatted Zoho candidate ID (ZR_ format)
    op.add_column(
        "candidates",
        sa.Column("zoho_candidate_id_formatted", sa.String(128), nullable=True, index=True)
    )


def downgrade() -> None:
    # Remove the column if migration is rolled back
    op.drop_column("candidates", "zoho_candidate_id_formatted")
