"""Add recurrence fields and visit numbering.

Revision ID: 005_add_recurrence_and_visit_number
Revises: 004_add_participant_questionnaire_responses
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005_add_recurrence_and_visit_number"
down_revision = "004_add_participant_questionnaire_responses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    recurrence_type_enum = sa.Enum(
        "one_time",
        "weekly",
        "monthly",
        "custom",
        name="recurrence_type_enum",
    )
    recurrence_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "trial_questionnaires",
        sa.Column(
            "recurrence_type",
            recurrence_type_enum,
            nullable=False,
            server_default="one_time",
        ),
    )
    op.add_column(
        "trial_questionnaires",
        sa.Column("recurrence_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column("trial_questionnaires", sa.Column("max_visits", sa.Integer(), nullable=True))
    op.add_column("trial_questionnaires", sa.Column("window_duration_minutes", sa.Integer(), nullable=True))
    op.add_column("trial_questionnaires", sa.Column("start_at_utc", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trial_questionnaires", sa.Column("end_at_utc", sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        "participant_questionnaire_responses",
        sa.Column("visit_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.drop_constraint(
        "uq_participant_trial_questionnaire_response",
        "participant_questionnaire_responses",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_participant_trial_questionnaire_visit",
        "participant_questionnaire_responses",
        ["customer_id", "trial_id", "questionnaire_id", "visit_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_participant_trial_questionnaire_visit",
        "participant_questionnaire_responses",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_participant_trial_questionnaire_response",
        "participant_questionnaire_responses",
        ["customer_id", "trial_id", "questionnaire_id"],
    )
    op.drop_column("participant_questionnaire_responses", "visit_number")

    op.drop_column("trial_questionnaires", "end_at_utc")
    op.drop_column("trial_questionnaires", "start_at_utc")
    op.drop_column("trial_questionnaires", "window_duration_minutes")
    op.drop_column("trial_questionnaires", "max_visits")
    op.drop_column("trial_questionnaires", "recurrence_config")
    op.drop_column("trial_questionnaires", "recurrence_type")

    recurrence_type_enum = sa.Enum(
        "one_time",
        "weekly",
        "monthly",
        "custom",
        name="recurrence_type_enum",
    )
    recurrence_type_enum.drop(op.get_bind(), checkfirst=True)
