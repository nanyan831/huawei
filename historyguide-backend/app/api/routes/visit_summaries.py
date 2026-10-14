from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.visit_summary import VisitSummary
from app.services.visit_summary_service import build_visit_summary
from app.services.visitor_state_service import get_visitor_state


router = APIRouter(prefix="/api/visits", tags=["visit-summaries"])


@router.get("/{session_id}/summary", response_model=VisitSummary)
def read_visit_summary(session_id: str, db: Session = Depends(get_db)) -> VisitSummary:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_visit_summary(db, visitor_state)

