from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.review_run import (
    FinalizeRunRequest,
    FinalizeRunResponse,
    PrepareRunRequest,
    PrepareRunResponse,
    ReviewRunRequest,
    ReviewRunResponse,
)
from app.services.review_run_service import (
    approved_evidence_for_handoff,
    finalize_run,
    prepare_run,
    review_run,
)
from app.services.visitor_state_service import get_visitor_state


router = APIRouter(prefix="/api/genios/runs", tags=["genios-runs"])


def _call(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("", response_model=PrepareRunResponse, status_code=status.HTTP_201_CREATED)
def create_review_run(
    payload: PrepareRunRequest, db: Session = Depends(get_db)
) -> PrepareRunResponse:
    visitor_state = get_visitor_state(db, payload.session_id)
    if visitor_state is None:
        raise HTTPException(status_code=404, detail="Visitor session was not found.")
    run, handoff = prepare_run(db, visitor_state, payload)
    return PrepareRunResponse(
        run_id=run.id, session_id=run.session_id, expires_at=run.expires_at,
        handoff=handoff,
        approved_evidence=approved_evidence_for_handoff(db, handoff),
    )


@router.post("/{run_id}/review", response_model=ReviewRunResponse)
def check_review_run(
    run_id: str, payload: ReviewRunRequest, db: Session = Depends(get_db)
) -> ReviewRunResponse:
    run = _call(review_run, db, run_id, payload)
    return ReviewRunResponse(
        run_id=run.id, session_id=run.session_id, decision=run.decision,
        issues=run.issues or "", safe_answer=run.safe_answer or "",
        draft_sha256=run.draft_sha256 or "",
    )


@router.post("/{run_id}/finalize", response_model=FinalizeRunResponse)
def release_review_run(
    run_id: str, payload: FinalizeRunRequest, db: Session = Depends(get_db)
) -> FinalizeRunResponse:
    run = _call(finalize_run, db, run_id, draft_answer=payload.draft_answer)
    return FinalizeRunResponse(
        run_id=run.id, decision=run.decision, answer=run.safe_answer or "",
    )
