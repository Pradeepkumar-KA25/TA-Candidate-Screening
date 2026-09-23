"""Rename zoho_candidate_id_formatted to candidate_id

Revision ID: 202609221005
Revises: 202609221004
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202609221005"
down_revision = "202609221004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the column
    op.alter_column("candidates", "zoho_candidate_id_formatted", new_column_name="candidate_id")


def downgrade() -> None:
    # Rename back to original name
    op.alter_column("candidates", "candidate_id", new_column_name="zoho_candidate_id_formatted")
