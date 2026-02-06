"""
Pydantic schemas for Questionnaire API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# =============================================================================
# Enums (matching SQLAlchemy enums)
# =============================================================================

class QuestionnaireStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class QuestionnaireType(str, Enum):
    ELIGIBILITY = "eligibility"
    SCREENING = "screening"
    BASELINE = "baseline"
    FOLLOW_UP = "follow_up"
    ADVERSE_EVENT = "adverse_event"
    QUALITY_OF_LIFE = "quality_of_life"
    CUSTOM = "custom"


class QuestionType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    DROPDOWN = "dropdown"
    RATING = "rating"
    SCALE = "scale"
    YES_NO = "yes_no"
    FILE_UPLOAD = "file_upload"
    SECTION_HEADER = "section_header"


# =============================================================================
# Question-related schemas
# =============================================================================

class QuestionOption(BaseModel):
    """Schema for question options (for choice-based questions)."""
    label: str = Field(..., min_length=1, max_length=500, description="Display label for the option")
    value: str = Field(..., min_length=1, max_length=255, description="Value stored when option is selected")
    score: Optional[int] = Field(None, description="Optional score value for scoring questionnaires")

    model_config = ConfigDict(extra="ignore")


class QuestionValidation(BaseModel):
    """Validation rules for a question."""
    minLength: Optional[int] = Field(None, ge=0, description="Minimum text length")
    maxLength: Optional[int] = Field(None, ge=1, description="Maximum text length")
    min: Optional[float] = Field(None, description="Minimum numeric value")
    max: Optional[float] = Field(None, description="Maximum numeric value")
    pattern: Optional[str] = Field(None, max_length=500, description="Regex pattern for validation")
    customError: Optional[str] = Field(None, max_length=500, description="Custom error message")

    model_config = ConfigDict(extra="ignore")


class ConditionalLogicCondition(BaseModel):
    """Condition for showing/hiding a question."""
    questionId: str = Field(..., description="ID of the question to check")
    operator: str = Field(..., description="Comparison operator: equals, not_equals, contains, greater_than, less_than")
    value: Any = Field(..., description="Value to compare against")

    model_config = ConfigDict(extra="ignore")


class ConditionalLogic(BaseModel):
    """Conditional logic settings for a question."""
    enabled: bool = Field(False, description="Whether conditional logic is enabled")
    showIf: Optional[ConditionalLogicCondition] = Field(None, description="Condition to show this question")

    model_config = ConfigDict(extra="ignore")


class Question(BaseModel):
    """Schema for a single question."""
    id: str = Field(..., min_length=1, max_length=50, description="Unique question identifier (UUID)")
    text: str = Field(..., min_length=1, max_length=2000, description="Question text")
    type: QuestionType = Field(..., description="Type of question")
    isRequired: bool = Field(False, description="Whether the question is required")
    order: int = Field(..., ge=0, description="Display order of the question")
    options: Optional[List[QuestionOption]] = Field(None, description="Options for choice questions")
    validation: Optional[QuestionValidation] = Field(None, description="Validation rules")
    conditionalLogic: Optional[ConditionalLogic] = Field(None, description="Conditional display logic")
    helpText: Optional[str] = Field(None, max_length=1000, description="Help text for the question")
    placeholder: Optional[str] = Field(None, max_length=255, description="Placeholder text")
    
    # Scale-specific fields
    scaleMin: Optional[int] = Field(None, description="Minimum value for scale questions")
    scaleMax: Optional[int] = Field(None, description="Maximum value for scale questions")
    scaleMinLabel: Optional[str] = Field(None, max_length=100, description="Label for minimum value")
    scaleMaxLabel: Optional[str] = Field(None, max_length=100, description="Label for maximum value")

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# Questionnaire Settings
# =============================================================================

class QuestionnaireSettings(BaseModel):
    """Settings for questionnaire behavior."""
    allowSaveProgress: bool = Field(True, description="Allow saving progress")
    showProgressBar: bool = Field(True, description="Show progress bar")
    randomizeQuestions: bool = Field(False, description="Randomize question order")
    timeLimit: Optional[int] = Field(None, ge=1, description="Time limit in minutes")
    submitButtonText: str = Field("Submit", max_length=50, description="Submit button text")
    successMessage: str = Field(
        "Thank you for completing the questionnaire.",
        max_length=1000,
        description="Message shown after submission"
    )

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# Scoring Configuration Schemas
# =============================================================================

class ScoringType(str, Enum):
    """Types of scoring systems supported."""
    SIMPLE_SUM = "simple_sum"          # Simple sum of all scores
    SUBSCALE = "subscale"              # Subscale-based (like DASS-21, PHQ-9)
    WEIGHTED = "weighted"              # Weighted scoring
    CUSTOM = "custom"                  # Custom formula/rules


class MissingValueHandling(str, Enum):
    """How to handle missing values in scoring."""
    ZERO = "zero"                      # Treat as 0
    SKIP = "skip"                      # Skip in calculation
    AVERAGE = "average"                # Use average of answered questions


class SeverityLevel(str, Enum):
    """Standard severity levels."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class SeverityRange(BaseModel):
    """A range mapping scores to severity levels."""
    min: float = Field(..., description="Minimum score for this range (inclusive)")
    max: Optional[float] = Field(None, description="Maximum score for this range (inclusive), null for no upper limit")
    label: str = Field(..., max_length=100, description="Display label (e.g., 'Mild Depression')")
    severity: SeverityLevel = Field(..., description="Severity classification")

    model_config = ConfigDict(extra="ignore")


