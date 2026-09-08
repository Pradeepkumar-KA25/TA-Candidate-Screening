"""Remove legacy resume storage and generated-download persistence.

Revision ID: 202609080001
Revises: b7ba7c24ba0e, 202609040001, kanini_001
Create Date: 2026-09-08

The active Kanini workflow retains only kanini_resumes (parsed data) and
kanini_user_templates (reusable template specifications). Rendered documents
are streamed directly to the client and are not stored.
"""

from alembic import op


revision = "202609080001"
down_revision = ("b7ba7c24ba0e", "202609040001", "kanini_001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy resume-builder tables, all superseded by the Kanini workflow.
    op.drop_table("resume_embeddings")
    op.drop_table("generated_resumes")
    op.drop_table("resume_templates")
    op.drop_table("resumes")
    op.drop_table("resume_drafts")
    op.drop_table("company_sectors")

    # Generated files and database-backed drafts are no longer persisted.
    op.drop_table("kanini_generated_resumes")
    op.drop_table("kanini_template_drafts")

    # Uploaded source documents are parsed transiently; only parsed data remains.
    op.drop_column("kanini_resumes", "file_path")


def downgrade() -> None:
    raise NotImplementedError(
        "This destructive cleanup intentionally cannot restore deleted resume data."
    )
