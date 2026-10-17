from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.history_review_run import (
    HistoryFinalizeRequest,
    HistoryFinalizeResponse,
    HistoryPrepareRequest,
    HistoryPrepareResponse,
    HistoryReviewRequest,
    HistoryReviewResponse,
)
from app.services.history_review_run_service import (
    finalize_history_run,
    prepare_history_run,
    review_history_run,
)


router = APIRouter(prefix="/api/genios/history-runs", tags=["genios-history-runs"])


def _call(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("", response_model=HistoryPrepareResponse, status_code=status.HTTP_201_CREATED)
def prepare_history_answer(
    payload: HistoryPrepareRequest, request: Request, db: Session = Depends(get_db)
) -> HistoryPrepareResponse:
    if request.app.state.settings.claim_support_required:
        raise HTTPException(status_code=409, detail="Use the one-call reviewed answer endpoint in strict mode.")
    run, evidence = _call(prepare_history_run, db, payload)
    return HistoryPrepareResponse(
        run_id=run.id, expires_at=run.expires_at, approved_evidence=evidence
    )


@router.post("/{run_id}/review", response_model=HistoryReviewResponse)
def review_history_answer(
    run_id: str, payload: HistoryReviewRequest, request: Request, db: Session = Depends(get_db)
) -> HistoryReviewResponse:
    if request.app.state.settings.claim_support_required:
        raise HTTPException(status_code=409, detail="Use the one-call reviewed answer endpoint in strict mode.")
    run = _call(review_history_run, db, run_id, payload)
    return HistoryReviewResponse(
        run_id=run.id,
        decision=run.decision,
        issues=run.issues or "",
        safe_answer=run.safe_answer or "",
        draft_sha256=run.draft_sha256 or "",
    )


@router.post("/{run_id}/finalize", response_model=HistoryFinalizeResponse)
def finalize_history_answer(
    run_id: str, payload: HistoryFinalizeRequest, request: Request, db: Session = Depends(get_db)
) -> HistoryFinalizeResponse:
    if request.app.state.settings.claim_support_required:
        raise HTTPException(status_code=409, detail="Use the one-call reviewed answer endpoint in strict mode.")
    run = _call(finalize_history_run, db, run_id, draft_answer=payload.draft_answer)
    return HistoryFinalizeResponse(run_id=run.id, answer=run.safe_answer or "")
