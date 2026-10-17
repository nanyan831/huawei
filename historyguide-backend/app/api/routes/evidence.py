from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import OPERATOR_API_KEY_HEADER, access_key_matches
from app.database.session import get_db
from app.models.evidence import EvidenceSource, ExhibitApproval, ExhibitEvidenceLink
from app.models.exhibit import Exhibit
from app.schemas.evidence import (
    EvidenceLinkRead,
    EvidenceSourceCreate,
    EvidenceSourceBatchCreate,
    EvidenceSourceBatchRead,
    EvidenceSourceBatchPreview,
    EvidenceSourcePage,
    EvidenceSourceRead,
    ExhibitApprovalRead,
    ReviewerAction,
    EvidenceExhibitBatchCreate,
    EvidenceExhibitBatchRead,
    EvidenceExhibitUpload,
    EvidenceExhibitRead,
    EvidenceExhibitPage,
)
from app.schemas.exhibit import ExhibitRead
from app.models.claim_support_review import ClaimSupportReview
from app.schemas.claim_support_review import (
    ClaimSupportApproval, ClaimSupportCandidate, ClaimSupportPage, ClaimSupportRead, ClaimSupportRevocation,
)
from app.services.claim_support_review_service import (
    approve_candidate, create_candidate, list_candidates, revoke_candidate,
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
    validate_sources_batch,
    exhibit_approval_issue,
)
from app.services.exhibit_import_service import (
    import_exhibit_batch, import_exhibit_with_sources, validate_exhibit_batch,
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
    if not access_key_matches(operator_key, configured_key):
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


@router.post("/sources/batch/preview", response_model=EvidenceSourceBatchPreview)
def preview_evidence_sources(
    payload: EvidenceSourceBatchCreate, db: Session = Depends(get_db)
) -> EvidenceSourceBatchPreview:
    items = _call(validate_sources_batch, db, payload.sources)
    return EvidenceSourceBatchPreview(count=len(items), items=items)


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


@router.post("/claim-support", response_model=ClaimSupportRead, status_code=201)
def add_claim_support_candidate(
    payload: ClaimSupportCandidate, db: Session = Depends(get_db)
) -> ClaimSupportRead:
    return _call(create_candidate, db, **payload.model_dump())


@router.get("/claim-support", response_model=ClaimSupportPage)
def read_claim_support_candidates(
    status_filter: Literal["draft", "approved", "revoked"] | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ClaimSupportPage:
    items, total = list_candidates(db, status=status_filter, offset=offset, limit=limit)
    return ClaimSupportPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/claim-support/{review_id}", response_model=ClaimSupportRead)
def read_claim_support_candidate(review_id: str, db: Session = Depends(get_db)) -> ClaimSupportRead:
    review = db.get(ClaimSupportReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Claim support candidate was not found.")
    return review


@router.post("/claim-support/{review_id}/approve", response_model=ClaimSupportRead)
def approve_claim_support_candidate(
    review_id: str, payload: ClaimSupportApproval, db: Session = Depends(get_db)
) -> ClaimSupportRead:
    return _call(approve_candidate, db, review_id, reviewer=payload.reviewer)


@router.post("/claim-support/{review_id}/revoke", response_model=ClaimSupportRead)
def revoke_claim_support_candidate(
    review_id: str, payload: ClaimSupportRevocation, db: Session = Depends(get_db)
) -> ClaimSupportRead:
    return _call(revoke_candidate, db, review_id, reviewer=payload.reviewer)


@router.post("/exhibits/batch/preview", response_model=EvidenceExhibitBatchRead)
def preview_evidence_exhibits(
    payload: EvidenceExhibitBatchCreate, db: Session = Depends(get_db)
) -> EvidenceExhibitBatchRead:
    _call(validate_exhibit_batch, db, payload.exhibits)
    return EvidenceExhibitBatchRead(count=len(payload.exhibits), items=payload.exhibits)


@router.post("/exhibits/batch", response_model=EvidenceExhibitBatchRead, status_code=201)
def add_evidence_exhibits(
    payload: EvidenceExhibitBatchCreate, db: Session = Depends(get_db)
) -> EvidenceExhibitBatchRead:
    records = _call(import_exhibit_batch, db, payload.exhibits)
    return EvidenceExhibitBatchRead(count=len(records), items=records)


@router.post("/exhibits", response_model=EvidenceExhibitRead, status_code=201)
def upload_evidence_exhibit(
    payload: EvidenceExhibitUpload, db: Session = Depends(get_db)
) -> EvidenceExhibitRead:
    record = _call(
        import_exhibit_with_sources,
        db,
        payload.exhibit,
        source_ids=payload.source_ids,
    )
    return _exhibit_detail(db, record)


def _exhibit_detail(db: Session, exhibit: Exhibit) -> EvidenceExhibitRead:
    return EvidenceExhibitRead(
        exhibit=ExhibitRead.model_validate(exhibit),
        approval=db.get(ExhibitApproval, exhibit.id),
        source_ids=list(db.scalars(
            select(ExhibitEvidenceLink.source_id)
            .where(ExhibitEvidenceLink.exhibit_id == exhibit.id)
            .order_by(ExhibitEvidenceLink.source_id)
        )),
        approval_issue=exhibit_approval_issue(db, exhibit),
    )


@router.get("/exhibits", response_model=EvidenceExhibitPage)
def read_evidence_exhibits(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> EvidenceExhibitPage:
    total = db.scalar(select(func.count()).select_from(Exhibit)) or 0
    exhibits = db.scalars(select(Exhibit).order_by(Exhibit.id).offset(offset).limit(limit))
    return EvidenceExhibitPage(
        items=[_exhibit_detail(db, exhibit) for exhibit in exhibits],
        total=total, offset=offset, limit=limit,
    )


@router.get("/exhibits/{exhibit_id}", response_model=EvidenceExhibitRead)
def read_evidence_exhibit(exhibit_id: str, db: Session = Depends(get_db)) -> EvidenceExhibitRead:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise HTTPException(status_code=404, detail="Exhibit was not found.")
    return _exhibit_detail(db, exhibit)


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
