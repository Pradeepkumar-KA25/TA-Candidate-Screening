"""Add resume drafts table for template creation workflow

Revision ID: 202609040001
Revises: 202609030001
Create Date: 2026-09-04 10:00:00.000000

Adds resume_drafts table to support template design workflow:
- Track intermediate drafts during template creation
- Store extracted resume data from uploaded PDFs
- Store AI-generated template specifications
- Store HTML previews for user review
- Enforce owner-scoping for security
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "202609040001"
down_revision = "202609030001"
branch_labels = None
depends_on = None

json_data = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    # Create resume_drafts table
    op.create_table(
        "resume_drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("extracted_data", json_data, nullable=False, server_default="{}"),
        sa.Column("template_spec", json_data, nullable=True, server_default="{}"),
        sa.Column("preview_html", sa.Text(), nullable=True),
        sa.Column("suggested_description", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_drafts_user_id", "resume_drafts", ["user_id"], unique=False)
    op.create_index("ix_resume_drafts_status", "resume_drafts", ["status"], unique=False)
    op.create_index("ix_resume_drafts_user_status", "resume_drafts", ["user_id", "status"], unique=False)
    op.create_index("ix_resume_drafts_created_at", "resume_drafts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resume_drafts_created_at", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_user_status", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_status", table_name="resume_drafts")
    op.drop_index("ix_resume_drafts_user_id", table_name="resume_drafts")
    op.drop_table("resume_drafts")
