from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource
from app.schemas.approved_source_search import ApprovedSourceSearchRequest
from app.schemas.history_review_run import HistoryEvidenceExcerpt
from app.services.evidence_service import source_publication_issue
from app.services.history_review_run_service import EVIDENCE_EXCERPT_LIMIT


def search_approved_sources(
    db: Session, request: ApprovedSourceSearchRequest
) -> list[HistoryEvidenceExcerpt]:
    excerpt = func.substr(EvidenceSource.content_text, 1, EVIDENCE_EXCERPT_LIMIT)
    score = sum(
        (
            case((EvidenceSource.title.contains(term, autoescape=True), 3), else_=0)
            + case((excerpt.contains(term, autoescape=True), 1), else_=0)
        )
        for term in request.keywords
    )
    candidates = db.scalars(
        select(EvidenceSource)
        .where(EvidenceSource.status == "approved", score > 0)
        .order_by(score.desc(), EvidenceSource.id)
        .execution_options(yield_per=50)
    )
    results: list[HistoryEvidenceExcerpt] = []
    try:
        for source in candidates:
            if source_publication_issue(source) is not None:
                continue
            results.append(HistoryEvidenceExcerpt(
                source_id=source.id,
                title=source.title,
                source_uri=source.source_uri,
                content_sha256=source.content_sha256,
                excerpt_text=source.content_text[:EVIDENCE_EXCERPT_LIMIT],
                truncated=len(source.content_text) > EVIDENCE_EXCERPT_LIMIT,
            ))
            if len(results) == request.limit:
                break
    finally:
        candidates.close()
    return results
