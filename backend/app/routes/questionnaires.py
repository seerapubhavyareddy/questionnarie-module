"""
API routes for Questionnaire CRUD operations.

Endpoints:
- POST   /api/questionnaires           - Create questionnaire
- GET    /api/questionnaires           - List all questionnaires
- GET    /api/questionnaires/:id       - Get single questionnaire
- PUT    /api/questionnaires/:id       - Update questionnaire
- DELETE /api/questionnaires/:id       - Soft delete questionnaire
- POST   /api/questionnaires/:id/clone - Clone questionnaire
- GET    /api/questionnaires/:id/versions - Get version history
- POST   /api/questionnaires/bulk-delete - Bulk soft delete
- POST   /api/questionnaires/bulk-status - Bulk status update
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
import logging

from app.database import get_db
from app.models.questionnaire import (
    Questionnaire as QuestionnaireModel,
    QuestionnaireVersion as QuestionnaireVersionModel,
    QuestionnaireStatus as DBQuestionnaireStatus,
    QuestionnaireType as DBQuestionnaireType,
)
from app.schemas.questionnaire import (
    QuestionnaireCreate,
    QuestionnaireUpdate,
    QuestionnaireResponse,
    QuestionnaireListItem,
    QuestionnaireList,
    QuestionnaireVersionResponse,
    BulkDeleteRequest,
    BulkStatusUpdateRequest,
    QuestionnaireCloneRequest,
    QuestionnaireStatus,
    QuestionnaireType,
    CalculateScoreRequest,
    ScoringResult,
    ScoringConfig,
)
from app.services.scoring import calculate_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/questionnaires", tags=["Questionnaires"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_questionnaire_or_404(db: Session, questionnaire_id: int) -> QuestionnaireModel:
    """Get a questionnaire by ID or raise 404."""
    questionnaire = db.query(QuestionnaireModel).filter(
        QuestionnaireModel.id == questionnaire_id,
        QuestionnaireModel.is_deleted == False  # noqa: E712
    ).first()
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire with ID {questionnaire_id} not found")
    
    return questionnaire


def create_version_snapshot(questionnaire: QuestionnaireModel, change_summary: str = None, changed_by: int = None):
    """Create a version snapshot of the questionnaire."""
    return QuestionnaireVersionModel(
        questionnaire_id=questionnaire.id,
        version_number=questionnaire.version,
        snapshot={
            "name": questionnaire.name,
            "description": questionnaire.description,
            "type": questionnaire.type.value if questionnaire.type else None,
            "status": questionnaire.status.value if questionnaire.status else None,
            "questions": questionnaire.questions,
            "settings": questionnaire.settings,
        },
        change_summary=change_summary,
        changed_by=changed_by,
    )


def questionnaire_to_list_item(q: QuestionnaireModel) -> QuestionnaireListItem:
    """Convert a questionnaire model to a list item schema."""
    return QuestionnaireListItem(
        id=q.id,
        name=q.name,
        description=q.description,
        type=q.type.value if q.type else QuestionnaireType.CUSTOM,
        status=q.status.value if q.status else QuestionnaireStatus.DRAFT,
        question_count=len(q.questions) if q.questions else 0,
        version=q.version,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


# =============================================================================
# CREATE - POST /api/questionnaires
# =============================================================================

@router.post("", response_model=QuestionnaireResponse, status_code=201)
async def create_questionnaire(
    questionnaire_data: QuestionnaireCreate,
    db: Session = Depends(get_db),
    # current_user_id: int = Depends(get_current_user)  # TODO: Add auth
):
    """
    Create a new questionnaire.
    
    - **name**: Required. Name of the questionnaire (1-255 chars)
    - **description**: Optional description (up to 2000 chars)
    - **type**: Type of questionnaire (eligibility, screening, etc.)
    - **status**: Initial status (default: draft)
    - **questions**: Array of question objects
    - **settings**: Questionnaire settings object
    """
    try:
        # Convert enums and prepare data
        db_type = DBQuestionnaireType(questionnaire_data.type.value) if questionnaire_data.type else DBQuestionnaireType.CUSTOM
        db_status = DBQuestionnaireStatus(questionnaire_data.status.value) if questionnaire_data.status else DBQuestionnaireStatus.DRAFT
        
        # Convert questions to dict for JSON storage (mode='json' ensures enums are serialized as strings)
        questions_data = [q.model_dump(mode='json') for q in questionnaire_data.questions] if questionnaire_data.questions else []
        settings_data = questionnaire_data.settings.model_dump(mode='json') if questionnaire_data.settings else {}
        scoring_config_data = questionnaire_data.scoring_config.model_dump(mode='json') if questionnaire_data.scoring_config else None
        
        # Create questionnaire
        questionnaire = QuestionnaireModel(
            name=questionnaire_data.name,
            description=questionnaire_data.description,
            type=db_type,
            status=db_status,
            questions=questions_data,
            settings=settings_data,
            scoring_config=scoring_config_data,
            version=1,
            # created_by=current_user_id,  # TODO: Add auth
        )
        
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        
        # Create initial version snapshot
        version_snapshot = create_version_snapshot(
            questionnaire, 
            change_summary="Initial creation"
        )
        db.add(version_snapshot)
        db.commit()
        
        logger.info(f"Created questionnaire: {questionnaire.id} - {questionnaire.name}")
        
        return QuestionnaireResponse(
            id=questionnaire.id,
            name=questionnaire.name,
            description=questionnaire.description,
            type=questionnaire.type.value,
            status=questionnaire.status.value,
            questions=questionnaire.questions,
            settings=questionnaire.settings,
            scoring_config=questionnaire.scoring_config,
            version=questionnaire.version,
            is_deleted=questionnaire.is_deleted,
            created_by=questionnaire.created_by,
            updated_by=questionnaire.updated_by,
            created_at=questionnaire.created_at,
            updated_at=questionnaire.updated_at,
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating questionnaire: {str(e)}")


# =============================================================================
# READ - GET /api/questionnaires
# =============================================================================

@router.get("", response_model=QuestionnaireList)
async def list_questionnaires(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    type: Optional[QuestionnaireType] = Query(None, description="Filter by type"),
    status: Optional[QuestionnaireStatus] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
):
    """
    List all questionnaires with pagination, filtering, and sorting.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **search**: Search term for name/description
    - **type**: Filter by questionnaire type
    - **status**: Filter by status (draft, active, archived)
    - **sort_by**: Field to sort by (created_at, updated_at, name)
    - **sort_order**: Sort direction (asc, desc)
    """
    try:
        # Base query - exclude deleted
        query = db.query(QuestionnaireModel).filter(
            QuestionnaireModel.is_deleted == False  # noqa: E712
        )
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    QuestionnaireModel.name.ilike(search_term),
                    QuestionnaireModel.description.ilike(search_term)
                )
            )
        
        # Apply type filter
        if type:
            db_type = DBQuestionnaireType(type.value)
            query = query.filter(QuestionnaireModel.type == db_type)
        
        # Apply status filter
        if status:
            db_status = DBQuestionnaireStatus(status.value)
            query = query.filter(QuestionnaireModel.status == db_status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(QuestionnaireModel, sort_by, QuestionnaireModel.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        questionnaires = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        # Convert to list items
        items = [questionnaire_to_list_item(q) for q in questionnaires]
        
        return QuestionnaireList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.error(f"Error listing questionnaires: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing questionnaires: {str(e)}")


# =============================================================================
# READ - GET /api/questionnaires/:id
# =============================================================================

@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single questionnaire by ID.
    
    Returns the full questionnaire including all questions and settings.
    """
    questionnaire = get_questionnaire_or_404(db, questionnaire_id)
    
    return QuestionnaireResponse(
        id=questionnaire.id,
        name=questionnaire.name,
        description=questionnaire.description,
        type=questionnaire.type.value if questionnaire.type else QuestionnaireType.CUSTOM,
        status=questionnaire.status.value if questionnaire.status else QuestionnaireStatus.DRAFT,
        questions=questionnaire.questions or [],
        settings=questionnaire.settings or {},
        scoring_config=questionnaire.scoring_config,
        version=questionnaire.version,
        is_deleted=questionnaire.is_deleted,
        created_by=questionnaire.created_by,
        updated_by=questionnaire.updated_by,
        created_at=questionnaire.created_at,
        updated_at=questionnaire.updated_at,
    )


