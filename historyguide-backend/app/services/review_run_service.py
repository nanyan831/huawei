import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource, ExhibitApproval, ExhibitEvidenceLink
from app.models.exhibit import Exhibit
from app.models.review_run import ReviewRun
from app.models.visitor_state import VisitorState
from app.schemas.genios_context import GeniosHandoffPackage, GeniosReviewRequest
from app.schemas.review_run import ApprovedEvidenceExcerpt, PrepareRunRequest, ReviewRunRequest
from app.services.audit_log_service import record_audit_log
from app.services.evidence_service import exhibit_approval_issue
from app.services.genios_context_service import build_genios_handoff_package, review_genios_answer


RUN_LIFETIME = timedelta(minutes=15)
EVIDENCE_EXCERPT_LIMIT = 8000


def prepare_run(
    db: Session, visitor_state: VisitorState, request: PrepareRunRequest
) -> tuple[ReviewRun, GeniosHandoffPackage]:
    handoff = build_genios_handoff_package(
        db, visitor_state,
        recommendation_limit=request.recommendation_limit,
        route_max_items=request.route_max_items,
    )
    now = datetime.now(timezone.utc)
    run = ReviewRun(
        id=str(uuid4()),
        session_id=request.session_id,
        snapshot_sha256=_snapshot_sha256(db, handoff),
        recommendation_limit=request.recommendation_limit,
        route_max_items=request.route_max_items,
        status="prepared",
        expires_at=now + RUN_LIFETIME,
    )
    db.add(run)
    record_audit_log(
        db, action="review_run_prepared", resource_type="review_run",
        resource_id=run.id, details={"session_id": run.session_id},
    )
    db.commit()
    db.refresh(run)
    return run, handoff


def approved_evidence_for_handoff(
    db: Session, handoff: GeniosHandoffPackage
) -> list[ApprovedEvidenceExcerpt]:
    excerpts: list[ApprovedEvidenceExcerpt] = []
    for exhibit_id in handoff.context.grounding_exhibit_ids:
        exhibit = db.get(Exhibit, exhibit_id)
        if exhibit is None or exhibit_approval_issue(db, exhibit) is not None:
            continue
        for source in _linked_sources(db, exhibit_id):
            if source.status != "approved":
                continue
            excerpts.append(
                ApprovedEvidenceExcerpt(
                    exhibit_id=exhibit_id,
                    source_id=source.id,
                    title=source.title,
                    source_uri=source.source_uri,
                    content_sha256=source.content_sha256,
                    excerpt_text=source.content_text[:EVIDENCE_EXCERPT_LIMIT],
                    truncated=len(source.content_text) > EVIDENCE_EXCERPT_LIMIT,
                )
            )
    return excerpts


def review_run(
    db: Session, run_id: str, request: ReviewRunRequest
) -> ReviewRun:
    run, visitor_state = _current_run(db, run_id)
    if run.status == "finalized":
        raise ValueError("Finalized runs cannot be reviewed again.")
    _assert_snapshot_current(db, run, visitor_state)
    review = GeniosReviewRequest(
        session_id=run.session_id,
        draft_answer=request.draft_answer,
        cited_exhibit_ids=request.cited_exhibit_ids,
        recommendation_limit=run.recommendation_limit,
        route_max_items=run.route_max_items,
    )
    result = review_genios_answer(db, visitor_state, review)
    citation_issues = _citation_issues(db, request)
    draft_sha256 = _sha256(request.draft_answer)
    decision = "revise" if citation_issues and result.decision == "pass" else result.decision
    safe_answer = (
        "展品来源引用未通过检查，请依据已审批资料重新生成并复核。"
        if decision == "revise" and citation_issues
        else result.safe_answer
    )
    updated = db.execute(
        update(ReviewRun)
        .where(ReviewRun.id == run.id, ReviewRun.status.in_(("prepared", "reviewed")))
        .values(
            draft_sha256=draft_sha256,
            decision=decision,
            issues=" | ".join(filter(None, [result.issues, *citation_issues])),
            safe_answer=safe_answer,
            status="reviewed",
        ),
        execution_options={"synchronize_session": False},
    )
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("Review run was already finalized or changed; prepare a new run.")
    record_audit_log(
        db, action="review_run_checked", resource_type="review_run",
        resource_id=run.id,
        details={
            "decision": decision,
            "draft_sha256": draft_sha256,
            "citations": [
                {
                    "exhibit_id": citation.exhibit_id,
                    "source_id": citation.source_id,
                    "quote_sha256": _sha256(citation.evidence_quote),
                }
                for citation in request.citations
            ],
        },
    )
    db.commit()
    db.refresh(run)
    return run


