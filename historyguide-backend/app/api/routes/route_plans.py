from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.route_plan import RoutePlan
from app.services.route_plan_service import build_route_plan
from app.services.visitor_state_service import get_visitor_state


router = APIRouter(prefix="/api/visit-routes", tags=["visit-routes"])


@router.get("/{session_id}/plan", response_model=RoutePlan)
def read_route_plan(
    session_id: str,
    max_items: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
) -> RoutePlan:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_route_plan(db, visitor_state, max_items=max_items)

