"""Add local write-back validation and sync tracking."""

from alembic import op
import sqlalchemy as sa


revision = "202609290002"
down_revision = "202609290001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate_reviews", sa.Column("write_back_status", sa.String(length=32), nullable=False, server_default="NOT_SENT"))
    op.add_column("candidate_reviews", sa.Column("write_back_error", sa.String(length=512), nullable=True))
    op.add_column("candidate_reviews", sa.Column("write_back_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_candidate_reviews_write_back_status", "candidate_reviews", ["write_back_status"])

    op.add_column("proposed_field_changes", sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="NOT_SENT"))
    op.add_column("proposed_field_changes", sa.Column("sync_error", sa.String(length=512), nullable=True))
    op.add_column("proposed_field_changes", sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_proposed_field_changes_sync_status", "proposed_field_changes", ["sync_status"])


def downgrade() -> None:
    op.drop_index("ix_proposed_field_changes_sync_status", table_name="proposed_field_changes")
    op.drop_column("proposed_field_changes", "synced_at")
    op.drop_column("proposed_field_changes", "sync_error")
    op.drop_column("proposed_field_changes", "sync_status")
    op.drop_index("ix_candidate_reviews_write_back_status", table_name="candidate_reviews")
    op.drop_column("candidate_reviews", "write_back_at")
    op.drop_column("candidate_reviews", "write_back_error")
    op.drop_column("candidate_reviews", "write_back_status")