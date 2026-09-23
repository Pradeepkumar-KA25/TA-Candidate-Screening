"""Fix proposed_field_changes to use JSON columns instead of VARCHAR.

Revision ID: 202609210002
Revises: 202609210001
Create Date: 2026-09-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202609210002'
down_revision = '202609210001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert existing VARCHAR/TEXT columns to JSON columns
    # First, alter the columns to use JSON type with casting
    
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN existing_zoho_value TYPE jsonb USING 
                CASE 
                    WHEN existing_zoho_value IS NULL THEN NULL
                    WHEN existing_zoho_value = '' THEN NULL
                    ELSE to_jsonb(existing_zoho_value::json) 
                END
        """)
    )
    
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN extracted_resume_value TYPE jsonb USING 
                CASE 
                    WHEN extracted_resume_value IS NULL THEN NULL
                    WHEN extracted_resume_value = '' THEN NULL
                    ELSE to_jsonb(extracted_resume_value::json)
                END
        """)
    )
    
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN proposed_value TYPE jsonb USING 
                CASE 
                    WHEN proposed_value IS NULL THEN NULL
                    WHEN proposed_value = '' THEN NULL
                    ELSE to_jsonb(proposed_value::json)
                END
        """)
    )


def downgrade() -> None:
    # Revert back to TEXT columns
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN existing_zoho_value TYPE text USING existing_zoho_value::text
        """)
    )
    
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN extracted_resume_value TYPE text USING extracted_resume_value::text
        """)
    )
    
    op.execute(
        sa.text("""
            ALTER TABLE proposed_field_changes
            ALTER COLUMN proposed_value TYPE text USING proposed_value::text
        """)
    )
