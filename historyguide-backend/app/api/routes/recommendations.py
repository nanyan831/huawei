from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.recommendation import ExhibitRecommendation
from app.services.recommendation_service import recommend_exhibits
from app.services.visitor_state_service import get_visitor_state


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{session_id}", response_model=list[ExhibitRecommendation])
def read_recommendations(
    session_id: str,
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[ExhibitRecommendation]:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return recommend_exhibits(db, visitor_state, limit=limit)