# =============================================================================
# UPDATE - PUT /api/questionnaires/:id
# =============================================================================

@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def update_questionnaire(
    questionnaire_id: int,
    questionnaire_data: QuestionnaireUpdate,
    db: Session = Depends(get_db),
    # current_user_id: int = Depends(get_current_user)  # TODO: Add auth
):
    """
    Update an existing questionnaire.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    Creates a new version snapshot for audit history.
    """
    try:
        questionnaire = get_questionnaire_or_404(db, questionnaire_id)
        
        # Track what changed for version summary
        changes = []
        
        # Update fields if provided
        if questionnaire_data.name is not None:
            if questionnaire_data.name != questionnaire.name:
                changes.append("name")
            questionnaire.name = questionnaire_data.name
            
        if questionnaire_data.description is not None:
            if questionnaire_data.description != questionnaire.description:
                changes.append("description")
            questionnaire.description = questionnaire_data.description
            
        if questionnaire_data.type is not None:
            new_type = DBQuestionnaireType(questionnaire_data.type.value)
            if new_type != questionnaire.type:
                changes.append("type")
            questionnaire.type = new_type
            
        if questionnaire_data.status is not None:
            new_status = DBQuestionnaireStatus(questionnaire_data.status.value)
            if new_status != questionnaire.status:
                changes.append("status")
            questionnaire.status = new_status
            
        if questionnaire_data.questions is not None:
            changes.append("questions")
            questionnaire.questions = [q.model_dump(mode='json') for q in questionnaire_data.questions]
            
        if questionnaire_data.settings is not None:
            changes.append("settings")
            questionnaire.settings = questionnaire_data.settings.model_dump(mode='json')
        
        if questionnaire_data.scoring_config is not None:
            changes.append("scoring_config")
            questionnaire.scoring_config = questionnaire_data.scoring_config.model_dump(mode='json')
        
        # Increment version
        questionnaire.version += 1
        # questionnaire.updated_by = current_user_id  # TODO: Add auth
        
        db.commit()
        db.refresh(questionnaire)
        
        # Create version snapshot
        change_summary = f"Updated: {', '.join(changes)}" if changes else "No changes"
        version_snapshot = create_version_snapshot(
            questionnaire,
            change_summary=change_summary
        )
        db.add(version_snapshot)
        db.commit()
        
        logger.info(f"Updated questionnaire {questionnaire_id}: {change_summary}")
        
        return QuestionnaireResponse(
            id=questionnaire.id,
            name=questionnaire.name,
            description=questionnaire.description,
            type=questionnaire.type.value if questionnaire.type else QuestionnaireType.CUSTOM,
            status=questionnaire.status.value if questionnaire.status else QuestionnaireStatus.DRAFT,
            questions=questionnaire.questions or [],
            settings=questionnaire.settings or {},
            scoring_config=questionnaire.scoring_config,
            version=questionnaire.version,
            is_deleted=questionnaire.is_deleted,
            created_by=questionnaire.created_by,
            updated_by=questionnaire.updated_by,
            created_at=questionnaire.created_at,
            updated_at=questionnaire.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating questionnaire {questionnaire_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating questionnaire: {str(e)}")


# =============================================================================
# DELETE - DELETE /api/questionnaires/:id (Soft Delete)
# =============================================================================

@router.delete("/{questionnaire_id}", status_code=204)
async def delete_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db),
    # current_user_id: int = Depends(get_current_user)  # TODO: Add auth
):
    """
    Soft delete a questionnaire.
    
    Sets is_deleted=True. The questionnaire can be restored if needed.
    """
    try:
        questionnaire = get_questionnaire_or_404(db, questionnaire_id)
        
        questionnaire.is_deleted = True
        questionnaire.status = DBQuestionnaireStatus.ARCHIVED
        # questionnaire.updated_by = current_user_id  # TODO: Add auth
        
        db.commit()
        
        logger.info(f"Soft deleted questionnaire {questionnaire_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting questionnaire {questionnaire_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting questionnaire: {str(e)}")


