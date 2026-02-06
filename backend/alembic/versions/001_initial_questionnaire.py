"""Initial questionnaire tables

Revision ID: 001_initial_questionnaire
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_questionnaire'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    questionnaire_status_enum = postgresql.ENUM(
        'draft', 'active', 'archived',
        name='questionnaire_status_enum',
        create_type=True
    )
    questionnaire_type_enum = postgresql.ENUM(
        'eligibility', 'screening', 'baseline', 'follow_up',
        'adverse_event', 'quality_of_life', 'custom',
        name='questionnaire_type_enum',
        create_type=True
    )
    
    # Create questionnaires table
    op.create_table(
        'questionnaires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', questionnaire_type_enum, nullable=False, server_default='custom'),
        sa.Column('status', questionnaire_status_enum, nullable=False, server_default='draft'),
        sa.Column('questions', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_questionnaires_id', 'questionnaires', ['id'], unique=False)
    op.create_index('ix_questionnaires_name', 'questionnaires', ['name'], unique=False)
    op.create_index('ix_questionnaires_type', 'questionnaires', ['type'], unique=False)
    op.create_index('ix_questionnaires_status', 'questionnaires', ['status'], unique=False)
    op.create_index('ix_questionnaires_is_deleted', 'questionnaires', ['is_deleted'], unique=False)
    op.create_index('ix_questionnaires_status_type', 'questionnaires', ['status', 'type'], unique=False)
    op.create_index('ix_questionnaires_created_at', 'questionnaires', ['created_at'], unique=False)
    
    # Create questionnaire_versions table
    op.create_table(
        'questionnaire_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questionnaire_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('change_summary', sa.String(500), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for versions
    op.create_index('ix_questionnaire_versions_id', 'questionnaire_versions', ['id'], unique=False)
    op.create_index('ix_questionnaire_versions_qid', 'questionnaire_versions', ['questionnaire_id'], unique=False)
    op.create_index('ix_questionnaire_versions_qid_version', 'questionnaire_versions', ['questionnaire_id', 'version_number'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('questionnaire_versions')
    op.drop_table('questionnaires')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS questionnaire_status_enum')
    op.execute('DROP TYPE IF EXISTS questionnaire_type_enum')
