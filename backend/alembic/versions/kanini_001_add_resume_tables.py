"""Kanini Resume Schema - Add kanini resume tables

Revision ID: kanini_001
Revises: 
Create Date: 2026-09-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'kanini_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create kanini_resumes table
    op.create_table(
        'kanini_resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('parsed_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kanini_resumes_user_id'), 'kanini_resumes', ['user_id'], unique=False)

    # Create kanini_generated_resumes table
    op.create_table(
        'kanini_generated_resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kanini_resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', sa.String(50), nullable=False),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['kanini_resume_id'], ['kanini_resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kanini_generated_resumes_kanini_resume_id'), 'kanini_generated_resumes', ['kanini_resume_id'], unique=False)

    # Create kanini_user_templates table
    op.create_table(
        'kanini_user_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_spec', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kanini_user_templates_user_id'), 'kanini_user_templates', ['user_id'], unique=False)

    # Create kanini_template_drafts table
    op.create_table(
        'kanini_template_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_spec', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kanini_template_drafts_user_id'), 'kanini_template_drafts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kanini_template_drafts_user_id'), table_name='kanini_template_drafts')
    op.drop_table('kanini_template_drafts')
    op.drop_index(op.f('ix_kanini_user_templates_user_id'), table_name='kanini_user_templates')
    op.drop_table('kanini_user_templates')
    op.drop_index(op.f('ix_kanini_generated_resumes_kanini_resume_id'), table_name='kanini_generated_resumes')
    op.drop_table('kanini_generated_resumes')
    op.drop_index(op.f('ix_kanini_resumes_user_id'), table_name='kanini_resumes')
    op.drop_table('kanini_resumes')
