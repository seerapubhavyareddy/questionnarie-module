"""Add trial_questionnaires table.

Revision ID: 003_add_trial_questionnaires
Revises: 002_add_scoring_config
Create Date: 2026-03-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_add_trial_questionnaires"
down_revision = "002_add_scoring_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trial_questionnaires",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trial_id", sa.Integer(), nullable=False),
        sa.Column("questionnaire_id", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("linked_by", sa.Integer(), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["questionnaire_id"], ["questionnaires.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trial_id", "questionnaire_id", name="uq_trial_questionnaire"),
    )

    op.create_index("ix_trial_questionnaires_id", "trial_questionnaires", ["id"], unique=False)
    op.create_index("ix_trial_questionnaires_trial_id", "trial_questionnaires", ["trial_id"], unique=False)
    op.create_index(
        "ix_trial_questionnaires_questionnaire_id",
        "trial_questionnaires",
        ["questionnaire_id"],
        unique=False,
    )
    op.create_index(
        "ix_trial_questionnaires_trial_order",
        "trial_questionnaires",
        ["trial_id", "display_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trial_questionnaires_trial_order", table_name="trial_questionnaires")
    op.drop_index("ix_trial_questionnaires_questionnaire_id", table_name="trial_questionnaires")
    op.drop_index("ix_trial_questionnaires_trial_id", table_name="trial_questionnaires")
    op.drop_index("ix_trial_questionnaires_id", table_name="trial_questionnaires")
    op.drop_table("trial_questionnaires")
