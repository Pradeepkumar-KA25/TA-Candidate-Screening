"""Add CASCADE DELETE to review batch foreign keys.

Revision ID: 202609210003
Revises: 202609210002
Create Date: 2026-09-21 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "202609210003"
down_revision = "202609210002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing foreign key constraints
    op.drop_constraint("fk_candidate_reviews_batch_id", "candidate_reviews", type_="foreignkey")
    op.drop_constraint("fk_proposed_field_changes_candidate_review_id", "proposed_field_changes", type_="foreignkey")
    
    # Recreate the foreign key constraints with CASCADE DELETE
    op.create_foreign_key(
        "fk_candidate_reviews_batch_id",
        "candidate_reviews",
        "review_batches",
        ["batch_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_proposed_field_changes_candidate_review_id",
        "proposed_field_changes",
        "candidate_reviews",
        ["candidate_review_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Drop the new CASCADE foreign keys
    op.drop_constraint("fk_candidate_reviews_batch_id", "candidate_reviews", type_="foreignkey")
    op.drop_constraint("fk_proposed_field_changes_candidate_review_id", "proposed_field_changes", type_="foreignkey")
    
    # Recreate the old foreign keys without CASCADE DELETE
    op.create_foreign_key(
        "fk_candidate_reviews_batch_id",
        "candidate_reviews",
        "review_batches",
        ["batch_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_proposed_field_changes_candidate_review_id",
        "proposed_field_changes",
        "candidate_reviews",
        ["candidate_review_id"],
        ["id"],
    )
