"""Add auto-sync columns to integration_settings table.

Revision ID: 202609150001
Revises: 202609080001
Create Date: 2026-09-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202609150001"
down_revision = "202609080001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auto_sync_enabled column
    op.add_column(
        "integration_settings",
        sa.Column(
            "auto_sync_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    # Add auto_sync_interval_minutes column
    op.add_column(
        "integration_settings",
        sa.Column(
            "auto_sync_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="5",
        ),
    )
    # Add last_auto_sync_at column
    op.add_column(
        "integration_settings",
        sa.Column(
            "last_auto_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    
    # Update existing records to use 5-minute interval
    op.execute(
        sa.text("UPDATE integration_settings SET auto_sync_interval_minutes = 5 WHERE auto_sync_interval_minutes IS NULL OR auto_sync_interval_minutes != 5")
    )


def downgrade() -> None:
    op.drop_column("integration_settings", "last_auto_sync_at")
    op.drop_column("integration_settings", "auto_sync_interval_minutes")
    op.drop_column("integration_settings", "auto_sync_enabled")
