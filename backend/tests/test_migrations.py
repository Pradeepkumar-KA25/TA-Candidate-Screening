from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.security import verify_password


def test_users_migration_round_trip(temp_sqlite_path) -> None:
    database_url = f"sqlite+pysqlite:///{temp_sqlite_path}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    assert {"id", "full_name", "email", "password_hash", "role", "is_active", "created_at", "updated_at"}.issubset(columns)

    with engine.connect() as connection:
        default_admin = connection.execute(
            text(
                "SELECT full_name, password_hash, role, is_active FROM users "
                "WHERE email = :email"
            ),
            {"email": "admin@talent.com"},
        ).mappings().one()

    assert default_admin["full_name"] == "Admin User"
    assert default_admin["role"] == "Admin"
    assert bool(default_admin["is_active"])
    assert verify_password("Secret123!", default_admin["password_hash"])

    integration_columns = {column["name"] for column in inspector.get_columns("integration_settings")}
    assert {
        "id",
        "provider",
        "status",
        "connection_state",
        "access_level",
        "sync_type",
        "access_token_encrypted",
        "refresh_token_encrypted",
        "token_expires_at",
        "last_checked_at",
        "last_successful_sync_at",
        "created_at",
        "updated_at",
    }.issubset(integration_columns)

    candidates_columns = {column["name"] for column in inspector.get_columns("candidates")}
    assert {
        "id",
        "zoho_record_id",
        "zoho_candidate_id",
        "full_name",
        "email",
        "skills",
        "match_metadata",
        "created_at",
        "updated_at",
    }.issubset(candidates_columns)

    candidate_indexes = {index["name"] for index in inspector.get_indexes("candidates")}
    assert {
        "ix_candidates_search_full_name",
        "ix_candidates_search_current_company",
        "ix_candidates_search_skills",
    }.issubset(candidate_indexes)

    sync_logs_columns = {column["name"] for column in inspector.get_columns("sync_logs")}
    assert {
        "id",
        "started_at",
        "completed_at",
        "status",
        "records_fetched",
        "records_new",
        "records_updated",
        "normalized_records",
        "normalization_examples",
        "triggered_by",
        "error_message",
    }.issubset(sync_logs_columns)

    activity_log_columns = {column["name"] for column in inspector.get_columns("activity_log")}
    assert {"id", "actor_id", "action_type", "description", "occurred_at"}.issubset(activity_log_columns)

    job_description_columns = {column["name"] for column in inspector.get_columns("job_descriptions")}
    assert {"id", "jd_code", "title", "required_skills", "created_at"}.issubset(job_description_columns)

    saved_filter_columns = {column["name"] for column in inspector.get_columns("saved_filters")}
    assert {
        "id",
        "recruiter_id",
        "name",
        "jd_id",
        "filter_criteria",
        "created_at",
        "updated_at",
    }.issubset(saved_filter_columns)

    duplicate_review_columns = {column["name"] for column in inspector.get_columns("duplicate_reviews")}
    assert {
        "id",
        "candidate_id",
        "matched_candidate_id",
        "match_basis",
        "confidence",
        "jd_id",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    }.issubset(duplicate_review_columns)

    ranking_criteria_columns = {column["name"] for column in inspector.get_columns("ranking_criteria")}
    assert {"id", "jd_id", "criteria_name", "weight_points", "created_at"}.issubset(ranking_criteria_columns)

    shortlist_columns = {column["name"] for column in inspector.get_columns("shortlists")}
    assert {"id", "recruiter_id", "jd_id", "created_at"}.issubset(shortlist_columns)

    shortlist_candidate_columns = {column["name"] for column in inspector.get_columns("shortlist_candidates")}
    assert {"shortlist_id", "candidate_id", "added_at"}.issubset(shortlist_candidate_columns)

    normalization_rule_columns = {column["name"] for column in inspector.get_columns("normalization_rules")}
    assert {
        "id",
        "field_type",
        "raw_value",
        "normalized_value",
        "created_at",
        "updated_at",
    }.issubset(normalization_rule_columns)

    command.downgrade(config, "base")
    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()
    assert "integration_settings" not in inspector.get_table_names()
    assert "sync_logs" not in inspector.get_table_names()
    assert "candidates" not in inspector.get_table_names()
    assert "activity_log" not in inspector.get_table_names()
    assert "job_descriptions" not in inspector.get_table_names()
    assert "saved_filters" not in inspector.get_table_names()
    assert "duplicate_reviews" not in inspector.get_table_names()
    assert "ranking_criteria" not in inspector.get_table_names()
    assert "shortlists" not in inspector.get_table_names()
    assert "shortlist_candidates" not in inspector.get_table_names()
    assert "normalization_rules" not in inspector.get_table_names()
    engine.dispose()
