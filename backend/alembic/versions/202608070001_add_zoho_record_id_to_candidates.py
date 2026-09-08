"""add zoho record id to candidates

Revision ID: 202608070001
Revises: 202608030001
Create Date: 2026-08-07 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608070001"
down_revision = "202608030001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind is not None else "postgresql"

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.add_column(sa.Column("zoho_record_id", sa.String(length=128), nullable=True))

    op.execute("UPDATE candidates SET zoho_record_id = zoho_candidate_id WHERE zoho_record_id IS NULL")

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column("zoho_record_id", existing_type=sa.String(length=128), nullable=False)
        batch_op.alter_column("zoho_candidate_id", existing_type=sa.String(length=128), nullable=True)
        batch_op.alter_column("status", existing_type=sa.String(length=32), nullable=True, server_default=None)
        batch_op.alter_column("source", existing_type=sa.String(length=64), nullable=True, server_default=None)

    if dialect_name == "postgresql":
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_candidates_zoho_record_id ON candidates (zoho_record_id)"
        )
        return

    op.create_index("ix_candidates_zoho_record_id", "candidates", ["zoho_record_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind is not None else "postgresql"

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_candidates_zoho_record_id")
    else:
        op.drop_index("ix_candidates_zoho_record_id", table_name="candidates")

    op.execute("UPDATE candidates SET zoho_candidate_id = COALESCE(zoho_candidate_id, zoho_record_id)")

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.alter_column("zoho_candidate_id", existing_type=sa.String(length=128), nullable=False)
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            nullable=False,
            server_default=sa.text("'active'"),
        )
        batch_op.alter_column(
            "source",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default=sa.text("'zoho_recruit'"),
        )
        batch_op.drop_column("zoho_record_id")