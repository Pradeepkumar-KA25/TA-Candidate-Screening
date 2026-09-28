from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def _config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _create_users_table(engine: sa.Engine) -> None:
    metadata = sa.MetaData()
    sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    )
    metadata.create_all(engine)


def _assert_active_schema(engine: sa.Engine) -> None:
    inspector = sa.inspect(engine)
    assert {"kanini_resumes", "kanini_user_templates"}.issubset(
        inspector.get_table_names()
    )
    assert {
        "id",
        "user_id",
        "filename",
        "parsed_data",
        "extraction_status",
        "extraction_progress",
        "extraction_error",
        "extraction_model",
        "source_reference",
        "source_file_type",
        "created_at",
        "updated_at",
    }.issubset({
        column["name"]
        for column in inspector.get_columns("kanini_resumes")
    })
    assert {
        "ix_kanini_resumes_user_id",
        "ix_kanini_resumes_extraction_status",
    }.issubset(
        index["name"] for index in inspector.get_indexes("kanini_resumes")
    )
    assert "ix_kanini_user_templates_user_id" in {
        index["name"]
        for index in inspector.get_indexes("kanini_user_templates")
    }


def test_creates_active_resume_schema_after_noop_head(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'missing.db'}"
    engine = sa.create_engine(database_url, future=True)
    _create_users_table(engine)

    config = _config(database_url)
    command.stamp(config, "202609250003")
    command.upgrade(config, "head")

    _assert_active_schema(engine)
    engine.dispose()


def test_reconciles_historical_resume_schema_without_losing_rows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'historical.db'}"
    engine = sa.create_engine(database_url, future=True)
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
    )
    resumes = sa.Table(
        "kanini_resumes",
        metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    templates = sa.Table(
        "kanini_user_templates",
        metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("template_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_spec", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    metadata.create_all(engine)

    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    timestamp = datetime(2026, 9, 25)
    with engine.begin() as connection:
        connection.execute(users.insert().values(id=user_id))
        connection.execute(
            resumes.insert().values(
                id=resume_id,
                user_id=user_id,
                filename="existing.pdf",
                file_path="legacy/existing.pdf",
                parsed_data={"summary": "keep me"},
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    config = _config(database_url)
    command.stamp(config, "202609250003")
    command.upgrade(config, "head")

    _assert_active_schema(engine)
    with engine.connect() as connection:
        row = connection.execute(
            sa.select(resumes.c.filename, resumes.c.parsed_data).where(
                resumes.c.id == resume_id
            )
        ).one()
    assert row.filename == "existing.pdf"
    assert row.parsed_data == {"summary": "keep me"}
    engine.dispose()
