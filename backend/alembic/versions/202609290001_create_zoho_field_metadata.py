"""Create cached Zoho field metadata."""

from alembic import op
import sqlalchemy as sa


revision = "202609290001"
down_revision = "202609280001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zoho_field_metadata",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("api_name", sa.String(length=128), nullable=False),
        sa.Column("display_label", sa.String(length=255), nullable=False),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("provider", "module", "api_name", name="uq_zoho_field_metadata_field"),
    )
    op.create_index("ix_zoho_field_metadata_provider_module", "zoho_field_metadata", ["provider", "module"])


def downgrade() -> None:
    op.drop_index("ix_zoho_field_metadata_provider_module", table_name="zoho_field_metadata")
    op.drop_table("zoho_field_metadata")