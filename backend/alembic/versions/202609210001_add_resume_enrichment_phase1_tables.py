"""Add resume enrichment Phase 1 tables.

Revision ID: 202609210001
Revises: 202609170001
Create Date: 2026-09-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "202609210001"
down_revision = "202609170001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create review_batches table
    op.create_table(
        "review_batches",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("batch_number", sa.String(32), nullable=False),
        sa.Column("batch_size", sa.Integer(), nullable=False),
        sa.Column("total_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_batches_batch_number", "review_batches", ["batch_number"], unique=True)
    op.create_index("ix_review_batches_status", "review_batches", ["status"])
    op.create_index("ix_review_batches_created_by_user_id", "review_batches", ["created_by_user_id"])

    # Create candidate_reviews table
    op.create_table(
        "candidate_reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("batch_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("candidate_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("zoho_candidate_id", sa.String(128), nullable=True),
        sa.Column("candidate_name", sa.String(255), nullable=False),
        sa.Column("approval_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("approval_notes", sa.String(512), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["batch_id"], ["review_batches.id"], "fk_candidate_reviews_batch_id"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], "fk_candidate_reviews_candidate_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_reviews_batch_id", "candidate_reviews", ["batch_id"])
    op.create_index("ix_candidate_reviews_candidate_id", "candidate_reviews", ["candidate_id"])
    op.create_index("ix_candidate_reviews_approval_status", "candidate_reviews", ["approval_status"])
    op.create_index("ix_candidate_reviews_reviewed_by_user_id", "candidate_reviews", ["reviewed_by_user_id"])
    op.create_index(
        "ix_candidate_reviews_batch_approval",
        "candidate_reviews",
        ["batch_id", "approval_status"],
    )

    # Create proposed_field_changes table
    op.create_table(
        "proposed_field_changes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("candidate_review_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("zoho_field_api_name", sa.String(128), nullable=False),
        sa.Column("zoho_field_display_name", sa.String(255), nullable=False),
        sa.Column("existing_zoho_value", sa.Text(), nullable=True),
        sa.Column("extracted_resume_value", sa.Text(), nullable=True),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("change_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("field_approval_notes", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["candidate_review_id"],
            ["candidate_reviews.id"],
            "fk_proposed_field_changes_candidate_review_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposed_field_changes_candidate_review_id", "proposed_field_changes", ["candidate_review_id"])
    op.create_index("ix_proposed_field_changes_change_status", "proposed_field_changes", ["change_status"])


def downgrade() -> None:
    op.drop_index("ix_proposed_field_changes_change_status", table_name="proposed_field_changes")
    op.drop_index("ix_proposed_field_changes_candidate_review_id", table_name="proposed_field_changes")
    op.drop_table("proposed_field_changes")

    op.drop_index("ix_candidate_reviews_batch_approval", table_name="candidate_reviews")
    op.drop_index("ix_candidate_reviews_reviewed_by_user_id", table_name="candidate_reviews")
    op.drop_index("ix_candidate_reviews_approval_status", table_name="candidate_reviews")
    op.drop_index("ix_candidate_reviews_candidate_id", table_name="candidate_reviews")
    op.drop_index("ix_candidate_reviews_batch_id", table_name="candidate_reviews")
    op.drop_table("candidate_reviews")

    op.drop_index("ix_review_batches_created_by_user_id", table_name="review_batches")
    op.drop_index("ix_review_batches_status", table_name="review_batches")
    op.drop_index("ix_review_batches_batch_number", table_name="review_batches")
    op.drop_table("review_batches")
