"""
SQLAlchemy models for the Questionnaire Module.

Tables:
- questionnaires: Main questionnaire metadata
- questions: Individual questions (stored as JSON in questionnaire, but also as a model for reference)
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    Enum, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class QuestionnaireStatus(str, enum.Enum):
    """Status of a questionnaire."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class QuestionnaireType(str, enum.Enum):
    """Type/category of questionnaire."""
    ELIGIBILITY = "eligibility"
    SCREENING = "screening"
    BASELINE = "baseline"
    FOLLOW_UP = "follow_up"
    ADVERSE_EVENT = "adverse_event"
    QUALITY_OF_LIFE = "quality_of_life"
    CUSTOM = "custom"


class QuestionType(str, enum.Enum):
    """Types of questions supported."""
    TEXT = "text"                      # Single line text input
    TEXTAREA = "textarea"              # Multi-line text input
    NUMBER = "number"                  # Numeric input
    EMAIL = "email"                    # Email input
    PHONE = "phone"                    # Phone number input
    DATE = "date"                      # Date picker
    TIME = "time"                      # Time picker
    DATETIME = "datetime"              # Date and time picker
    SINGLE_CHOICE = "single_choice"    # Radio buttons
    MULTIPLE_CHOICE = "multiple_choice" # Checkboxes
    DROPDOWN = "dropdown"              # Select dropdown
    RATING = "rating"                  # Star rating or numeric scale
    SCALE = "scale"                    # Likert scale (1-5, 1-10, etc.)
    YES_NO = "yes_no"                  # Boolean yes/no
    FILE_UPLOAD = "file_upload"        # File attachment
    SECTION_HEADER = "section_header"  # Visual separator/header (not a question)


class ResponseStatus(str, enum.Enum):
    """Status of a participant questionnaire response."""
    DRAFT = "draft"
    SUBMITTED = "submitted"


