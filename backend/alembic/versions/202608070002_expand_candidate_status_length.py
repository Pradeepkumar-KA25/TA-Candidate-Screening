"""expand candidate status length

Revision ID: 202608070002
Revises: 202608070001
Create Date: 2026-08-07 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608070002"
down_revision = "202608070001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            type_=sa.String(length=255),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=255),
            type_=sa.String(length=32),
            existing_nullable=True,
        )