# =============================================================================
# CLONE - POST /api/questionnaires/:id/clone
# =============================================================================

@router.post("/{questionnaire_id}/clone", response_model=QuestionnaireResponse, status_code=201)
async def clone_questionnaire(
    questionnaire_id: int,
    clone_data: QuestionnaireCloneRequest = None,
    db: Session = Depends(get_db),
    # current_user_id: int = Depends(get_current_user)  # TODO: Add auth
):
    """
    Clone an existing questionnaire.
    
    Creates a new questionnaire with the same questions and settings.
    The cloned questionnaire starts with status=draft and version=1.
    """
    try:
        original = get_questionnaire_or_404(db, questionnaire_id)
        
        # Determine new name
        new_name = clone_data.new_name if clone_data and clone_data.new_name else f"{original.name} (Copy)"
        
        # Create cloned questionnaire
        cloned = QuestionnaireModel(
            name=new_name,
            description=original.description,
            type=original.type,
            status=DBQuestionnaireStatus.DRAFT,
            questions=original.questions.copy() if original.questions else [],
            settings=original.settings.copy() if original.settings else {},
            scoring_config=original.scoring_config.copy() if original.scoring_config else None,
            version=1,
            # created_by=current_user_id,  # TODO: Add auth
        )
        
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        
        # Create initial version snapshot
        version_snapshot = create_version_snapshot(
            cloned,
            change_summary=f"Cloned from questionnaire {questionnaire_id}"
        )
        db.add(version_snapshot)
        db.commit()
        
        logger.info(f"Cloned questionnaire {questionnaire_id} to {cloned.id}")
        
        return QuestionnaireResponse(
            id=cloned.id,
            name=cloned.name,
            description=cloned.description,
            type=cloned.type.value if cloned.type else QuestionnaireType.CUSTOM,
            status=cloned.status.value if cloned.status else QuestionnaireStatus.DRAFT,
            questions=cloned.questions or [],
            settings=cloned.settings or {},
            scoring_config=cloned.scoring_config,
            version=cloned.version,
            is_deleted=cloned.is_deleted,
            created_by=cloned.created_by,
            updated_by=cloned.updated_by,
            created_at=cloned.created_at,
            updated_at=cloned.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cloning questionnaire {questionnaire_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cloning questionnaire: {str(e)}")


# =============================================================================
# VERSION HISTORY - GET /api/questionnaires/:id/versions
# =============================================================================

@router.get("/{questionnaire_id}/versions", response_model=List[QuestionnaireVersionResponse])
async def get_questionnaire_versions(
    questionnaire_id: int,
    db: Session = Depends(get_db),
):
    """
    Get version history for a questionnaire.
    
    Returns all version snapshots ordered by version number (newest first).
    """
    # Verify questionnaire exists
    get_questionnaire_or_404(db, questionnaire_id)
    
    versions = db.query(QuestionnaireVersionModel).filter(
        QuestionnaireVersionModel.questionnaire_id == questionnaire_id
    ).order_by(QuestionnaireVersionModel.version_number.desc()).all()
    
    return [
        QuestionnaireVersionResponse(
            id=v.id,
            questionnaire_id=v.questionnaire_id,
            version_number=v.version_number,
            snapshot=v.snapshot,
            change_summary=v.change_summary,
            changed_by=v.changed_by,
            created_at=v.created_at,
        )
        for v in versions
    ]


# =============================================================================
# BULK OPERATIONS
# =============================================================================

@router.post("/bulk-delete", status_code=200)
async def bulk_delete_questionnaires(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    Soft delete multiple questionnaires at once.
    """
    try:
        deleted_count = db.query(QuestionnaireModel).filter(
            QuestionnaireModel.id.in_(request.ids),
            QuestionnaireModel.is_deleted == False  # noqa: E712
        ).update(
            {
                QuestionnaireModel.is_deleted: True,
                QuestionnaireModel.status: DBQuestionnaireStatus.ARCHIVED
            },
            synchronize_session=False
        )
        
        db.commit()
        
        logger.info(f"Bulk deleted {deleted_count} questionnaires")
        
        return {"deleted_count": deleted_count, "requested_ids": request.ids}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in bulk delete: {str(e)}")


@router.post("/bulk-status", status_code=200)
async def bulk_update_status(
    request: BulkStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update status for multiple questionnaires at once.
    """
    try:
        db_status = DBQuestionnaireStatus(request.status.value)
        
        updated_count = db.query(QuestionnaireModel).filter(
            QuestionnaireModel.id.in_(request.ids),
            QuestionnaireModel.is_deleted == False  # noqa: E712
        ).update(
            {QuestionnaireModel.status: db_status},
            synchronize_session=False
        )
        
        db.commit()
        
        logger.info(f"Bulk updated status to {request.status.value} for {updated_count} questionnaires")
        
        return {
            "updated_count": updated_count,
            "new_status": request.status.value,
            "requested_ids": request.ids
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk status update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in bulk status update: {str(e)}")


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/types/list", response_model=List[dict])
async def list_questionnaire_types():
    """Get all available questionnaire types."""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in QuestionnaireType
    ]


@router.get("/question-types/list", response_model=List[dict])
async def list_question_types():
    """Get all available question types."""
    from app.schemas.questionnaire import QuestionType
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in QuestionType
    ]


# =============================================================================
# SCORING ENDPOINTS
# =============================================================================

@router.post("/{questionnaire_id}/calculate-score", response_model=ScoringResult)
async def calculate_questionnaire_score(
    questionnaire_id: int,
    request: CalculateScoreRequest,
    db: Session = Depends(get_db),
):
    """
    Calculate score for questionnaire responses.
    
    - **questionnaire_id**: ID of the questionnaire
    - **responses**: Dict mapping question ID to answer value
    - **questions**: Optional - current questions for preview (overrides saved questions)
    
    Returns calculated scores including subscales if configured.
    """
    questionnaire = get_questionnaire_or_404(db, questionnaire_id)
    
    scoring_config = questionnaire.scoring_config or {}
    # Use provided questions if available (for preview with unsaved changes), otherwise use saved questions
    questions = request.questions if request.questions is not None else (questionnaire.questions or [])
    
    result = calculate_score(
        questionnaire_id=questionnaire_id,
        scoring_config=scoring_config,
        questions=questions,
        responses=request.responses
    )
    
    return result


@router.get("/{questionnaire_id}/scoring-config")
async def get_scoring_config(
    questionnaire_id: int,
    db: Session = Depends(get_db),
):
    """Get the scoring configuration for a questionnaire."""
    questionnaire = get_questionnaire_or_404(db, questionnaire_id)
    return {
        "questionnaire_id": questionnaire_id,
        "scoring_config": questionnaire.scoring_config,
        "has_scoring": questionnaire.scoring_config is not None and questionnaire.scoring_config.get('enabled', False)
    }


@router.put("/{questionnaire_id}/scoring-config")
async def update_scoring_config(
    questionnaire_id: int,
    scoring_config: ScoringConfig,
    db: Session = Depends(get_db),
):
    """Update the scoring configuration for a questionnaire."""
    questionnaire = get_questionnaire_or_404(db, questionnaire_id)
    
    questionnaire.scoring_config = scoring_config.model_dump(mode='json')
    questionnaire.version += 1
    
    db.commit()
    db.refresh(questionnaire)
    
    # Create version snapshot
    version_snapshot = create_version_snapshot(
        questionnaire,
        change_summary="Updated scoring configuration"
    )
    db.add(version_snapshot)
    db.commit()
    
    return {
        "message": "Scoring configuration updated",
        "questionnaire_id": questionnaire_id,
        "scoring_config": questionnaire.scoring_config
    }