class RecurrenceType(str, enum.Enum):
    """Recurrence cadence for trial-linked questionnaires."""
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class Questionnaire(Base):
    """
    Main questionnaire table.
    
    Stores questionnaire metadata and questions as JSON for flexibility.
    Questions JSON structure allows for complex nested question configurations
    without requiring multiple database joins.
    """
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Type and status
    type = Column(
        Enum(QuestionnaireType, name="questionnaire_type_enum", values_callable=lambda obj: [e.value for e in obj]),
        default=QuestionnaireType.CUSTOM,
        nullable=False,
        index=True
    )
    status = Column(
        Enum(QuestionnaireStatus, name="questionnaire_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        default=QuestionnaireStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Questions stored as JSON array
    # Each question object contains:
    # {
    #     "id": "uuid-string",
    #     "text": "Question text",
    #     "type": "text|single_choice|multiple_choice|...",
    #     "isRequired": true|false,
    #     "order": 1,
    #     "options": [{"label": "Option 1", "value": "opt1"}, ...],  # for choice questions
    #     "validation": {
    #         "minLength": 0,
    #         "maxLength": 500,
    #         "min": 0,
    #         "max": 100,
    #         "pattern": "regex",
    #         "customError": "Custom error message"
    #     },
    #     "conditionalLogic": {
    #         "enabled": true|false,
    #         "showIf": {
    #             "questionId": "uuid",
    #             "operator": "equals|contains|greater_than|less_than",
    #             "value": "answer value"
    #         }
    #     },
    #     "helpText": "Optional help text",
    #     "placeholder": "Placeholder text"
    # }
    questions = Column(JSON, default=list, nullable=False)
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    # Settings structure:
    # {
    #     "allowSaveProgress": true,
    #     "showProgressBar": true,
    #     "randomizeQuestions": false,
    #     "timeLimit": null | number (minutes),
    #     "submitButtonText": "Submit",
    #     "successMessage": "Thank you for completing the questionnaire."
    # }
    
    # Scoring configuration - flexible JSON to support different scoring systems
    scoring_config = Column(JSON, default=None, nullable=True)
    # Scoring config structure:
    # {
    #     "enabled": true|false,
    #     "type": "simple_sum|subscale|weighted|custom",
    #     "subscales": [
    #         {
    #             "name": "Depression",
    #             "key": "depression",
    #             "questionIds": ["q1", "q3", "q5"],
    #             "multiplier": 2,  # Optional multiplier (like DASS-21)
    #             "severityRanges": [
    #                 {"min": 0, "max": 9, "label": "Normal", "severity": "normal"},
    #                 {"min": 10, "max": 13, "label": "Mild", "severity": "mild"},
    #                 {"min": 14, "max": 20, "label": "Moderate", "severity": "moderate"},
    #                 {"min": 21, "max": 27, "label": "Severe", "severity": "severe"},
    #                 {"min": 28, "max": null, "label": "Extremely Severe", "severity": "extreme"}
    #             ]
    #         }
    #     ],
    #     "totalScore": {
    #         "enabled": true,
    #         "maxScore": 100,
    #         "severityRanges": [...]  # Optional overall severity
    #     },
    #     "passingScore": null | number,  # For eligibility/pass-fail
    #     "scoringRules": {
    #         "defaultScore": 0,
    #         "missingValueHandling": "zero|skip|average"
    #     }
    # }
    
    # Version tracking (for audit trail)
    version = Column(Integer, default=1, nullable=False)
    
    # Soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit fields
    created_by = Column(Integer, nullable=True)  # User ID who created
    updated_by = Column(Integer, nullable=True)  # User ID who last updated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_questionnaires_status_type', 'status', 'type'),
        Index('ix_questionnaires_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Questionnaire(id={self.id}, name='{self.name}', status='{self.status}')>"


class QuestionnaireVersion(Base):
    """
    Version history for questionnaires.
    Stores snapshots of questionnaire state for audit purposes.
    """
    __tablename__ = "questionnaire_versions"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    
    # Snapshot of questionnaire data at this version
    snapshot = Column(JSON, nullable=False)
    
    # Change metadata
    change_summary = Column(String(500), nullable=True)
    changed_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    questionnaire = relationship("Questionnaire", backref="versions")

    __table_args__ = (
        Index('ix_questionnaire_versions_qid_version', 'questionnaire_id', 'version_number'),
    )

    def __repr__(self):
        return f"<QuestionnaireVersion(questionnaire_id={self.questionnaire_id}, version={self.version_number})>"


class TrialQuestionnaire(Base):
    """
    Links questionnaires to trials with ordering and required/optional flags.

    `trial_id` references the trial entity in the clinical trials domain.
    We intentionally keep it as an integer field here (without FK) because
    trial records are managed by a separate module/database boundary.
    """
    __tablename__ = "trial_questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, nullable=False, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, index=True)

    is_required = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    recurrence_type = Column(
        Enum(RecurrenceType, name="recurrence_type_enum", values_callable=lambda obj: [e.value for e in obj]),
        default=RecurrenceType.ONE_TIME,
        nullable=False,
    )
    recurrence_config = Column(JSON, default=dict, nullable=False)
    max_visits = Column(Integer, nullable=True)
    window_duration_minutes = Column(Integer, nullable=True)
    start_at_utc = Column(DateTime(timezone=True), nullable=True)
    end_at_utc = Column(DateTime(timezone=True), nullable=True)

    linked_by = Column(Integer, nullable=True)
    linked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    questionnaire = relationship("Questionnaire", backref="trial_links")

    __table_args__ = (
        UniqueConstraint("trial_id", "questionnaire_id", name="uq_trial_questionnaire"),
        Index("ix_trial_questionnaires_trial_order", "trial_id", "display_order"),
    )

    def __repr__(self):
        return (
            f"<TrialQuestionnaire(id={self.id}, trial_id={self.trial_id}, "
            f"questionnaire_id={self.questionnaire_id})>"
        )


class ParticipantQuestionnaireResponse(Base):
    """
    Participant responses for a trial-linked questionnaire.

    One row per (customer, trial, questionnaire) is maintained and can move
    from draft -> submitted.
    """
    __tablename__ = "participant_questionnaire_responses"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False, index=True)
    trial_id = Column(Integer, nullable=False, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, index=True)

    questionnaire_version = Column(Integer, nullable=False, default=1)
    visit_number = Column(Integer, nullable=False, default=1)
    status = Column(
        Enum(ResponseStatus, name="response_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ResponseStatus.DRAFT,
        index=True,
    )
    responses = Column(JSON, nullable=False, default=dict)
    progress_percent = Column(Integer, nullable=False, default=0)
    score_result = Column(JSON, nullable=True)
    eligibility_passed = Column(Boolean, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    questionnaire = relationship("Questionnaire", backref="participant_responses")

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "trial_id",
            "questionnaire_id",
            "visit_number",
            name="uq_participant_trial_questionnaire_visit",
        ),
        Index("ix_pqr_customer_trial", "customer_id", "trial_id"),
        Index("ix_pqr_trial_questionnaire", "trial_id", "questionnaire_id"),
    )

    def __repr__(self):
        return (
            f"<ParticipantQuestionnaireResponse(id={self.id}, customer_id={self.customer_id}, "
            f"trial_id={self.trial_id}, questionnaire_id={self.questionnaire_id}, status={self.status})>"
        )
