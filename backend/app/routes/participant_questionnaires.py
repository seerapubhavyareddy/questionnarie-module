"""
Phase 5 participant questionnaire and response APIs.
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.questionnaire import (
    ParticipantQuestionnaireResponse as ParticipantResponseModel,
    Questionnaire as QuestionnaireModel,
    RecurrenceType,
    ResponseStatus as DBResponseStatus,
    TrialQuestionnaire as TrialQuestionnaireModel,
)
from app.schemas.questionnaire import (
    ParticipantQuestionnaireDetail,
    ParticipantQuestionnaireSummary,
    ParticipantResponseItem,
    ParticipantResponseUpsertRequest,
    QuestionnaireResponse,
    QuestionnaireStatus,
    QuestionnaireType,
    ResponseStatus,
    TrialEligibilityResult,
)
from app.services.scoring import calculate_score

router = APIRouter(prefix="/api/customer", tags=["Participant Questionnaires"])
MAX_GENERATION_DAYS = 366 * 5


def _is_eligibility_type(questionnaire: QuestionnaireModel) -> bool:
    q_type = getattr(questionnaire, "type", None)
    if q_type is None:
        return False
    type_value = getattr(q_type, "value", q_type)
    return str(type_value).lower() == QuestionnaireType.ELIGIBILITY.value


def _is_answered(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return True


def _is_scored_question(question: Dict[str, Any]) -> bool:
    return (question.get("type") or "").lower() != "section_header"


def _compute_progress_percent(questions: List[Dict[str, Any]], responses: Dict[str, Any]) -> int:
    answerable = [q for q in questions if _is_scored_question(q)]
    if not answerable:
        return 100
    answered = sum(1 for q in answerable if _is_answered(responses.get(q.get("id"))))
    return int((answered / len(answerable)) * 100)


def _normalize_datetime_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _parse_time_utc(raw: Any) -> time | None:
    if isinstance(raw, str) and raw:
        try:
            parsed = datetime.strptime(raw.strip(), "%H:%M").time()
            return parsed.replace(second=0, microsecond=0)
        except ValueError:
            return None
    return None


def _sorted_unique_times_utc(config: Dict[str, Any]) -> List[time]:
    times: List[time] = []
    for key in ("times_utc", "times", "slots"):
        values = config.get(key)
        if not values:
            continue
        if key == "slots" and isinstance(values, list):
            for slot in values:
                if isinstance(slot, dict):
                    parsed = _parse_time_utc(slot.get("time_utc") or slot.get("time"))
                    if parsed:
                        times.append(parsed)
        elif isinstance(values, list):
            for raw in values:
                parsed = _parse_time_utc(raw)
                if parsed:
                    times.append(parsed)
    if not times:
        times = [time(hour=0, minute=0, tzinfo=timezone.utc)]
    unique = sorted({(t.hour, t.minute): t for t in times}.values(), key=lambda t: (t.hour, t.minute))
    return unique


def _recurrence_type_value(link: TrialQuestionnaireModel) -> str:
    value = getattr(link.recurrence_type, "value", link.recurrence_type)
    return str(value or RecurrenceType.ONE_TIME.value)


def _matches_custom_date(config: Dict[str, Any], current_date: date, anchor_date: date) -> bool:
    weekdays = config.get("weekdays") or []
    days_of_month = config.get("days_of_month") or []
    interval_days = config.get("interval_days")

    weekday_ok = not weekdays or current_date.weekday() in {int(w) for w in weekdays}
    monthday_ok = not days_of_month or current_date.day in {int(d) for d in days_of_month}
    if interval_days:
        delta_days = (current_date - anchor_date).days
        interval_ok = delta_days >= 0 and delta_days % int(interval_days) == 0
    else:
        interval_ok = True
    return weekday_ok and monthday_ok and interval_ok


def _generate_occurrence_starts(
    link: TrialQuestionnaireModel,
    schedule_start: datetime,
    schedule_end: datetime,
) -> List[datetime]:
    recurrence_type = _recurrence_type_value(link)
    config = link.recurrence_config or {}
    times_utc = _sorted_unique_times_utc(config)
    starts: List[datetime] = []

    if recurrence_type == RecurrenceType.ONE_TIME.value:
        unlock_at = _normalize_datetime_utc(config.get("unlock_at_utc")) or _normalize_datetime_utc(link.start_at_utc) or _normalize_datetime_utc(link.linked_at)
        if unlock_at and schedule_start <= unlock_at <= schedule_end:
            starts.append(unlock_at)
        return starts

    anchor = _normalize_datetime_utc(link.start_at_utc) or _normalize_datetime_utc(link.linked_at) or schedule_start
    first_day = max(anchor.date(), schedule_start.date())
    last_day = min(schedule_end.date(), (anchor + timedelta(days=MAX_GENERATION_DAYS)).date())

    weekly_days = {int(d) for d in (config.get("weekdays") or [])}
    monthly_days = {int(d) for d in (config.get("days_of_month") or [])}

    day = first_day
    while day <= last_day:
        include_day = False
        if recurrence_type == RecurrenceType.WEEKLY.value:
            include_day = day.weekday() in (weekly_days or {anchor.weekday()})
        elif recurrence_type == RecurrenceType.MONTHLY.value:
            include_day = day.day in (monthly_days or {anchor.day})
        else:
            include_day = _matches_custom_date(config, day, anchor.date())

        if include_day:
            for utc_time in times_utc:
                candidate = datetime.combine(day, utc_time).replace(tzinfo=timezone.utc)
                if candidate < anchor:
                    continue
                if schedule_start <= candidate <= schedule_end:
                    starts.append(candidate)
        day += timedelta(days=1)

    starts.sort()
    return starts


def _compute_schedule_state(
    link: TrialQuestionnaireModel,
    now_utc: datetime,
    submitted_visits: set[int],
) -> Dict[str, Any]:
    start_bound = _normalize_datetime_utc(link.start_at_utc) or _normalize_datetime_utc(link.linked_at) or now_utc
    end_bound = _normalize_datetime_utc(link.end_at_utc) or (now_utc + timedelta(days=MAX_GENERATION_DAYS))
    if end_bound < start_bound:
        end_bound = start_bound

    starts = _generate_occurrence_starts(link, start_bound, end_bound)
    window_minutes = int(link.window_duration_minutes or 24 * 60)
    max_visits = link.max_visits
    submitted_count = len(submitted_visits)

    if not starts:
        return {
            "is_locked": submitted_count > 0 or (max_visits is not None and submitted_count >= max_visits),
            "active_visit_number": None,
            "current_visit_number": 1,
            "next_visit_number": None,
            "unlocks_at_utc": None,
            "locks_at_utc": None,
            "submitted_visits": submitted_count,
            "max_visits_reached": max_visits is not None and submitted_count >= max_visits,
        }

    current_idx = None
    next_idx = None
    for idx, occurrence_start in enumerate(starts):
        if occurrence_start <= now_utc:
            current_idx = idx
        elif next_idx is None:
            next_idx = idx

    active_visit_number = None
    unlocks_at_utc = None
    locks_at_utc = None
    is_locked = True

    if current_idx is not None:
        start_at = starts[current_idx]
        end_at = start_at + timedelta(minutes=window_minutes)
        if start_at <= now_utc <= end_at:
            active_visit_number = current_idx + 1
            unlocks_at_utc = start_at
            locks_at_utc = end_at
            is_locked = False

    if active_visit_number is None and next_idx is not None:
        unlocks_at_utc = starts[next_idx]

    if active_visit_number is not None and active_visit_number in submitted_visits:
        is_locked = True
        if next_idx is not None:
            unlocks_at_utc = starts[next_idx]
            locks_at_utc = None

    if max_visits is not None and submitted_count >= max_visits:
        is_locked = True
        active_visit_number = None
        unlocks_at_utc = None
        locks_at_utc = None

    current_visit_number = (current_idx + 1) if current_idx is not None else 1
    next_visit_number = (next_idx + 1) if next_idx is not None else None

    return {
        "is_locked": is_locked,
        "active_visit_number": active_visit_number,
        "current_visit_number": current_visit_number,
        "next_visit_number": next_visit_number,
        "unlocks_at_utc": unlocks_at_utc,
        "locks_at_utc": locks_at_utc,
        "submitted_visits": submitted_count,
        "max_visits_reached": max_visits is not None and submitted_count >= max_visits,
    }


def _required_missing_questions(questions: List[Dict[str, Any]], responses: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for q in questions:
        if not _is_scored_question(q):
            continue
        if not q.get("isRequired"):
            continue
        qid = q.get("id")
        if not _is_answered(responses.get(qid)):
            missing.append(str(qid))
    return missing


def _get_trial_link_or_404(db: Session, trial_id: int, questionnaire_id: int) -> TrialQuestionnaireModel:
    link = db.query(TrialQuestionnaireModel).join(
        QuestionnaireModel,
        TrialQuestionnaireModel.questionnaire_id == QuestionnaireModel.id,
    ).filter(
        TrialQuestionnaireModel.trial_id == trial_id,
        TrialQuestionnaireModel.questionnaire_id == questionnaire_id,
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).first()
    if not link:
        raise HTTPException(
            status_code=404,
            detail=f"Questionnaire {questionnaire_id} is not linked to trial {trial_id}",
        )
    return link


def _to_questionnaire_response(questionnaire: QuestionnaireModel) -> QuestionnaireResponse:
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


@router.get(
    "/{customer_id}/trials/{trial_id}/questionnaires",
    response_model=List[ParticipantQuestionnaireSummary],
)
async def list_customer_trial_questionnaires(
    customer_id: int,
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

    if not links:
        return []

    response_rows = db.query(ParticipantResponseModel).filter(
        ParticipantResponseModel.customer_id == customer_id,
        ParticipantResponseModel.trial_id == trial_id,
    ).all()
    response_map: Dict[int, List[ParticipantResponseModel]] = {}
    for row in response_rows:
        response_map.setdefault(row.questionnaire_id, []).append(row)

    items: List[ParticipantQuestionnaireSummary] = []
    for link in links:
        questionnaire = link.questionnaire
        rows = sorted(response_map.get(link.questionnaire_id, []), key=lambda r: (r.visit_number, r.updated_at or r.created_at))
        submitted_visits = {r.visit_number for r in rows if r.status == DBResponseStatus.SUBMITTED}
        schedule_state = _compute_schedule_state(link, datetime.now(timezone.utc), submitted_visits)
        active_visit = schedule_state["active_visit_number"]
        response_row = next((r for r in rows if r.visit_number == active_visit), None) if active_visit else None
        items.append(
            ParticipantQuestionnaireSummary(
                questionnaire_id=link.questionnaire_id,
                questionnaire_name=questionnaire.name if questionnaire else f"Questionnaire {link.questionnaire_id}",
                questionnaire_description=questionnaire.description if questionnaire else None,
                questionnaire_type=questionnaire.type.value if questionnaire and questionnaire.type else QuestionnaireType.CUSTOM,
                question_count=len(questionnaire.questions or []) if questionnaire else 0,
                is_required=link.is_required,
                display_order=link.display_order,
                recurrence_type=_recurrence_type_value(link),
                max_visits=link.max_visits,
                current_visit_number=schedule_state["current_visit_number"],
                next_visit_number=schedule_state["next_visit_number"],
                is_locked=schedule_state["is_locked"],
                unlocks_at_utc=schedule_state["unlocks_at_utc"],
                locks_at_utc=schedule_state["locks_at_utc"],
                submitted_visits=schedule_state["submitted_visits"],
                response_id=response_row.id if response_row else None,
                response_visit_number=response_row.visit_number if response_row else None,
                response_status=response_row.status.value if response_row else None,
                progress_percent=response_row.progress_percent if response_row else 0,
                eligibility_passed=response_row.eligibility_passed if response_row else None,
                submitted_at=response_row.submitted_at if response_row else None,
            )
        )
    return items


@router.get(
    "/{customer_id}/trials/{trial_id}/questionnaires/{questionnaire_id}",
    response_model=ParticipantQuestionnaireDetail,
)
async def get_customer_trial_questionnaire_detail(
    customer_id: int,
    trial_id: int,
    questionnaire_id: int,
    db: Session = Depends(get_db),
):
    link = _get_trial_link_or_404(db, trial_id, questionnaire_id)
    questionnaire = link.questionnaire
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire {questionnaire_id} not found")

    response_rows = db.query(ParticipantResponseModel).filter(
        ParticipantResponseModel.customer_id == customer_id,
        ParticipantResponseModel.trial_id == trial_id,
        ParticipantResponseModel.questionnaire_id == questionnaire_id,
    ).all()
    submitted_visits = {r.visit_number for r in response_rows if r.status == DBResponseStatus.SUBMITTED}
    schedule_state = _compute_schedule_state(link, datetime.now(timezone.utc), submitted_visits)
    active_visit = schedule_state["active_visit_number"]
    response_row = None
    if active_visit is not None:
        response_row = next((r for r in response_rows if r.visit_number == active_visit), None)

    return ParticipantQuestionnaireDetail(
        trial_id=trial_id,
        customer_id=customer_id,
        questionnaire_id=questionnaire_id,
        questionnaire=_to_questionnaire_response(questionnaire),
        recurrence_type=_recurrence_type_value(link),
        recurrence_config=link.recurrence_config or {},
        max_visits=link.max_visits,
        window_duration_minutes=link.window_duration_minutes,
        current_visit_number=schedule_state["current_visit_number"],
        next_visit_number=schedule_state["next_visit_number"],
        is_locked=schedule_state["is_locked"],
        unlocks_at_utc=schedule_state["unlocks_at_utc"],
        locks_at_utc=schedule_state["locks_at_utc"],
        active_visit_number=active_visit,
        response_id=response_row.id if response_row else None,
        response_visit_number=response_row.visit_number if response_row else None,
        response_status=response_row.status.value if response_row else None,
        progress_percent=response_row.progress_percent if response_row else 0,
        saved_answers=response_row.responses if response_row else {},
        eligibility_passed=response_row.eligibility_passed if response_row else None,
        submitted_at=response_row.submitted_at if response_row else None,
    )


@router.post(
    "/{customer_id}/trials/{trial_id}/responses",
    response_model=ParticipantResponseItem,
)
async def upsert_customer_response(
    customer_id: int,
    trial_id: int,
    payload: ParticipantResponseUpsertRequest,
    db: Session = Depends(get_db),
):
    link = _get_trial_link_or_404(db, trial_id, payload.questionnaire_id)
    questionnaire = link.questionnaire
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire {payload.questionnaire_id} not found")

    rows = db.query(ParticipantResponseModel).filter(
        ParticipantResponseModel.customer_id == customer_id,
        ParticipantResponseModel.trial_id == trial_id,
        ParticipantResponseModel.questionnaire_id == payload.questionnaire_id,
    ).all()
    submitted_visits = {r.visit_number for r in rows if r.status == DBResponseStatus.SUBMITTED}
    schedule_state = _compute_schedule_state(link, datetime.now(timezone.utc), submitted_visits)
    current_visit = schedule_state["active_visit_number"]
    if current_visit is None or schedule_state["is_locked"]:
        raise HTTPException(
            status_code=409,
            detail="This questionnaire is currently locked for your timeline window.",
        )

    existing = next((r for r in rows if r.visit_number == current_visit), None)
    if existing and existing.status == DBResponseStatus.SUBMITTED:
        raise HTTPException(
            status_code=409,
            detail=f"Visit {current_visit} is already submitted and locked.",
        )

    responses = payload.responses or {}
    questions = questionnaire.questions or []
    progress_percent = _compute_progress_percent(questions, responses)

    score_result = None
    eligibility_passed = None
    response_status = DBResponseStatus.DRAFT
    submitted_at = None

    if payload.submit:
        missing_required = _required_missing_questions(questions, responses)
        if missing_required:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Missing required answers",
                    "missing_question_ids": missing_required,
                },
            )
        response_status = DBResponseStatus.SUBMITTED
        submitted_at = datetime.now(timezone.utc)
        progress_percent = 100

        scoring_config = questionnaire.scoring_config or {}
        if scoring_config.get("enabled"):
            score = calculate_score(
                questionnaire_id=questionnaire.id,
                scoring_config=scoring_config,
                questions=questions,
                responses=responses,
            )
            score_result = score.model_dump(mode="json")
            eligibility_passed = score_result.get("passed")
        elif _is_eligibility_type(questionnaire):
            # No scoring configured: treat completed eligibility submission as pass.
            eligibility_passed = True

    if existing:
        existing.responses = responses
        existing.progress_percent = progress_percent
        existing.status = response_status
        existing.score_result = score_result
        existing.eligibility_passed = eligibility_passed
        existing.submitted_at = submitted_at
        existing.questionnaire_version = questionnaire.version
        db.commit()
        db.refresh(existing)
        return existing

    new_row = ParticipantResponseModel(
        customer_id=customer_id,
        trial_id=trial_id,
        questionnaire_id=payload.questionnaire_id,
        questionnaire_version=questionnaire.version,
        visit_number=current_visit,
        status=response_status,
        responses=responses,
        progress_percent=progress_percent,
        score_result=score_result,
        eligibility_passed=eligibility_passed,
        submitted_at=submitted_at,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row


@router.get(
    "/{customer_id}/trials/{trial_id}/responses/{response_id}",
    response_model=ParticipantResponseItem,
)
async def get_customer_response(
    customer_id: int,
    trial_id: int,
    response_id: int,
    db: Session = Depends(get_db),
):
    row = db.query(ParticipantResponseModel).filter(
        ParticipantResponseModel.id == response_id,
        ParticipantResponseModel.customer_id == customer_id,
        ParticipantResponseModel.trial_id == trial_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Response {response_id} not found")
    return row


@router.get(
    "/{customer_id}/trials/{trial_id}/eligibility-result",
    response_model=TrialEligibilityResult,
)
async def get_trial_eligibility_result(
    customer_id: int,
    trial_id: int,
    db: Session = Depends(get_db),
):
    required_links = db.query(TrialQuestionnaireModel).join(
        QuestionnaireModel,
        TrialQuestionnaireModel.questionnaire_id == QuestionnaireModel.id,
    ).filter(
        TrialQuestionnaireModel.trial_id == trial_id,
        TrialQuestionnaireModel.is_required == True,  # noqa: E712
        QuestionnaireModel.is_deleted == False,  # noqa: E712
    ).all()

    if not required_links:
        return TrialEligibilityResult(
            customer_id=customer_id,
            trial_id=trial_id,
            is_eligible=True,
            total_required_questionnaires=0,
            completed_required_questionnaires=0,
            failed_required_questionnaires=0,
            reasons=[],
        )

    eligibility_required_links = [
        link for link in required_links if link.questionnaire and _is_eligibility_type(link.questionnaire)
    ]
    # Unlocking gate should depend on required eligibility questionnaires only.
    # If none exist, trial is considered eligible by questionnaire gate.
    evaluation_links = eligibility_required_links

    responses = db.query(ParticipantResponseModel).filter(
        ParticipantResponseModel.customer_id == customer_id,
        ParticipantResponseModel.trial_id == trial_id,
    ).all()
    response_by_questionnaire: Dict[int, ParticipantResponseModel] = {}
    for response in sorted(responses, key=lambda r: (r.questionnaire_id, r.visit_number, r.updated_at or r.created_at)):
        existing = response_by_questionnaire.get(response.questionnaire_id)
        if existing is None:
            response_by_questionnaire[response.questionnaire_id] = response
            continue
        if existing.status != DBResponseStatus.SUBMITTED and response.status == DBResponseStatus.SUBMITTED:
            response_by_questionnaire[response.questionnaire_id] = response
            continue
        if response.visit_number >= existing.visit_number:
            response_by_questionnaire[response.questionnaire_id] = response

    reasons: List[str] = []
    completed = 0
    failed = 0

    for link in evaluation_links:
        response = response_by_questionnaire.get(link.questionnaire_id)
        questionnaire_name = (
            link.questionnaire.name
            if link.questionnaire
            else f"Questionnaire {link.questionnaire_id}"
        )

        if not response or response.status != DBResponseStatus.SUBMITTED:
            reasons.append(f"Required questionnaire '{questionnaire_name}' is not submitted.")
            continue

        completed += 1
        if response.eligibility_passed is False:
            failed += 1
            reasons.append(f"Eligibility criteria not met in '{questionnaire_name}'.")

    return TrialEligibilityResult(
        customer_id=customer_id,
        trial_id=trial_id,
        is_eligible=(len(reasons) == 0),
        total_required_questionnaires=len(evaluation_links),
        completed_required_questionnaires=completed,
        failed_required_questionnaires=failed,
        reasons=reasons,
    )
