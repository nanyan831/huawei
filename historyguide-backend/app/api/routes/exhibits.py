from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.exhibit import ExhibitFacets, ExhibitQualityReport, ExhibitRead, ExhibitSourceReport
from app.services.exhibit_service import (
    get_exhibit,
    get_exhibit_facets,
    get_exhibit_quality_report,
    get_exhibit_source_report,
    list_exhibits,
)


router = APIRouter(prefix="/api/exhibits", tags=["exhibits"])


@router.get("", response_model=list[ExhibitRead])
def read_exhibits(
    keyword: str | None = Query(default=None, description="Filter by keyword, person, theme, name, or description."),
    period: str | None = Query(default=None, description="Filter by exhibit period."),
    importance_min: int | None = Query(default=None, ge=1, le=5, description="Minimum exhibit importance."),
    limit: int | None = Query(default=None, ge=1, le=200, description="Maximum number of exhibits to return."),
    offset: int = Query(default=0, ge=0, description="Number of matching exhibits to skip."),
    db: Session = Depends(get_db),
) -> list[ExhibitRead]:
    return list_exhibits(
        db,
        keyword=keyword,
        period=period,
        importance_min=importance_min,
        limit=limit,
        offset=offset,
    )


@router.get("/facets", response_model=ExhibitFacets)
def read_exhibit_facets(db: Session = Depends(get_db)) -> ExhibitFacets:
    return get_exhibit_facets(db)


@router.get("/quality-report", response_model=ExhibitQualityReport)
def read_exhibit_quality_report(db: Session = Depends(get_db)) -> ExhibitQualityReport:
    return get_exhibit_quality_report(db)


@router.get("/source-report", response_model=ExhibitSourceReport)
def read_exhibit_source_report(db: Session = Depends(get_db)) -> ExhibitSourceReport:
    return get_exhibit_source_report(db)


@router.get("/{exhibit_id}", response_model=ExhibitRead)
def read_exhibit(exhibit_id: str, db: Session = Depends(get_db)) -> ExhibitRead:
    exhibit = get_exhibit(db, exhibit_id)
    if exhibit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exhibit '{exhibit_id}' was not found.",
        )
    return exhibit
