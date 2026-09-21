"""Add resume storage fields to candidates table.

Revision ID: 202609170001
Revises: 202609150002
Create Date: 2026-09-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202609170001'
down_revision = '202609150002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add resume-related columns to candidates table
    op.add_column('candidates', sa.Column('resume_url', sa.String(512), nullable=True))
    op.add_column('candidates', sa.Column('resume_file_name', sa.String(255), nullable=True))
    op.add_column('candidates', sa.Column('resume_last_fetched_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove resume-related columns from candidates table
    op.drop_column('candidates', 'resume_last_fetched_at')
    op.drop_column('candidates', 'resume_file_name')
    op.drop_column('candidates', 'resume_url')
