"""Add participant questionnaire responses table.

Revision ID: 004_add_participant_questionnaire_responses
Revises: 003_add_trial_questionnaires
Create Date: 2026-03-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004_add_participant_questionnaire_responses"
down_revision = "003_add_trial_questionnaires"
branch_labels = None
depends_on = None


def upgrade() -> None:
    response_status_enum = sa.Enum(
        "draft",
        "submitted",
        name="response_status_enum",
    )
    response_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "participant_questionnaire_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("trial_id", sa.Integer(), nullable=False),
        sa.Column("questionnaire_id", sa.Integer(), nullable=False),
        sa.Column("questionnaire_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", response_status_enum, nullable=False, server_default="draft"),
        sa.Column("responses", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_result", sa.JSON(), nullable=True),
        sa.Column("eligibility_passed", sa.Boolean(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["questionnaire_id"], ["questionnaires.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_id",
            "trial_id",
            "questionnaire_id",
            name="uq_participant_trial_questionnaire_response",
        ),
    )

    op.create_index(
        "ix_participant_questionnaire_responses_id",
        "participant_questionnaire_responses",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_questionnaire_responses_customer_id",
        "participant_questionnaire_responses",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_questionnaire_responses_trial_id",
        "participant_questionnaire_responses",
        ["trial_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_questionnaire_responses_questionnaire_id",
        "participant_questionnaire_responses",
        ["questionnaire_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_questionnaire_responses_status",
        "participant_questionnaire_responses",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_pqr_customer_trial",
        "participant_questionnaire_responses",
        ["customer_id", "trial_id"],
        unique=False,
    )
    op.create_index(
        "ix_pqr_trial_questionnaire",
        "participant_questionnaire_responses",
        ["trial_id", "questionnaire_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pqr_trial_questionnaire", table_name="participant_questionnaire_responses")
    op.drop_index("ix_pqr_customer_trial", table_name="participant_questionnaire_responses")
    op.drop_index("ix_participant_questionnaire_responses_status", table_name="participant_questionnaire_responses")
    op.drop_index("ix_participant_questionnaire_responses_questionnaire_id", table_name="participant_questionnaire_responses")
    op.drop_index("ix_participant_questionnaire_responses_trial_id", table_name="participant_questionnaire_responses")
    op.drop_index("ix_participant_questionnaire_responses_customer_id", table_name="participant_questionnaire_responses")
    op.drop_index("ix_participant_questionnaire_responses_id", table_name="participant_questionnaire_responses")
    op.drop_table("participant_questionnaire_responses")

    response_status_enum = sa.Enum(
        "draft",
        "submitted",
        name="response_status_enum",
    )
    response_status_enum.drop(op.get_bind(), checkfirst=True)