class Subscale(BaseModel):
    """A subscale grouping for scoring."""
    name: str = Field(..., min_length=1, max_length=100, description="Display name (e.g., 'Depression')")
    key: str = Field(..., min_length=1, max_length=50, description="Unique key for this subscale")
    questionIds: List[str] = Field(..., min_length=1, description="List of question IDs in this subscale")
    multiplier: Optional[float] = Field(1.0, ge=0, description="Multiplier for subscale total (e.g., 2 for DASS-21)")
    severityRanges: Optional[List[SeverityRange]] = Field(None, description="Severity ranges for this subscale")

    model_config = ConfigDict(extra="ignore")


class TotalScoreConfig(BaseModel):
    """Configuration for overall total score."""
    enabled: bool = Field(True, description="Whether to calculate total score")
    maxScore: Optional[float] = Field(None, ge=0, description="Maximum possible score")
    severityRanges: Optional[List[SeverityRange]] = Field(None, description="Overall severity ranges")

    model_config = ConfigDict(extra="ignore")


class ScoringRules(BaseModel):
    """Rules governing score calculation."""
    defaultScore: float = Field(0, description="Default score for unscored options")
    missingValueHandling: MissingValueHandling = Field(
        MissingValueHandling.ZERO, 
        description="How to handle missing/unanswered questions"
    )

    model_config = ConfigDict(extra="ignore")


class ScoringConfig(BaseModel):
    """
    Complete scoring configuration for a questionnaire.
    
    Supports multiple scoring types:
    - SIMPLE_SUM: Add up scores from all questions
    - SUBSCALE: Group questions into subscales (like DASS-21, PHQ-9)
    - WEIGHTED: Apply different weights to questions
    - CUSTOM: Custom scoring rules
    """
    enabled: bool = Field(False, description="Whether scoring is enabled for this questionnaire")
    type: ScoringType = Field(ScoringType.SIMPLE_SUM, description="Type of scoring system")
    subscales: Optional[List[Subscale]] = Field(None, description="Subscale definitions (for SUBSCALE type)")
    totalScore: Optional[TotalScoreConfig] = Field(None, description="Total score configuration")
    passingScore: Optional[float] = Field(None, description="Passing score threshold (for eligibility)")
    scoringRules: Optional[ScoringRules] = Field(None, description="Additional scoring rules")

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# Questionnaire CRUD Schemas
# =============================================================================

class QuestionnaireBase(BaseModel):
    """Base schema for questionnaire data."""
    name: str = Field(..., min_length=1, max_length=255, description="Questionnaire name")
    description: Optional[str] = Field(None, max_length=2000, description="Questionnaire description")
    type: QuestionnaireType = Field(QuestionnaireType.CUSTOM, description="Type of questionnaire")

    model_config = ConfigDict(extra="ignore")


class QuestionnaireCreate(QuestionnaireBase):
    """Schema for creating a new questionnaire."""
    questions: List[Question] = Field(default_factory=list, description="List of questions")
    settings: Optional[QuestionnaireSettings] = Field(None, description="Questionnaire settings")
    status: QuestionnaireStatus = Field(QuestionnaireStatus.DRAFT, description="Initial status")
    scoring_config: Optional[ScoringConfig] = Field(None, description="Scoring configuration")


