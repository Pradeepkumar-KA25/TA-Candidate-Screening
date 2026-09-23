"""Add CASCADE DELETE to shortlist_candidates.candidate_id foreign key

Revision ID: 202609221004
Revises: 202609221003
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202609221004"
down_revision = "202609221003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing foreign key constraint that doesn't have CASCADE DELETE
    op.drop_constraint("shortlist_candidates_candidate_id_fkey", "shortlist_candidates", type_="foreignkey")
    
    # Recreate the foreign key constraint with ondelete="CASCADE"
    op.create_foreign_key(
        "shortlist_candidates_candidate_id_fkey",
        "shortlist_candidates",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # Drop the CASCADE DELETE foreign key
    op.drop_constraint("shortlist_candidates_candidate_id_fkey", "shortlist_candidates", type_="foreignkey")
    
    # Recreate the original foreign key without CASCADE DELETE
    op.create_foreign_key(
        "shortlist_candidates_candidate_id_fkey",
        "shortlist_candidates",
        "candidates",
        ["candidate_id"],
        ["id"]
    )
