"""create core recruitment tables

Revision ID: 202607290001
Revises: 202607280001
Create Date: 2026-07-29 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202607290001"
down_revision = "202607280001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("zoho_candidate_id", sa.String(length=128), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("relevant_experience_years", sa.Float(), nullable=True),
        sa.Column("current_company", sa.String(length=255), nullable=True),
        sa.Column("current_location", sa.String(length=255), nullable=True),
        sa.Column("preferred_location", sa.String(length=255), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("normalized_degree", sa.String(length=255), nullable=True),
        sa.Column("current_ctc", sa.Float(), nullable=True),
        sa.Column("expected_ctc", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("match_metadata", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default=sa.text("'zoho_recruit'")),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zoho_candidate_id", name="uq_candidates_zoho_candidate_id"),
    )
    op.create_index("ix_candidates_zoho_candidate_id", "candidates", ["zoho_candidate_id"], unique=True)
    op.create_index("ix_candidates_full_name", "candidates", ["full_name"], unique=False)
    op.create_index("ix_candidates_email", "candidates", ["email"], unique=False)
    op.create_index("ix_candidates_current_company", "candidates", ["current_company"], unique=False)
    op.create_index("ix_candidates_status", "candidates", ["status"], unique=False)

    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jd_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jd_code", name="uq_job_descriptions_jd_code"),
    )
    op.create_index("ix_job_descriptions_jd_code", "job_descriptions", ["jd_code"], unique=True)

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'running'")),
        sa.Column("records_fetched", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_new", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("triggered_by", sa.Uuid(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_logs_status", "sync_logs", ["status"], unique=False)
    op.create_index("ix_sync_logs_triggered_by", "sync_logs", ["triggered_by"], unique=False)

    op.create_table(
        "activity_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_log_actor_id", "activity_log", ["actor_id"], unique=False)
    op.create_index("ix_activity_log_action_type", "activity_log", ["action_type"], unique=False)
    op.create_index("ix_activity_log_occurred_at", "activity_log", ["occurred_at"], unique=False)

    op.create_table(
        "saved_filters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=True),
        sa.Column("filter_criteria", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_filters_recruiter_id", "saved_filters", ["recruiter_id"], unique=False)
    op.create_index("ix_saved_filters_jd_id", "saved_filters", ["jd_id"], unique=False)

    op.create_table(
        "duplicate_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("matched_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("match_basis", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matched_candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_duplicate_reviews_candidate_id", "duplicate_reviews", ["candidate_id"], unique=False)
    op.create_index("ix_duplicate_reviews_matched_candidate_id", "duplicate_reviews", ["matched_candidate_id"], unique=False)
    op.create_index("ix_duplicate_reviews_jd_id", "duplicate_reviews", ["jd_id"], unique=False)
    op.create_index("ix_duplicate_reviews_status", "duplicate_reviews", ["status"], unique=False)
    op.create_index("ix_duplicate_reviews_reviewed_by", "duplicate_reviews", ["reviewed_by"], unique=False)

    op.create_table(
        "ranking_criteria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=False),
        sa.Column("criteria_name", sa.String(length=255), nullable=False),
        sa.Column("weight_points", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ranking_criteria_jd_id", "ranking_criteria", ["jd_id"], unique=False)

    op.create_table(
        "shortlists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), nullable=False),
        sa.Column("jd_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["jd_id"], ["job_descriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shortlists_recruiter_id", "shortlists", ["recruiter_id"], unique=False)
    op.create_index("ix_shortlists_jd_id", "shortlists", ["jd_id"], unique=False)

    op.create_table(
        "shortlist_candidates",
        sa.Column("shortlist_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shortlist_id"], ["shortlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("shortlist_id", "candidate_id"),
    )
    op.create_index("ix_shortlist_candidates_candidate_id", "shortlist_candidates", ["candidate_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_shortlist_candidates_candidate_id", table_name="shortlist_candidates")
    op.drop_table("shortlist_candidates")

    op.drop_index("ix_shortlists_jd_id", table_name="shortlists")
    op.drop_index("ix_shortlists_recruiter_id", table_name="shortlists")
    op.drop_table("shortlists")

    op.drop_index("ix_ranking_criteria_jd_id", table_name="ranking_criteria")
    op.drop_table("ranking_criteria")

    op.drop_index("ix_duplicate_reviews_reviewed_by", table_name="duplicate_reviews")
    op.drop_index("ix_duplicate_reviews_status", table_name="duplicate_reviews")
    op.drop_index("ix_duplicate_reviews_jd_id", table_name="duplicate_reviews")
    op.drop_index("ix_duplicate_reviews_matched_candidate_id", table_name="duplicate_reviews")
    op.drop_index("ix_duplicate_reviews_candidate_id", table_name="duplicate_reviews")
    op.drop_table("duplicate_reviews")

    op.drop_index("ix_saved_filters_jd_id", table_name="saved_filters")
    op.drop_index("ix_saved_filters_recruiter_id", table_name="saved_filters")
    op.drop_table("saved_filters")

    op.drop_index("ix_activity_log_occurred_at", table_name="activity_log")
    op.drop_index("ix_activity_log_action_type", table_name="activity_log")
    op.drop_index("ix_activity_log_actor_id", table_name="activity_log")
    op.drop_table("activity_log")

    op.drop_index("ix_sync_logs_triggered_by", table_name="sync_logs")
    op.drop_index("ix_sync_logs_status", table_name="sync_logs")
    op.drop_table("sync_logs")

    op.drop_index("ix_job_descriptions_jd_code", table_name="job_descriptions")
    op.drop_table("job_descriptions")

    op.drop_index("ix_candidates_status", table_name="candidates")
    op.drop_index("ix_candidates_current_company", table_name="candidates")
    op.drop_index("ix_candidates_email", table_name="candidates")
    op.drop_index("ix_candidates_full_name", table_name="candidates")
    op.drop_index("ix_candidates_zoho_candidate_id", table_name="candidates")
    op.drop_table("candidates")
