from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.genios_answer import ExhibitAnswerRequest, HistoryAnswerRequest, ReleasedAnswer
from app.services.genios_answer_service import run_exhibit_answer, run_history_answer


router = APIRouter(prefix="/api/genios/answers", tags=["genios-answers"])


def _release(action):
    try:
        return action()
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/history", response_model=ReleasedAnswer)
def release_history_answer(
    payload: HistoryAnswerRequest, request: Request, db: Session = Depends(get_db)
) -> ReleasedAnswer:
    return _release(lambda: run_history_answer(
        db, payload, require_claim_support=request.app.state.settings.claim_support_required,
    ))


@router.post("/exhibit", response_model=ReleasedAnswer)
def release_exhibit_answer(
    payload: ExhibitAnswerRequest, request: Request, db: Session = Depends(get_db)
) -> ReleasedAnswer:
    return _release(lambda: run_exhibit_answer(
        db, payload, require_claim_support=request.app.state.settings.claim_support_required,
    ))
