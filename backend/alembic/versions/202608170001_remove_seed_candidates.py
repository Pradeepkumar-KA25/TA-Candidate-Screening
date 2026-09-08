"""remove local sample candidates

Revision ID: 202608170001
Revises: 202608140001
Create Date: 2026-08-17 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608170001"
down_revision = "202608140001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM candidates "
            "WHERE source = 'local_seed' "
            "OR zoho_record_id LIKE 'sample_zoho_record_%'"
        )
    )


def downgrade() -> None:
    pass