class QuestionnaireUpdate(BaseModel):
    """Schema for updating an existing questionnaire."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    type: Optional[QuestionnaireType] = None
    status: Optional[QuestionnaireStatus] = None
    questions: Optional[List[Question]] = None
    settings: Optional[QuestionnaireSettings] = None
    scoring_config: Optional[ScoringConfig] = Field(None, description="Scoring configuration")

    model_config = ConfigDict(extra="ignore")


class QuestionnaireResponse(BaseModel):
    """Schema for questionnaire response (read operations)."""
    id: int
    name: str
    description: Optional[str]
    type: QuestionnaireType
    status: QuestionnaireStatus
    questions: List[Dict[str, Any]]
    settings: Dict[str, Any]
    scoring_config: Optional[Dict[str, Any]] = None
    version: int
    is_deleted: bool
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionnaireListItem(BaseModel):
    """Schema for questionnaire list view (minimal data)."""
    id: int
    name: str
    description: Optional[str]
    type: QuestionnaireType
    status: QuestionnaireStatus
    question_count: int = Field(..., description="Number of questions")
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionnaireList(BaseModel):
    """Paginated list of questionnaires."""
    items: List[QuestionnaireListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Version History Schemas
# =============================================================================

class QuestionnaireVersionResponse(BaseModel):
    """Schema for questionnaire version history."""
    id: int
    questionnaire_id: int
    version_number: int
    snapshot: Dict[str, Any]
    change_summary: Optional[str]
    changed_by: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operations."""
    ids: List[int] = Field(..., min_length=1, description="List of questionnaire IDs to delete")


class BulkStatusUpdateRequest(BaseModel):
    """Schema for bulk status update."""
    ids: List[int] = Field(..., min_length=1, description="List of questionnaire IDs")
    status: QuestionnaireStatus = Field(..., description="New status to apply")


# =============================================================================
# Clone/Duplicate
# =============================================================================

class QuestionnaireCloneRequest(BaseModel):
    """Schema for cloning a questionnaire."""
    new_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name for the cloned questionnaire")


# =============================================================================
# Scoring Calculation Schemas (for API responses)
# =============================================================================

class SubscaleScoreResult(BaseModel):
    """Result for a single subscale."""
    name: str = Field(..., description="Subscale name")
    key: str = Field(..., description="Subscale key")
    rawScore: float = Field(..., description="Raw score before multiplier")
    score: float = Field(..., description="Final score after multiplier")
    maxPossible: Optional[float] = Field(None, description="Maximum possible score")
    percentage: Optional[float] = Field(None, description="Score as percentage of max")
    severity: Optional[str] = Field(None, description="Severity level if applicable")
    severityLabel: Optional[str] = Field(None, description="Severity display label")
    questionsAnswered: int = Field(..., description="Number of questions answered in this subscale")
    questionsTotal: int = Field(..., description="Total questions in this subscale")


class ScoringResult(BaseModel):
    """Complete scoring result for a questionnaire response."""
    questionnaireId: int = Field(..., description="Questionnaire ID")
    scoringType: ScoringType = Field(..., description="Type of scoring used")
    totalScore: Optional[float] = Field(None, description="Total score")
    maxPossibleScore: Optional[float] = Field(None, description="Maximum possible score")
    percentage: Optional[float] = Field(None, description="Score as percentage")
    passed: Optional[bool] = Field(None, description="Whether passing score was met (for eligibility)")
    severity: Optional[str] = Field(None, description="Overall severity level")
    severityLabel: Optional[str] = Field(None, description="Overall severity display label")
    subscales: Optional[List[SubscaleScoreResult]] = Field(None, description="Individual subscale scores")
    calculatedAt: datetime = Field(..., description="When the score was calculated")
    warnings: Optional[List[str]] = Field(None, description="Any warnings during calculation")

    model_config = ConfigDict(extra="ignore")


class CalculateScoreRequest(BaseModel):
    """Request to calculate score for responses."""
    responses: Dict[str, Any] = Field(..., description="Map of question ID to answer value")
    questions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Optional: current questions for preview scoring (overrides saved questions)"
    )

    model_config = ConfigDict(extra="ignore")
