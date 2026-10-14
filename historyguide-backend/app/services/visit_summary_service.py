from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState
from app.schemas.visit_summary import VisitSummary
from app.schemas.visitor_state import VisitorStateRead, VisitorVisitEventRead
from app.services.exhibit_service import get_exhibit
from app.services.visitor_state_service import list_visit_events


def build_visit_summary(db: Session, visitor_state: VisitorState) -> VisitSummary:
    visited_exhibits = []
    missing_exhibit_ids: list[str] = []

    for exhibit_id in visitor_state.visited_history:
        exhibit = get_exhibit(db, exhibit_id)
        if exhibit is None:
            missing_exhibit_ids.append(exhibit_id)
            continue
        visited_exhibits.append(exhibit)

    return VisitSummary(
        session_id=visitor_state.session_id,
        visitor_state=VisitorStateRead.model_validate(visitor_state),
        visited_count=len(visited_exhibits),
        visited_exhibits=visited_exhibits,
        visit_events=[
            VisitorVisitEventRead.model_validate(visit_event)
            for visit_event in list_visit_events(db, visitor_state.session_id)
        ],
        interests=visitor_state.interest,
        remaining_time=visitor_state.remaining_time,
        missing_exhibit_ids=missing_exhibit_ids,
    )
