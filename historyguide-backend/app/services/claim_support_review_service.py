import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.claim_support_review import ClaimSupportReview
from app.models.evidence import EvidenceSource
from app.services.audit_log_service import record_audit_log
from app.services.evidence_service import source_publication_issue


def _review_id(source_id: str, fingerprint: str, quote: str, claim: str) -> str:
    encoded = json.dumps([source_id, fingerprint, quote, claim], ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def list_candidates(
    db: Session, *, status: str | None, offset: int, limit: int
) -> tuple[list[ClaimSupportReview], int]:
    count_query = select(func.count()).select_from(ClaimSupportReview)
    items_query = select(ClaimSupportReview)
    if status:
        count_query = count_query.where(ClaimSupportReview.status == status)
        items_query = items_query.where(ClaimSupportReview.status == status)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(items_query.order_by(ClaimSupportReview.created_at.desc(), ClaimSupportReview.id).offset(offset).limit(limit)))
    return items, total


def create_candidate(
    db: Session, *, source_id: str, evidence_quote: str, claim_text: str
) -> ClaimSupportReview:
    source = db.get(EvidenceSource, source_id)
    if source is None:
        raise LookupError(f"Evidence source '{source_id}' was not found.")
    issue = source_publication_issue(source)
    if issue:
        raise ValueError(f"Source cannot support a claim: {issue}.")
    quote, claim = evidence_quote.strip(), claim_text.strip()
    if len(quote) < 8 or len(claim) < 8:
        raise ValueError("Evidence quote and claim must contain at least eight nonblank characters.")
    if quote not in source.content_text or claim not in quote:
        raise ValueError("Claim must be an exact excerpt of a quote in the approved source.")
    review_id = _review_id(source_id, source.approved_fingerprint, quote, claim)
    if db.get(ClaimSupportReview, review_id) is not None:
        raise ValueError("Claim support candidate already exists for this source version.")
    review = ClaimSupportReview(
        id=review_id, source_id=source_id, source_fingerprint=source.approved_fingerprint,
        evidence_quote=quote, claim_text=claim, status="draft",
    )
    try:
        db.add(review)
        record_audit_log(
            db, action="claim_support_candidate_created", resource_type="claim_support_review",
            resource_id=review_id, actor="operator", details={"source_id": source_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(review)
    return review


def approve_candidate(db: Session, review_id: str, *, reviewer: str) -> ClaimSupportReview:
    review = db.get(ClaimSupportReview, review_id)
    if review is None:
        raise LookupError("Claim support candidate was not found.")
    if review.status != "draft":
        raise ValueError("Only a draft claim support candidate can be approved.")
    if not reviewer.strip():
        raise ValueError("Reviewer identity is required.")
    source = db.get(EvidenceSource, review.source_id)
    if source is None or source_publication_issue(source) or source.approved_fingerprint != review.source_fingerprint:
        raise ValueError("Source approval changed; create a candidate for the current source version.")
    try:
        review.status = "approved"
        review.reviewed_by = reviewer.strip()
        review.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="claim_support_approved", resource_type="claim_support_review",
            resource_id=review_id, actor=review.reviewed_by,
            details={"source_id": review.source_id, "source_fingerprint": review.source_fingerprint},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(review)
    return review


def revoke_candidate(db: Session, review_id: str, *, reviewer: str) -> ClaimSupportReview:
    review = db.get(ClaimSupportReview, review_id)
    if review is None:
        raise LookupError("Claim support candidate was not found.")
    if review.status != "approved":
        raise ValueError("Only an approved claim support candidate can be revoked.")
    if not reviewer.strip():
        raise ValueError("Reviewer identity is required.")
    try:
        review.status = "revoked"
        review.reviewed_by = reviewer.strip()
        review.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="claim_support_revoked", resource_type="claim_support_review",
            resource_id=review_id, actor=review.reviewed_by,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(review)
    return review


def claim_support_review_id(
    *, source_id: str, source_fingerprint: str, evidence_quote: str, claim_text: str
) -> str:
    return _review_id(source_id, source_fingerprint, evidence_quote.strip(), claim_text.strip())


def claim_support_issue(
    db: Session, *, source_id: str, evidence_quote: str, claim_text: str,
    lock_for_release: bool = False,
) -> str | None:
    if lock_for_release:
        source = db.scalar(
            select(EvidenceSource).where(EvidenceSource.id == source_id)
            .with_for_update().execution_options(populate_existing=True)
        )
    else:
        source = db.get(EvidenceSource, source_id)
    if source is None:
        return "source missing"
    issue = source_publication_issue(source)
    if issue:
        return issue
    review_id = claim_support_review_id(
        source_id=source_id, source_fingerprint=source.approved_fingerprint,
        evidence_quote=evidence_quote, claim_text=claim_text,
    )
    if lock_for_release:
        review = db.scalar(
            select(ClaimSupportReview).where(ClaimSupportReview.id == review_id)
            .with_for_update().execution_options(populate_existing=True)
        )
    else:
        review = db.get(ClaimSupportReview, review_id)
    if review is None or review.status != "approved" or not review.reviewed_by or not review.reviewed_at:
        return "claim-to-quote support has not been approved"
    if review.source_fingerprint != source.approved_fingerprint:
        return "source version changed after claim support approval"
    if (
        review.source_id != source_id
        or review.evidence_quote != evidence_quote.strip()
        or review.claim_text != claim_text.strip()
        or review.evidence_quote not in source.content_text
        or review.claim_text not in review.evidence_quote
    ):
        return "approved claim support record changed"
    return None
