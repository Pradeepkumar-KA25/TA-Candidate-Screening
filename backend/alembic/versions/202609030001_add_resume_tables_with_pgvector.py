"""Add resume builder tables with pgvector support

Revision ID: 202609030001
Revises: 202608250001
Create Date: 2026-09-03 10:00:00.000000

Tables created:
1. resumes - Main resume documents
2. resume_templates - Template definitions  
3. generated_resumes - Generated output files
4. company_sectors - Company-to-sector lookups
5. resume_embeddings - Vector embeddings (requires pgvector extension)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "202609030001"
down_revision = "202608250001"
branch_labels = None
depends_on = None

json_data = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    # Note: pgvector extension is optional and not required for initial schema
    # If pgvector is installed on PostgreSQL, embeddings can be migrated to vector type later
    # For now, embeddings are stored as text (JSON array format)

    # 1. Create resumes table
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("file_format", sa.String(length=10), nullable=False),
        sa.Column("parsed_data", json_data, nullable=False, server_default="{}"),
        sa.Column("normalization_data", json_data, nullable=True, server_default="{}"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("extra_metadata", json_data, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_resumes_session_id"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"], unique=False)
    op.create_index("ix_resumes_session_id", "resumes", ["session_id"], unique=False)
    op.create_index("ix_resumes_status", "resumes", ["status"], unique=False)
    op.create_index("ix_resumes_created_at", "resumes", ["created_at"], unique=False)
    op.create_index("ix_resumes_user_id_created_at", "resumes", ["user_id", sa.text("created_at DESC")], unique=False)
    op.create_index("ix_resumes_user_status", "resumes", ["user_id", "status"], unique=False)

    # 2. Create resume_templates table
    op.create_table(
        "resume_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.String(length=100), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("template_type", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("template_spec", json_data, nullable=False, server_default="{}"),
        sa.Column("template_file_path", sa.String(length=1000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("extra_metadata", json_data, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", name="uq_templates_template_id"),
    )
    op.create_index("ix_templates_template_id", "resume_templates", ["template_id"], unique=False)
    op.create_index("ix_templates_user_id", "resume_templates", ["user_id"], unique=False)
    op.create_index("ix_templates_is_active", "resume_templates", ["is_active"], unique=False)
    op.create_index("ix_templates_type", "resume_templates", ["template_type"], unique=False)
    op.create_index("ix_templates_user_active", "resume_templates", ["user_id", "is_active"], unique=False)

    # 3. Create generated_resumes table
    op.create_table(
        "generated_resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("generation_status", sa.String(length=50), nullable=False, server_default="generated"),
        sa.Column("generation_error", sa.Text(), nullable=True),
        sa.Column("extra_metadata", json_data, nullable=True, server_default="{}"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["resume_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_resumes_resume_id", "generated_resumes", ["resume_id"], unique=False)
    op.create_index("ix_generated_resumes_template_id", "generated_resumes", ["template_id"], unique=False)
    op.create_index("ix_generated_resumes_format", "generated_resumes", ["format"], unique=False)
    op.create_index("ix_generated_resumes_generated_at", "generated_resumes", ["generated_at"], unique=False)
    op.create_index("ix_generated_resume_id_format", "generated_resumes", ["resume_id", "format"], unique=False)

    # 4. Create company_sectors table
    op.create_table(
        "company_sectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_name", sa.String(length=500), nullable=False),
        sa.Column("sector", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="manual"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("extra_metadata", json_data, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_name", name="uq_company_sectors_company_name"),
    )
    op.create_index("ix_company_sectors_company_name", "company_sectors", ["company_name"], unique=False)
    op.create_index("ix_company_sectors_sector", "company_sectors", ["sector"], unique=False)
    op.create_index("ix_company_sectors_source", "company_sectors", ["source"], unique=False)
    op.create_index("ix_company_sectors_last_updated", "company_sectors", ["last_updated"], unique=False)

    # 5. Create resume_embeddings table with pgvector support (optional)
    op.create_table(
        "resume_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("section_type", sa.String(length=100), nullable=False),
        sa.Column("section_index", sa.Integer(), nullable=False),
        sa.Column("section_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # Stored as JSON text array, can be migrated to pgvector later
        sa.Column("extra_metadata", json_data, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "section_type", "section_index", name="uq_resume_section_unique"),
    )
    
    op.create_index("ix_resume_embeddings_resume_id", "resume_embeddings", ["resume_id"], unique=False)
    op.create_index("ix_resume_embeddings_section_type", "resume_embeddings", ["section_type"], unique=False)
    op.create_index("ix_resume_embeddings_created_at", "resume_embeddings", ["created_at"], unique=False)
    op.create_index("ix_resume_embeddings_resume_section", "resume_embeddings", ["resume_id", "section_type"], unique=False)
    
    # Vector index for semantic search would be created here IF pgvector is available
    # CREATE INDEX ix_resume_embeddings_cosine ON resume_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


def downgrade() -> None:
    # Drop in reverse order of creation
    # Note: Vector index (ix_resume_embeddings_cosine) is not dropped since it was never created
    op.drop_index("ix_resume_embeddings_resume_section", table_name="resume_embeddings")
    op.drop_index("ix_resume_embeddings_created_at", table_name="resume_embeddings")
    op.drop_index("ix_resume_embeddings_section_type", table_name="resume_embeddings")
    op.drop_index("ix_resume_embeddings_resume_id", table_name="resume_embeddings")
    op.drop_table("resume_embeddings")

    op.drop_index("ix_company_sectors_last_updated", table_name="company_sectors")
    op.drop_index("ix_company_sectors_source", table_name="company_sectors")
    op.drop_index("ix_company_sectors_sector", table_name="company_sectors")
    op.drop_index("ix_company_sectors_company_name", table_name="company_sectors")
    op.drop_table("company_sectors")

    op.drop_index("ix_generated_resume_id_format", table_name="generated_resumes")
    op.drop_index("ix_generated_resumes_generated_at", table_name="generated_resumes")
    op.drop_index("ix_generated_resumes_format", table_name="generated_resumes")
    op.drop_index("ix_generated_resumes_template_id", table_name="generated_resumes")
    op.drop_index("ix_generated_resumes_resume_id", table_name="generated_resumes")
    op.drop_table("generated_resumes")

    op.drop_index("ix_templates_user_active", table_name="resume_templates")
    op.drop_index("ix_templates_type", table_name="resume_templates")
    op.drop_index("ix_templates_is_active", table_name="resume_templates")
    op.drop_index("ix_templates_user_id", table_name="resume_templates")
    op.drop_index("ix_templates_template_id", table_name="resume_templates")
    op.drop_table("resume_templates")

    op.drop_index("ix_resumes_user_status", table_name="resumes")
    op.drop_index("ix_resumes_user_id_created_at", table_name="resumes")
    op.drop_index("ix_resumes_created_at", table_name="resumes")
    op.drop_index("ix_resumes_status", table_name="resumes")
    op.drop_index("ix_resumes_session_id", table_name="resumes")
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")

    # Extension drop not needed since we don't create the extension in upgrade

