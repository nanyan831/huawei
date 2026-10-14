from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.visitor_state import (
    VisitorStateCreate,
    VisitorStateIntegrityReport,
    VisitorStateRead,
    VisitorStateStats,
    VisitorStateUpdate,
    VisitorType,
    VisitorVisitEvent,
    VisitorVisitEventRead,
)
from app.services.visitor_state_service import (
    create_visitor_state,
    get_visitor_state,
    get_visitor_state_integrity_report,
    get_visitor_state_stats,
    list_visit_events,
    list_visitor_states,
    record_visit_event,
    update_visitor_state,
    validate_exhibit_references,
)


router = APIRouter(prefix="/api/visitor-states", tags=["visitor-states"])


@router.post("", response_model=VisitorStateRead, status_code=status.HTTP_201_CREATED)
def create_state(state: VisitorStateCreate, db: Session = Depends(get_db)) -> VisitorStateRead:
    if get_visitor_state(db, state.session_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Visitor session '{state.session_id}' already exists.",
        )

    missing_exhibit = validate_exhibit_references(
        db,
        current_exhibit=state.current_exhibit,
        visited_history=state.visited_history,
    )
    if missing_exhibit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Referenced exhibit '{missing_exhibit}' was not found.",
        )

    return create_visitor_state(db, state)


@router.get("", response_model=list[VisitorStateRead])
def read_states(
    visitor_type: VisitorType | None = Query(default=None, description="Filter by visitor type."),
    limit: int | None = Query(default=None, ge=1, le=200, description="Maximum number of sessions to return."),
    offset: int = Query(default=0, ge=0, description="Number of matching sessions to skip."),
    db: Session = Depends(get_db),
) -> list[VisitorStateRead]:
    return list_visitor_states(db, visitor_type=visitor_type, limit=limit, offset=offset)


@router.get("/stats", response_model=VisitorStateStats)
def read_state_stats(db: Session = Depends(get_db)) -> VisitorStateStats:
    return get_visitor_state_stats(db)


@router.get("/integrity-report", response_model=VisitorStateIntegrityReport)
def read_state_integrity_report(db: Session = Depends(get_db)) -> VisitorStateIntegrityReport:
    return get_visitor_state_integrity_report(db)


@router.get("/{session_id}/integrity", response_model=VisitorStateIntegrityReport)
def read_state_integrity(
    session_id: str,
    db: Session = Depends(get_db),
) -> VisitorStateIntegrityReport:
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return get_visitor_state_integrity_report(db, session_id=session_id)


@router.get("/{session_id}", response_model=VisitorStateRead)
def read_state(session_id: str, db: Session = Depends(get_db)) -> VisitorStateRead:
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )
    return state


@router.patch("/{session_id}", response_model=VisitorStateRead)
def update_state(
    session_id: str,
    state_update: VisitorStateUpdate,
    db: Session = Depends(get_db),
) -> VisitorStateRead:
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    missing_exhibit = validate_exhibit_references(
        db,
        current_exhibit=state_update.current_exhibit,
        visited_history=state_update.visited_history,
    )
    if missing_exhibit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Referenced exhibit '{missing_exhibit}' was not found.",
        )

    return update_visitor_state(db, state, state_update)


@router.get("/{session_id}/visit-events", response_model=list[VisitorVisitEventRead])
def read_visit_events(
    session_id: str,
    limit: int | None = Query(default=None, ge=1, le=200, description="Maximum number of visit events to return."),
    offset: int = Query(default=0, ge=0, description="Number of visit events to skip."),
    db: Session = Depends(get_db),
) -> list[VisitorVisitEventRead]:
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return list_visit_events(db, session_id, limit=limit, offset=offset)


@router.post("/{session_id}/visit-events", response_model=VisitorStateRead)
def create_visit_event(
    session_id: str,
    visit_event: VisitorVisitEvent,
    db: Session = Depends(get_db),
) -> VisitorStateRead:
    state = get_visitor_state(db, session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    missing_exhibit = validate_exhibit_references(db, current_exhibit=visit_event.exhibit_id)
    if missing_exhibit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Referenced exhibit '{missing_exhibit}' was not found.",
        )

    return record_visit_event(db, state, visit_event)
