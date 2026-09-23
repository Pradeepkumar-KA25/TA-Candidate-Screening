"""Add CASCADE DELETE to duplicate_reviews foreign keys

Revision ID: 202609221003
Revises: 202609221002
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202609221003"
down_revision = "202609221002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing foreign key constraints that don't have CASCADE DELETE
    op.drop_constraint("duplicate_reviews_candidate_id_fkey", "duplicate_reviews", type_="foreignkey")
    op.drop_constraint("duplicate_reviews_matched_candidate_id_fkey", "duplicate_reviews", type_="foreignkey")
    
    # Recreate the foreign key constraints with ondelete="CASCADE"
    op.create_foreign_key(
        "duplicate_reviews_candidate_id_fkey",
        "duplicate_reviews",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="CASCADE"
    )
    op.create_foreign_key(
        "duplicate_reviews_matched_candidate_id_fkey",
        "duplicate_reviews",
        "candidates",
        ["matched_candidate_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # Drop the CASCADE DELETE foreign keys
    op.drop_constraint("duplicate_reviews_candidate_id_fkey", "duplicate_reviews", type_="foreignkey")
    op.drop_constraint("duplicate_reviews_matched_candidate_id_fkey", "duplicate_reviews", type_="foreignkey")
    
    # Recreate the original foreign keys without CASCADE DELETE
    op.create_foreign_key(
        "duplicate_reviews_candidate_id_fkey",
        "duplicate_reviews",
        "candidates",
        ["candidate_id"],
        ["id"]
    )
    op.create_foreign_key(
        "duplicate_reviews_matched_candidate_id_fkey",
        "duplicate_reviews",
        "candidates",
        ["matched_candidate_id"],
        ["id"]
    )
