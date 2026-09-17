"""Make sync_logs.triggered_by nullable for system-triggered syncs.

Revision ID: 202609150002
Revises: 202609150001
Create Date: 2026-09-15 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202609150002'
down_revision = '202609150001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter the triggered_by column to be nullable
    op.alter_column('sync_logs', 'triggered_by',
               existing_type=sa.UUID(),
               nullable=True,
               existing_nullable=False)


def downgrade() -> None:
    # Downgrade: make triggered_by NOT NULL again
    # This will fail if there are NULL values, so we set them to a placeholder first
    op.execute(sa.text("UPDATE sync_logs SET triggered_by = '00000000-0000-0000-0000-000000000000' WHERE triggered_by IS NULL"))
    op.alter_column('sync_logs', 'triggered_by',
               existing_type=sa.UUID(),
               nullable=False,
               existing_nullable=True)
