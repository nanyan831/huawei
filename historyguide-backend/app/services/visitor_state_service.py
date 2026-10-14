from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState, VisitorVisitEventLog
from app.schemas.visitor_state import (
    RemainingTimeStats,
    VisitorStateCountItem,
    VisitorStateCreate,
    VisitorStateIntegrityIssue,
    VisitorStateIntegrityReport,
    VisitorStateStats,
    VisitorStateUpdate,
    VisitorVisitEvent,
)
from app.services.audit_log_service import record_audit_log
from app.services.exhibit_service import get_exhibit


def list_visitor_states(
    db: Session,
    *,
    visitor_type: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[VisitorState]:
    statement = select(VisitorState).order_by(VisitorState.session_id)
    if visitor_type:
        statement = statement.where(VisitorState.visitor_type == visitor_type)

    states = list(db.scalars(statement).all())
    if offset:
        states = states[offset:]
    if limit is not None:
        states = states[:limit]
    return states


def get_visitor_state(db: Session, session_id: str) -> VisitorState | None:
    return db.get(VisitorState, session_id)


def list_visit_events(
    db: Session,
    session_id: str,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[VisitorVisitEventLog]:
    statement = (
        select(VisitorVisitEventLog)
        .where(VisitorVisitEventLog.session_id == session_id)
        .order_by(VisitorVisitEventLog.event_time, VisitorVisitEventLog.id)
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(db.scalars(statement).all())


def get_visitor_state_stats(db: Session) -> VisitorStateStats:
    states = list_visitor_states(db)
    remaining_times = [state.remaining_time for state in states]
    remaining_time_stats = None
    if remaining_times:
        remaining_time_stats = RemainingTimeStats(
            min=min(remaining_times),
            max=max(remaining_times),
            average=sum(remaining_times) / len(remaining_times),
        )

    return VisitorStateStats(
        total_sessions=len(states),
        visitor_types=_count_scalar_values(state.visitor_type for state in states),
        current_exhibits=_count_scalar_values(state.current_exhibit for state in states),
        interests=_count_list_values(state.interest for state in states),
        no_current_exhibit_count=sum(1 for state in states if not state.current_exhibit),
        remaining_time=remaining_time_stats,
    )


def get_visitor_state_integrity_report(
    db: Session,
    *,
    session_id: str | None = None,
) -> VisitorStateIntegrityReport:
    if session_id is None:
        states = list_visitor_states(db)
        event_statement = select(VisitorVisitEventLog)
    else:
        state = get_visitor_state(db, session_id)
        states = [state] if state is not None else []
        event_statement = select(VisitorVisitEventLog).where(
            VisitorVisitEventLog.session_id == session_id
        )

    all_events = list(
        db.scalars(
            event_statement.order_by(
                VisitorVisitEventLog.session_id,
                VisitorVisitEventLog.event_time,
                VisitorVisitEventLog.id,
            )
        ).all()
    )
    events_by_session: dict[str, list[VisitorVisitEventLog]] = {}
    for event in all_events:
        events_by_session.setdefault(event.session_id, []).append(event)

    issues: list[VisitorStateIntegrityIssue] = []
    for state in states:
        visit_events = events_by_session.get(state.session_id, [])
        visited_history = list(state.visited_history or [])
        if not visit_events:
            if visited_history:
                issues.append(
                    VisitorStateIntegrityIssue(
                        session_id=state.session_id,
                        issue="visited_history_without_visit_events",
                        detail="Visited history exists but no visit-event timeline entries were recorded.",
                        exhibit_ids=sorted(set(visited_history)),
                    )
                )
            continue

        latest_event = visit_events[-1]
        if state.current_exhibit != latest_event.exhibit_id:
            issues.append(
                VisitorStateIntegrityIssue(
                    session_id=state.session_id,
                    issue="latest_event_not_current_exhibit",
                    detail=(
                        f"Latest visit event exhibit '{latest_event.exhibit_id}' does not match "
                        f"current_exhibit '{state.current_exhibit}'."
                    ),
                    exhibit_ids=[latest_event.exhibit_id],
                )
            )

        missing_from_history = sorted(
            {event.exhibit_id for event in visit_events} - set(visited_history)
        )
        if missing_from_history:
            issues.append(
                VisitorStateIntegrityIssue(
                    session_id=state.session_id,
                    issue="visit_events_missing_from_visited_history",
                    detail="Visit-event exhibits are missing from visited_history.",
                    exhibit_ids=missing_from_history,
                )
            )

    return VisitorStateIntegrityReport(
        total_sessions=len(states),
        total_visit_events=len(all_events),
        sessions_with_visit_events=len(events_by_session),
        issue_count=len(issues),
        issues=issues,
    )


def validate_exhibit_references(
    db: Session,
    *,
    current_exhibit: str | None = None,
    visited_history: list[str] | None = None,
) -> str | None:
    exhibit_ids = set(visited_history or [])
    if current_exhibit:
        exhibit_ids.add(current_exhibit)

    for exhibit_id in exhibit_ids:
        if get_exhibit(db, exhibit_id) is None:
            return exhibit_id
    return None


def create_visitor_state(db: Session, state: VisitorStateCreate) -> VisitorState:
    db_state = VisitorState(**state.model_dump())
    db.add(db_state)
    record_audit_log(
        db,
        action="visitor_state_created",
        resource_type="visitor_state",
        resource_id=state.session_id,
        actor="api",
        details={
            "visitor_type": state.visitor_type,
            "current_exhibit": state.current_exhibit,
            "visited_count": len(state.visited_history),
            "interest_count": len(state.interest),
        },
    )
    db.commit()
    db.refresh(db_state)
    return db_state


def _count_scalar_values(values) -> list[VisitorStateCountItem]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = value.strip() if value else ""
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return _count_items(counts)


def _count_list_values(values_by_state) -> list[VisitorStateCountItem]:
    counts: dict[str, int] = {}
    for values in values_by_state:
        for value in values or []:
            normalized = value.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
    return _count_items(counts)


def _count_items(counts: dict[str, int]) -> list[VisitorStateCountItem]:
    return [
        VisitorStateCountItem(value=value, count=count)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def update_visitor_state(
    db: Session,
    db_state: VisitorState,
    state_update: VisitorStateUpdate,
) -> VisitorState:
    update_data = state_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_state, field, value)

    db.add(db_state)
    record_audit_log(
        db,
        action="visitor_state_updated",
        resource_type="visitor_state",
        resource_id=db_state.session_id,
        actor="api",
        details={"updated_fields": sorted(update_data.keys())},
    )
    db.commit()
    db.refresh(db_state)
    return db_state


def record_visit_event(
    db: Session,
    db_state: VisitorState,
    visit_event: VisitorVisitEvent,
) -> VisitorState:
    visited_history = list(db_state.visited_history or [])
    if visit_event.exhibit_id not in visited_history:
        visited_history.append(visit_event.exhibit_id)

    db_state.current_exhibit = visit_event.exhibit_id
    db_state.visited_history = visited_history
    if visit_event.remaining_time is not None:
        db_state.remaining_time = visit_event.remaining_time

    db_event = VisitorVisitEventLog(
        session_id=db_state.session_id,
        exhibit_id=visit_event.exhibit_id,
        remaining_time=visit_event.remaining_time,
    )
    db.add(db_event)
    db.add(db_state)
    record_audit_log(
        db,
        action="visit_event_recorded",
        resource_type="visitor_state",
        resource_id=db_state.session_id,
        actor="api",
        details={
            "exhibit_id": visit_event.exhibit_id,
            "remaining_time": visit_event.remaining_time,
            "visited_count": len(visited_history),
        },
    )
    db.commit()
    db.refresh(db_state)
    return db_state
