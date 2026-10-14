from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from secrets import compare_digest
from typing import Literal
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import OPERATOR_API_KEY_HEADER
from app.models.evidence import EvidenceSource
from app.schemas.evidence import (
    EvidenceLinkRead,
    EvidenceSourceCreate,
    EvidenceSourceBatchCreate,
    EvidenceSourceBatchRead,
    EvidenceSourcePage,
    EvidenceSourceRead,
    ExhibitApprovalRead,
    ReviewerAction,
)
from app.schemas.review_run import ReviewRunStats
from app.services.evidence_service import (
    approve_exhibit,
    approve_source,
    create_source,
    create_sources_batch,
    list_sources,
    link_source,
    revoke_exhibit,
    revoke_source,
)
from app.services.review_run_stats_service import get_review_run_stats


def require_evidence_operator(
    request: Request,
    operator_key: str | None = Header(default=None, alias=OPERATOR_API_KEY_HEADER),
) -> None:
    configured_key = request.app.state.settings.operator_api_key
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evidence operations require a configured operator API key.",
        )
    if operator_key is None or not compare_digest(operator_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid HistoryGuide operator API key is required.",
        )


router = APIRouter(
    prefix="/api/evidence",
    tags=["evidence-operations"],
    dependencies=[Depends(require_evidence_operator)],
)


def _call(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/sources", response_model=EvidenceSourceRead, status_code=status.HTTP_201_CREATED)
def add_evidence_source(
    payload: EvidenceSourceCreate, db: Session = Depends(get_db)
) -> EvidenceSourceRead:
    return _call(create_source, db, source_id=payload.id, title=payload.title,
                 source_uri=payload.source_uri, content_text=payload.content_text)


@router.post("/sources/batch", response_model=EvidenceSourceBatchRead, status_code=status.HTTP_201_CREATED)
def add_evidence_sources_batch(
    payload: EvidenceSourceBatchCreate, db: Session = Depends(get_db)
) -> EvidenceSourceBatchRead:
    sources = _call(create_sources_batch, db, payload.sources)
    return EvidenceSourceBatchRead(imported_count=len(sources), items=sources)


@router.get("/sources", response_model=EvidenceSourcePage)
def read_evidence_sources(
    status_filter: Literal["draft", "approved", "revoked"] | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> EvidenceSourcePage:
    items, total = list_sources(db, status=status_filter, offset=offset, limit=limit)
    return EvidenceSourcePage(items=items, total=total, offset=offset, limit=limit)


@router.get("/sources/{source_id}", response_model=EvidenceSourceRead)
def read_evidence_source(source_id: str, db: Session = Depends(get_db)) -> EvidenceSourceRead:
    source = db.get(EvidenceSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Evidence source was not found.")
    return source


@router.post("/sources/{source_id}/approve", response_model=EvidenceSourceRead)
def approve_evidence_source(
    source_id: str, payload: ReviewerAction, db: Session = Depends(get_db)
) -> EvidenceSourceRead:
    return _call(approve_source, db, source_id, reviewer=payload.reviewer)


@router.post("/sources/{source_id}/revoke", response_model=EvidenceSourceRead)
def revoke_evidence_source(
    source_id: str, payload: ReviewerAction, db: Session = Depends(get_db)
) -> EvidenceSourceRead:
    return _call(revoke_source, db, source_id, reviewer=payload.reviewer)


@router.post("/exhibits/{exhibit_id}/sources/{source_id}", response_model=EvidenceLinkRead)
def attach_evidence_source(
    exhibit_id: str, source_id: str, db: Session = Depends(get_db)
) -> EvidenceLinkRead:
    return _call(link_source, db, exhibit_id, source_id)


@router.post("/exhibits/{exhibit_id}/approve", response_model=ExhibitApprovalRead)
def approve_evidence_exhibit(
    exhibit_id: str, payload: ReviewerAction, db: Session = Depends(get_db)
) -> ExhibitApprovalRead:
    return _call(approve_exhibit, db, exhibit_id, reviewer=payload.reviewer)


@router.post("/exhibits/{exhibit_id}/revoke", response_model=ExhibitApprovalRead)
def revoke_evidence_exhibit(
    exhibit_id: str, payload: ReviewerAction, db: Session = Depends(get_db)
) -> ExhibitApprovalRead:
    return _call(revoke_exhibit, db, exhibit_id, reviewer=payload.reviewer)


@router.get("/review-run-stats", response_model=ReviewRunStats)
def read_review_run_stats(db: Session = Depends(get_db)) -> ReviewRunStats:
    return get_review_run_stats(db)
