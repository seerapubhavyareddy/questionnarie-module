"""Add scoring_config column to questionnaires table.

Revision ID: 002_add_scoring_config
Revises: 001_initial_questionnaire
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '002_add_scoring_config'
down_revision = '001_initial_questionnaire'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add scoring_config column to questionnaires table."""
    op.add_column(
        'questionnaires',
        sa.Column('scoring_config', JSON, nullable=True)
    )


def downgrade() -> None:
    """Remove scoring_config column from questionnaires table."""
    op.drop_column('questionnaires', 'scoring_config')
