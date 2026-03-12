"""
API routes for linking questionnaires to trials (Phase 3).

Endpoints:
- POST   /api/trials/{trial_id}/questionnaires
- GET    /api/trials/{trial_id}/questionnaires
- PUT    /api/trials/{trial_id}/questionnaires/{questionnaire_id}
- DELETE /api/trials/{trial_id}/questionnaires/{questionnaire_id}
"""
from typing import List, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.questionnaire import (
    Questionnaire as QuestionnaireModel,
    TrialQuestionnaire as TrialQuestionnaireModel,
)
from app.schemas.questionnaire import (
    QuestionnaireResponse,
    QuestionnaireStatus,
    QuestionnaireType,
    TrialQuestionnaireCreate,
    TrialQuestionnaireBulkUpsertRequest,
    TrialQuestionnaireResponse,
    TrialQuestionnaireUpdate,
)

router = APIRouter(prefix="/api/trials", tags=["Trial Questionnaires"])
vendor_router = APIRouter(prefix="/api/vendor/trials", tags=["Vendor Trial Questionnaires"])


def _build_link_response(link: TrialQuestionnaireModel) -> TrialQuestionnaireResponse:
    questionnaire = link.questionnaire
    return TrialQuestionnaireResponse(
        id=link.id,
        trial_id=link.trial_id,
        questionnaire_id=link.questionnaire_id,
        is_required=link.is_required,
        display_order=link.display_order,
        recurrence_type=link.recurrence_type.value if link.recurrence_type else "one_time",
        recurrence_config=link.recurrence_config or {},
        max_visits=link.max_visits,
        window_duration_minutes=link.window_duration_minutes,
        start_at_utc=link.start_at_utc,
        end_at_utc=link.end_at_utc,
        linked_by=link.linked_by,
        linked_at=link.linked_at,
        updated_at=link.updated_at,
        questionnaire_name=questionnaire.name if questionnaire else None,
        questionnaire_description=questionnaire.description if questionnaire else None,
        questionnaire_type=questionnaire.type.value if questionnaire and questionnaire.type else None,
        questionnaire_status=questionnaire.status.value if questionnaire and questionnaire.status else None,
        question_count=len(questionnaire.questions or []) if questionnaire else 0,
    )


def _get_trial_questionnaire_link_or_404(
    db: Session,
    trial_id: int,
    questionnaire_id: int,
) -> TrialQuestionnaireModel:
    link = db.query(TrialQuestionnaireModel).filter(
        TrialQuestionnaireModel.trial_id == trial_id,
        TrialQuestionnaireModel.questionnaire_id == questionnaire_id,
    ).first()
    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Questionnaire {questionnaire_id} is not linked to trial {trial_id}",
        )
    return link


def _assert_trial_owned_by_vendor(db: Session, trial_id: int, vendor_id: str) -> None:
    trial_row = db.execute(
        text(
            """
            SELECT trial_id
            FROM public.clinical_trial
            WHERE trial_id = :trial_id AND vendor_id = :vendor_id
            """
        ),
        {"trial_id": trial_id, "vendor_id": vendor_id},
    ).fetchone()
    if not trial_row:
        raise HTTPException(
            status_code=404,
            detail=f"Trial {trial_id} not found for vendor {vendor_id}",
        )


