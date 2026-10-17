from datetime import datetime, timezone
import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.visitor_tokens import issue_visitor_token, verify_visitor_token
from app.database.session import get_db
from app.models.visitor_access_grant import VisitorAccessGrant
from app.models.visitor_state import VisitorState
from app.schemas.genios_answer import ExhibitAnswerRequest, HistoryAnswerRequest, ReleasedAnswer
from app.schemas.exhibit import ExhibitRead
from app.schemas.route_plan import RoutePlan
from app.schemas.visitor_gateway import (
    VisitorExhibitAnswerRequest,
    VisitorGrantRequest,
    VisitorGrantResponse,
    VisitorRevokeResponse,
)
from app.schemas.visitor_state import VisitorStateRead, VisitorVisitEvent
from app.services.evidence_service import exhibit_approval_issue
from app.services.exhibit_service import get_exhibit
from app.services.genios_answer_service import run_exhibit_answer, run_history_answer
from app.services.route_plan_service import build_route_plan
from app.services.visitor_state_service import get_visitor_state, record_visit_event
from app.services.audit_log_service import record_audit_log


router = APIRouter(prefix="/api/visitor", tags=["visitor-gateway"])


def _owned_state(request: Request, db: Session = Depends(get_db)) -> VisitorState:
    settings = request.app.state.settings
    if not settings.visitor_gateway_enabled or not settings.visitor_signing_key:
        raise HTTPException(status_code=404, detail="Visitor gateway is disabled.")
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Valid visitor token is required.")
    token = authorization[7:]
    session_id = verify_visitor_token(token, settings.visitor_signing_key)
    if session_id is None:
        raise HTTPException(status_code=401, detail="Valid visitor token is required.")
    grant = db.get(VisitorAccessGrant, hashlib.sha256(token.encode("ascii")).hexdigest())
    if (
        grant is None or grant.session_id != session_id or grant.revoked_at is not None
        or grant.expires_at_epoch <= int(time.time())
    ):
        raise HTTPException(status_code=401, detail="Valid visitor token is required.")
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(status_code=401, detail="Visitor session is no longer available.")
    return state


@router.post("/grants", response_model=VisitorGrantResponse, status_code=status.HTTP_201_CREATED)
def grant_visitor_session(
    payload: VisitorGrantRequest, request: Request, response: Response,
    db: Session = Depends(get_db),
) -> VisitorGrantResponse:
    settings = request.app.state.settings
    if not settings.visitor_gateway_enabled or not settings.visitor_signing_key:
        raise HTTPException(status_code=404, detail="Visitor gateway is disabled.")
    if get_visitor_state(db, payload.session_id) is None:
        raise HTTPException(status_code=404, detail="Visitor session was not found.")
    token, expiry = issue_visitor_token(
        payload.session_id, settings.visitor_signing_key, settings.visitor_token_ttl_minutes
    )
    token_sha256 = hashlib.sha256(token.encode("ascii")).hexdigest()
    db.add(VisitorAccessGrant(
        token_sha256=token_sha256,
        session_id=payload.session_id,
        expires_at_epoch=expiry,
    ))
    try:
        record_audit_log(
            db, action="visitor_grant_issued", resource_type="visitor_session",
            resource_id=payload.session_id,
            details={"expires_at_epoch": expiry},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    response.headers["Cache-Control"] = "no-store"
    return VisitorGrantResponse(
        session_id=payload.session_id,
        access_token=token,
        expires_at=datetime.fromtimestamp(expiry, tz=timezone.utc),
    )


@router.post("/grants/revoke", response_model=VisitorRevokeResponse)
def revoke_visitor_session_grants(
    payload: VisitorGrantRequest, request: Request, response: Response,
    db: Session = Depends(get_db),
) -> VisitorRevokeResponse:
    if not request.app.state.settings.visitor_gateway_enabled:
        raise HTTPException(status_code=404, detail="Visitor gateway is disabled.")
    result = db.execute(
        update(VisitorAccessGrant)
        .where(VisitorAccessGrant.session_id == payload.session_id)
        .where(VisitorAccessGrant.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    try:
        record_audit_log(
            db, action="visitor_grants_revoked", resource_type="visitor_session",
            resource_id=payload.session_id, details={"revoked_count": result.rowcount},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    response.headers["Cache-Control"] = "no-store"
    return VisitorRevokeResponse(revoked_count=result.rowcount)


@router.post("/revoke", response_model=VisitorRevokeResponse)
def revoke_own_visitor_token(
    request: Request, response: Response, state: VisitorState = Depends(_owned_state),
    db: Session = Depends(get_db),
) -> VisitorRevokeResponse:
    token = request.headers["Authorization"][7:]
    grant = db.get(VisitorAccessGrant, hashlib.sha256(token.encode("ascii")).hexdigest())
    grant.revoked_at = datetime.now(timezone.utc)
    try:
        record_audit_log(
            db, action="visitor_grant_self_revoked", resource_type="visitor_session",
            resource_id=state.session_id, actor="visitor",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    response.headers["Cache-Control"] = "no-store"
    return VisitorRevokeResponse(revoked_count=1)


@router.get("/me", response_model=VisitorStateRead)
def read_own_visit(state: VisitorState = Depends(_owned_state)) -> VisitorStateRead:
    return state


@router.get("/route", response_model=RoutePlan)
def read_own_route(
    state: VisitorState = Depends(_owned_state), db: Session = Depends(get_db),
) -> RoutePlan:
    return build_route_plan(db, state, approved_only=True)


@router.get("/exhibits/{exhibit_id}", response_model=ExhibitRead)
def read_approved_exhibit(
    exhibit_id: str, state: VisitorState = Depends(_owned_state), db: Session = Depends(get_db),
) -> ExhibitRead:
    exhibit = get_exhibit(db, exhibit_id)
    if exhibit is None or exhibit.id.startswith("fixture-") or exhibit_approval_issue(db, exhibit):
        raise HTTPException(status_code=404, detail="Approved exhibit was not found.")
    return exhibit


@router.post("/visit-events", response_model=VisitorStateRead)
def record_own_visit(
    event: VisitorVisitEvent,
    state: VisitorState = Depends(_owned_state), db: Session = Depends(get_db),
) -> VisitorStateRead:
    exhibit = get_exhibit(db, event.exhibit_id)
    if exhibit is None or exhibit.id.startswith("fixture-") or exhibit_approval_issue(db, exhibit):
        raise HTTPException(status_code=404, detail="Approved exhibit was not found.")
    return record_visit_event(db, state, event)


def _release(action):
    try:
        return action()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/answers/history", response_model=ReleasedAnswer)
def release_own_history_answer(
    payload: HistoryAnswerRequest,
    request: Request,
    state: VisitorState = Depends(_owned_state), db: Session = Depends(get_db),
) -> ReleasedAnswer:
    return _release(lambda: run_history_answer(
        db, payload, require_claim_support=request.app.state.settings.claim_support_required,
    ))


@router.post("/answers/exhibit", response_model=ReleasedAnswer)
def release_own_exhibit_answer(
    payload: VisitorExhibitAnswerRequest,
    request: Request,
    state: VisitorState = Depends(_owned_state), db: Session = Depends(get_db),
) -> ReleasedAnswer:
    trusted_payload = ExhibitAnswerRequest(
        session_id=state.session_id, **payload.model_dump()
    )
    return _release(lambda: run_exhibit_answer(
        db, trusted_payload, require_claim_support=request.app.state.settings.claim_support_required,
    ))
