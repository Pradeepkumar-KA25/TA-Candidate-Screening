"""add candidate search indexes

Revision ID: 202608030001
Revises: 202607310002
Create Date: 2026-08-03 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202608030001"
down_revision = "202607310002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind is not None else "postgresql"

    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_candidates_search_full_name ON candidates USING gin (lower(full_name) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_candidates_search_current_company ON candidates USING gin (lower(current_company) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_candidates_search_skills ON candidates USING gin ((lower(CAST(skills AS text))) gin_trgm_ops)"
        )
        return

    op.create_index("ix_candidates_search_full_name", "candidates", ["full_name"], unique=False)
    op.create_index("ix_candidates_search_current_company", "candidates", ["current_company"], unique=False)
    op.create_index("ix_candidates_search_skills", "candidates", ["skills"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind is not None else "postgresql"

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_candidates_search_skills")
        op.execute("DROP INDEX IF EXISTS ix_candidates_search_current_company")
        op.execute("DROP INDEX IF EXISTS ix_candidates_search_full_name")
        return

    op.drop_index("ix_candidates_search_skills", table_name="candidates")
    op.drop_index("ix_candidates_search_current_company", table_name="candidates")
    op.drop_index("ix_candidates_search_full_name", table_name="candidates")
