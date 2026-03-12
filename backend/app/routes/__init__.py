"""Routes package initialization."""
from app.routes.questionnaires import router as questionnaires_router
from app.routes.trial_questionnaires import (
    router as trial_questionnaires_router,
    vendor_router as vendor_trial_questionnaires_router,
)
from app.routes.participant_questionnaires import router as participant_questionnaires_router

__all__ = [
    "questionnaires_router",
    "trial_questionnaires_router",
    "vendor_trial_questionnaires_router",
    "participant_questionnaires_router",
]
