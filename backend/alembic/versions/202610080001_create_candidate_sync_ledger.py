"""Create the persistent Zoho candidate sync ledger."""

from alembic import op
import sqlalchemy as sa


revision = "202610080001"
down_revision = "202609290002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_sync_ledger",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("zoho_record_id", sa.String(length=128), nullable=False),
        sa.Column("last_processed_modified_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="processing"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zoho_record_id"),
    )
    op.create_index(
        "ix_candidate_sync_ledger_zoho_record_id",
        "candidate_sync_ledger",
        ["zoho_record_id"],
        unique=True,
    )
    op.create_index(
        "ix_candidate_sync_ledger_status",
        "candidate_sync_ledger",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_sync_ledger_status", table_name="candidate_sync_ledger")
    op.drop_index("ix_candidate_sync_ledger_zoho_record_id", table_name="candidate_sync_ledger")
    op.drop_table("candidate_sync_ledger")
