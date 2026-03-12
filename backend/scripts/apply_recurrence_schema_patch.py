from sqlalchemy import text

from app.database import engine


STATEMENTS = [
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recurrence_type_enum') THEN
            CREATE TYPE recurrence_type_enum AS ENUM ('one_time','weekly','monthly','custom');
        END IF;
    END
    $$;
    """,
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS recurrence_type recurrence_type_enum NOT NULL DEFAULT 'one_time';",
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS recurrence_config JSON NOT NULL DEFAULT '{}'::json;",
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS max_visits INTEGER NULL;",
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS window_duration_minutes INTEGER NULL;",
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS start_at_utc TIMESTAMPTZ NULL;",
    "ALTER TABLE trial_questionnaires ADD COLUMN IF NOT EXISTS end_at_utc TIMESTAMPTZ NULL;",
    "ALTER TABLE participant_questionnaire_responses ADD COLUMN IF NOT EXISTS visit_number INTEGER NOT NULL DEFAULT 1;",
    "ALTER TABLE participant_questionnaire_responses DROP CONSTRAINT IF EXISTS uq_participant_trial_questionnaire_response;",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_participant_trial_questionnaire_visit'
        ) THEN
            ALTER TABLE participant_questionnaire_responses
            ADD CONSTRAINT uq_participant_trial_questionnaire_visit
            UNIQUE (customer_id, trial_id, questionnaire_id, visit_number);
        END IF;
    END
    $$;
    """,
]


def main() -> None:
    with engine.begin() as conn:
        for statement in STATEMENTS:
            conn.execute(text(statement))
    print("schema_patch_applied")


if __name__ == "__main__":
    main()
