from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.approved_source_search import ApprovedSourceSearchRequest, ApprovedSourceSearchResponse
from app.services.approved_source_search_service import search_approved_sources


router = APIRouter(prefix="/api/genios/sources", tags=["genios-sources"])


@router.post("/search", response_model=ApprovedSourceSearchResponse)
def search_sources(
    payload: ApprovedSourceSearchRequest, response: Response, db: Session = Depends(get_db)
) -> ApprovedSourceSearchResponse:
    response.headers["Cache-Control"] = "no-store"
    return ApprovedSourceSearchResponse(matches=search_approved_sources(db, payload))
