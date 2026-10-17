from sqlalchemy.orm import Session

from app.schemas.genios_answer import ExhibitAnswerRequest, HistoryAnswerRequest, ReleasedAnswer
from app.schemas.history_review_run import HistoryPrepareRequest, HistoryReviewRequest
from app.schemas.review_run import PrepareRunRequest, ReviewRunRequest
from app.services.history_review_run_service import (
    finalize_history_run,
    prepare_history_run,
    review_history_run,
)
from app.services.review_run_service import finalize_run, prepare_run, review_run
from app.services.visitor_state_service import get_visitor_state
from app.models.evidence import EvidenceSource
from app.services.claim_support_review_service import claim_support_issue, claim_support_review_id


def _require_claim_support(db: Session, citations) -> list[str]:
    review_ids = []
    for citation in sorted(citations, key=lambda item: (item.source_id, item.evidence_quote, item.claim_text)):
        issue = claim_support_issue(
            db, source_id=citation.source_id,
            evidence_quote=citation.evidence_quote, claim_text=citation.claim_text,
            lock_for_release=True,
        )
        if issue:
            raise ValueError(f"Claim support review is required for source {citation.source_id}: {issue}.")
        source = db.get(EvidenceSource, citation.source_id)
        review_ids.append(claim_support_review_id(
            source_id=citation.source_id, source_fingerprint=source.approved_fingerprint,
            evidence_quote=citation.evidence_quote, claim_text=citation.claim_text,
        ))
    return review_ids


def run_history_answer(
    db: Session, payload: HistoryAnswerRequest, *, require_claim_support: bool = False
) -> ReleasedAnswer:
    run, _ = prepare_history_run(
        db, HistoryPrepareRequest(question=payload.question, source_ids=payload.source_ids)
    )
    reviewed = review_history_run(
        db, run.id,
        HistoryReviewRequest(draft_answer=payload.draft_answer, citations=payload.citations),
    )
    if reviewed.decision != "pass":
        raise ValueError("History draft did not pass review; no answer was released.")
    review_ids = _require_claim_support(db, payload.citations) if require_claim_support else []
    finalized = finalize_history_run(
        db, run.id, draft_answer=payload.draft_answer, claim_support_review_ids=review_ids,
    )
    return ReleasedAnswer(
        run_id=run.id, decision="pass", answer=finalized.safe_answer or "",
        claim_support_reviewed=require_claim_support,
    )


def run_exhibit_answer(
    db: Session, payload: ExhibitAnswerRequest, *, require_claim_support: bool = False
) -> ReleasedAnswer:
    visitor_state = get_visitor_state(db, payload.session_id)
    if visitor_state is None:
        raise LookupError("Visitor session was not found.")
    run, _ = prepare_run(
        db, visitor_state,
        PrepareRunRequest(
            session_id=payload.session_id,
            recommendation_limit=payload.recommendation_limit,
            route_max_items=payload.route_max_items,
        ),
    )
    reviewed = review_run(
        db, run.id,
        ReviewRunRequest(
            draft_answer=payload.draft_answer,
            cited_exhibit_ids=payload.cited_exhibit_ids,
            citations=payload.citations,
        ),
    )
    if reviewed.decision == "revise":
        raise ValueError("Exhibit draft did not pass review; no answer was released.")
    review_ids = (
        _require_claim_support(db, payload.citations)
        if require_claim_support and reviewed.decision == "pass" else []
    )
    finalized = finalize_run(
        db, run.id, draft_answer=payload.draft_answer, claim_support_review_ids=review_ids,
    )
    return ReleasedAnswer(
        run_id=run.id, decision=finalized.decision,
        answer=finalized.safe_answer or "",
        claim_support_reviewed=require_claim_support and finalized.decision == "pass",
    )