@router.post("/{trial_id}/questionnaires", response_model=TrialQuestionnaireResponse, status_code=201)
async def link_questionnaire_to_trial(
    trial_id: int,
    payload: TrialQuestionnaireCreate,
    db: Session = Depends(get_db),
):
    questionnaire = db.query(QuestionnaireModel).filter(
        QuestionnaireModel.id == payload.questionnaire_id,
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire {payload.questionnaire_id} not found")

    link = TrialQuestionnaireModel(
        trial_id=trial_id,
        questionnaire_id=payload.questionnaire_id,
        is_required=payload.is_required,
        display_order=payload.display_order,
        recurrence_type=payload.recurrence_type.value if payload.recurrence_type else "one_time",
        recurrence_config=payload.recurrence_config or {},
        max_visits=payload.max_visits,
        window_duration_minutes=payload.window_duration_minutes,
        start_at_utc=payload.start_at_utc,
        end_at_utc=payload.end_at_utc,
    )
    db.add(link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Questionnaire {payload.questionnaire_id} is already linked to trial {trial_id}",
        )

    db.refresh(link)
    return _build_link_response(link)


@router.get("/{trial_id}/questionnaires", response_model=List[TrialQuestionnaireResponse])
async def list_trial_questionnaires(
    trial_id: int,
    db: Session = Depends(get_db),
):
    links = db.query(TrialQuestionnaireModel).join(
        QuestionnaireModel,
        TrialQuestionnaireModel.questionnaire_id == QuestionnaireModel.id,
    ).filter(
        TrialQuestionnaireModel.trial_id == trial_id,
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).order_by(
        TrialQuestionnaireModel.display_order.asc(),
        TrialQuestionnaireModel.id.asc(),
    ).all()

    return [_build_link_response(link) for link in links]


@router.put("/{trial_id}/questionnaires", response_model=List[TrialQuestionnaireResponse])
async def replace_trial_questionnaires(
    trial_id: int,
    payload: TrialQuestionnaireBulkUpsertRequest,
    db: Session = Depends(get_db),
):
    """
    Atomically replace all questionnaire links for a trial.
    """
    try:
        questionnaire_ids = [link.questionnaire_id for link in payload.questionnaire_links]
        unique_ids: Set[int] = set(questionnaire_ids)

        if len(unique_ids) != len(questionnaire_ids):
            raise HTTPException(status_code=400, detail="Duplicate questionnaire IDs in payload")

        existing_count = db.query(QuestionnaireModel).filter(
            QuestionnaireModel.id.in_(unique_ids),
            QuestionnaireModel.is_deleted == False,  # noqa: E712
        ).count()
        if existing_count != len(unique_ids):
            raise HTTPException(status_code=404, detail="One or more questionnaires not found")

        db.query(TrialQuestionnaireModel).filter(
            TrialQuestionnaireModel.trial_id == trial_id
        ).delete(synchronize_session=False)

        for idx, link in enumerate(payload.questionnaire_links):
            db.add(
                TrialQuestionnaireModel(
                    trial_id=trial_id,
                    questionnaire_id=link.questionnaire_id,
                    is_required=link.is_required,
                    display_order=idx,
                    recurrence_type=link.recurrence_type.value if link.recurrence_type else "one_time",
                    recurrence_config=link.recurrence_config or {},
                    max_visits=link.max_visits,
                    window_duration_minutes=link.window_duration_minutes,
                    start_at_utc=link.start_at_utc,
                    end_at_utc=link.end_at_utc,
                )
            )

        db.commit()

        links = db.query(TrialQuestionnaireModel).join(
            QuestionnaireModel,
            TrialQuestionnaireModel.questionnaire_id == QuestionnaireModel.id,
        ).filter(
            TrialQuestionnaireModel.trial_id == trial_id,
            QuestionnaireModel.is_deleted == False,  # noqa: E712
        ).order_by(
            TrialQuestionnaireModel.display_order.asc(),
            TrialQuestionnaireModel.id.asc(),
        ).all()

        return [_build_link_response(link) for link in links]
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to replace trial questionnaire links: {str(e)}")


@router.put(
    "/{trial_id}/questionnaires/{questionnaire_id}",
    response_model=TrialQuestionnaireResponse,
)
async def update_trial_questionnaire_link(
    trial_id: int,
    questionnaire_id: int,
    payload: TrialQuestionnaireUpdate,
    db: Session = Depends(get_db),
):
    link = _get_trial_questionnaire_link_or_404(db, trial_id, questionnaire_id)

    if payload.is_required is not None:
        link.is_required = payload.is_required
    if payload.display_order is not None:
        link.display_order = payload.display_order
    if payload.recurrence_type is not None:
        link.recurrence_type = payload.recurrence_type.value
    if payload.recurrence_config is not None:
        link.recurrence_config = payload.recurrence_config
    if payload.max_visits is not None:
        link.max_visits = payload.max_visits
    if payload.window_duration_minutes is not None:
        link.window_duration_minutes = payload.window_duration_minutes
    if payload.start_at_utc is not None:
        link.start_at_utc = payload.start_at_utc
    if payload.end_at_utc is not None:
        link.end_at_utc = payload.end_at_utc

    db.commit()
    db.refresh(link)
    return _build_link_response(link)


@router.delete("/{trial_id}/questionnaires/{questionnaire_id}", status_code=204)
async def unlink_questionnaire_from_trial(
    trial_id: int,
    questionnaire_id: int,
    db: Session = Depends(get_db),
):
    link = _get_trial_questionnaire_link_or_404(db, trial_id, questionnaire_id)
    db.delete(link)
    db.commit()
    return None


@vendor_router.get("/{trial_id}/questionnaires", response_model=List[TrialQuestionnaireResponse])
async def vendor_list_trial_questionnaires(
    trial_id: int,
    vendor_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Vendor-scoped list endpoint with ownership enforcement.
    """
    _assert_trial_owned_by_vendor(db, trial_id, vendor_id)
    links = db.query(TrialQuestionnaireModel).join(
        QuestionnaireModel,
        TrialQuestionnaireModel.questionnaire_id == QuestionnaireModel.id,
    ).filter(
        TrialQuestionnaireModel.trial_id == trial_id,
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).order_by(
        TrialQuestionnaireModel.display_order.asc(),
        TrialQuestionnaireModel.id.asc(),
    ).all()
    return [_build_link_response(link) for link in links]


@vendor_router.get(
    "/{trial_id}/questionnaires/{questionnaire_id}",
    response_model=QuestionnaireResponse,
)
async def vendor_get_trial_questionnaire(
    trial_id: int,
    questionnaire_id: int,
    vendor_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Vendor-scoped questionnaire detail endpoint with ownership + link enforcement.
    """
    _assert_trial_owned_by_vendor(db, trial_id, vendor_id)
    _get_trial_questionnaire_link_or_404(db, trial_id, questionnaire_id)

    questionnaire = db.query(QuestionnaireModel).filter(
        QuestionnaireModel.id == questionnaire_id,
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire with ID {questionnaire_id} not found")

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