def finalize_run(db: Session, run_id: str, *, draft_answer: str) -> ReviewRun:
    run, visitor_state = _current_run(db, run_id)
    if run.status != "reviewed" or run.decision not in ("pass", "block"):
        raise ValueError("Run has no finalizable review decision.")
    _assert_snapshot_current(db, run, visitor_state)
    if run.draft_sha256 != _sha256(draft_answer):
        raise ValueError("Final answer does not match the reviewed draft.")
    finalized_at = datetime.now(timezone.utc)
    updated = db.execute(
        update(ReviewRun)
        .where(
            ReviewRun.id == run.id,
            ReviewRun.status == "reviewed",
            ReviewRun.decision == run.decision,
            ReviewRun.draft_sha256 == run.draft_sha256,
        )
        .values(status="finalized", finalized_at=finalized_at),
        execution_options={"synchronize_session": False},
    )
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("Review run was already finalized or changed; prepare a new run.")
    record_audit_log(
        db, action="review_run_finalized", resource_type="review_run",
        resource_id=run.id, details={"decision": run.decision},
    )
    db.commit()
    db.refresh(run)
    return run


def _current_run(db: Session, run_id: str) -> tuple[ReviewRun, VisitorState]:
    run = db.get(ReviewRun, run_id)
    if run is None:
        raise LookupError(f"Review run '{run_id}' was not found.")
    expiry = run.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expiry:
        raise ValueError("Review run has expired; prepare a new handoff.")
    visitor_state = db.get(VisitorState, run.session_id)
    if visitor_state is None:
        raise ValueError("Visitor session no longer exists.")
    return run, visitor_state


def _assert_snapshot_current(
    db: Session, run: ReviewRun, visitor_state: VisitorState
) -> None:
    current = build_genios_handoff_package(
        db, visitor_state,
        recommendation_limit=run.recommendation_limit,
        route_max_items=run.route_max_items,
    )
    if _snapshot_sha256(db, current) != run.snapshot_sha256:
        raise ValueError("Visitor or evidence state changed; prepare a new handoff.")


def _snapshot_sha256(db: Session, handoff: GeniosHandoffPackage) -> str:
    approvals = []
    for exhibit_id in handoff.context.grounding_exhibit_ids:
        exhibit = db.get(Exhibit, exhibit_id)
        approval = db.get(ExhibitApproval, exhibit_id)
        approvals.append({
            "exhibit_id": exhibit_id,
            "approved_fingerprint": approval.approved_fingerprint if approval else None,
            "approval_status": approval.status if approval else None,
            "approval_issue": exhibit_approval_issue(db, exhibit) if exhibit else "missing",
        })
    payload = {
        "context": handoff.context.model_dump(mode="json"),
        "route_plan": handoff.route_plan.model_dump(mode="json"),
        "source_safety": handoff.source_safety.model_dump(mode="json"),
        "approvals": approvals,
    }
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _citation_issues(db: Session, request: ReviewRunRequest) -> list[str]:
    cited_ids = [part.strip() for part in request.cited_exhibit_ids.split(",") if part.strip()]
    if not request.citations:
        return ["At least one approved evidence citation is required."]
    issues: list[str] = []
    covered_ids: set[str] = set()
    for citation in request.citations:
        if citation.exhibit_id not in cited_ids:
            issues.append(f"Citation exhibit {citation.exhibit_id} is not in cited_exhibit_ids.")
            continue
        source = db.get(EvidenceSource, citation.source_id)
        link = db.get(ExhibitEvidenceLink, (citation.exhibit_id, citation.source_id))
        if source is None or source.status != "approved" or link is None:
            issues.append(f"Source {citation.source_id} is not approved and linked to {citation.exhibit_id}.")
            continue
        normalized_quote = _normalized_quote(citation.evidence_quote)
        if len(normalized_quote) < 8 or normalized_quote not in _normalized_quote(source.content_text):
            issues.append(f"Quote for {citation.source_id} is absent from approved source text.")
            continue
        covered_ids.add(citation.exhibit_id)
    for exhibit_id in cited_ids:
        if exhibit_id not in covered_ids:
            issues.append(f"Cited exhibit {exhibit_id} lacks a valid evidence quote.")
    return issues


def _linked_sources(db: Session, exhibit_id: str) -> list[EvidenceSource]:
    return list(
        db.scalars(
            select(EvidenceSource)
            .join(ExhibitEvidenceLink, ExhibitEvidenceLink.source_id == EvidenceSource.id)
            .where(ExhibitEvidenceLink.exhibit_id == exhibit_id)
            .order_by(EvidenceSource.id)
        )
    )


def _normalized_quote(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
