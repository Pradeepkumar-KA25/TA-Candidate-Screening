"""create integration settings table

Revision ID: 202607280001
Revises: 202607240001
Create Date: 2026-07-28 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202607280001"
down_revision = "202607240001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_settings",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'disconnected'")),
        sa.Column("connection_state", sa.String(length=32), nullable=False, server_default=sa.text("'disconnected'")),
        sa.Column("access_level", sa.String(length=32), nullable=False, server_default=sa.text("'read_only'")),
        sa.Column("sync_type", sa.String(length=32), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("provider", name="uq_integration_settings_provider"),
    )
    op.create_index("ix_integration_settings_provider", "integration_settings", ["provider"], unique=True)
    op.create_index("ix_integration_settings_status", "integration_settings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_integration_settings_status", table_name="integration_settings")
    op.drop_index("ix_integration_settings_provider", table_name="integration_settings")
    op.drop_table("integration_settings")
