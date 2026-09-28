"""create active Kanini resume persistence tables

Revision ID: 202609250004
Revises: 202609250003
Create Date: 2026-09-25 00:04:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202609250004"
down_revision = "202609250003"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }


def _index_names(table_name: str) -> set[str]:
    return {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }


def _create_resume_table() -> None:
    op.create_table(
        "kanini_resumes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column(
            "extraction_status",
            sa.String(length=32),
            server_default=sa.text("'completed'"),
            nullable=False,
        ),
        sa.Column(
            "extraction_progress",
            sa.Integer(),
            server_default=sa.text("100"),
            nullable=False,
        ),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("extraction_model", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("source_file_type", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _reconcile_resume_table() -> None:
    columns = _column_names("kanini_resumes")
    extraction_columns = {
        "extraction_status": sa.Column(
            "extraction_status",
            sa.String(length=32),
            server_default=sa.text("'completed'"),
            nullable=False,
        ),
        "extraction_progress": sa.Column(
            "extraction_progress",
            sa.Integer(),
            server_default=sa.text("100"),
            nullable=False,
        ),
        "extraction_error": sa.Column("extraction_error", sa.Text(), nullable=True),
        "extraction_model": sa.Column(
            "extraction_model", sa.String(length=255), nullable=True
        ),
        "source_reference": sa.Column("source_reference", sa.Text(), nullable=True),
        "source_file_type": sa.Column(
            "source_file_type", sa.String(length=16), nullable=True
        ),
    }
    for column_name, column in extraction_columns.items():
        if column_name not in columns:
            op.add_column("kanini_resumes", column)

    # Historical Kanini tables required file_path. Keep its data, but allow the
    # current in-memory upload flow to insert rows without a legacy path.
    if "file_path" in columns and op.get_bind().dialect.name != "sqlite":
        op.alter_column(
            "kanini_resumes",
            "file_path",
            existing_type=sa.Text(),
            nullable=True,
        )


def _create_user_template_table() -> None:
    op.create_table(
        "kanini_user_templates",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_spec", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def upgrade() -> None:
    if "kanini_resumes" not in _table_names():
        _create_resume_table()
    else:
        _reconcile_resume_table()

    resume_indexes = _index_names("kanini_resumes")
    if "ix_kanini_resumes_user_id" not in resume_indexes:
        op.create_index(
            "ix_kanini_resumes_user_id",
            "kanini_resumes",
            ["user_id"],
            unique=False,
        )
    if "ix_kanini_resumes_extraction_status" not in resume_indexes:
        op.create_index(
            "ix_kanini_resumes_extraction_status",
            "kanini_resumes",
            ["extraction_status"],
            unique=False,
        )

    if "kanini_user_templates" not in _table_names():
        _create_user_template_table()

    if "ix_kanini_user_templates_user_id" not in _index_names(
        "kanini_user_templates"
    ):
        op.create_index(
            "ix_kanini_user_templates_user_id",
            "kanini_user_templates",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    tables = _table_names()
    if "kanini_user_templates" in tables:
        op.drop_table("kanini_user_templates")
    if "kanini_resumes" in tables:
        op.drop_table("kanini_resumes")
