import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource
from app.models.history_review_run import HistoryReviewRun
from app.schemas.history_review_run import (
    HistoryEvidenceExcerpt,
    HistoryPrepareRequest,
    HistoryReviewRequest,
)
from app.services.audit_log_service import record_audit_log


RUN_LIFETIME = timedelta(minutes=15)
EVIDENCE_EXCERPT_LIMIT = 8000


def prepare_history_run(
    db: Session, request: HistoryPrepareRequest
) -> tuple[HistoryReviewRun, list[HistoryEvidenceExcerpt]]:
    if not request.question.strip():
        raise ValueError("History question must not be blank.")
    source_ids = [source_id.strip() for source_id in request.source_ids]
    if any(
        not source_id or len(source_id) > 64 or "[" in source_id or "]" in source_id
        for source_id in source_ids
    ):
        raise ValueError("Source ids must be nonempty and at most 64 characters.")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source ids are not allowed.")
    sources = _approved_sources(db, source_ids)
    now = datetime.now(timezone.utc)
    run = HistoryReviewRun(
        id=str(uuid4()),
        question_sha256=_sha256(request.question),
        source_ids=source_ids,
        snapshot_sha256=_snapshot_sha256(sources),
        status="prepared",
        expires_at=now + RUN_LIFETIME,
    )
    db.add(run)
    record_audit_log(
        db,
        action="history_review_run_prepared",
        resource_type="history_review_run",
        resource_id=run.id,
        details={"question_sha256": run.question_sha256, "source_ids": source_ids},
    )
    db.commit()
    db.refresh(run)
    excerpts = [
        HistoryEvidenceExcerpt(
            source_id=source.id,
            title=source.title,
            source_uri=source.source_uri,
            content_sha256=source.content_sha256,
            excerpt_text=source.content_text[:EVIDENCE_EXCERPT_LIMIT],
            truncated=len(source.content_text) > EVIDENCE_EXCERPT_LIMIT,
        )
        for source in sources
    ]
    return run, excerpts


def review_history_run(
    db: Session, run_id: str, request: HistoryReviewRequest
) -> HistoryReviewRun:
    run = _current_run(db, run_id)
    if run.status == "finalized":
        raise ValueError("Finalized runs cannot be reviewed again.")
    sources = _assert_snapshot_current(db, run)
    sources_by_id = {source.id: source for source in sources}
    issues: list[str] = []
    if not request.citations:
        issues.append("At least one approved source citation is required.")
    for citation in request.citations:
        source = sources_by_id.get(citation.source_id)
        if source is None:
            issues.append(f"Source {citation.source_id} was not prepared for this run.")
            continue
        quote = _normalize(citation.evidence_quote)
        if len(quote) < 8 or quote not in _normalize(source.content_text):
            issues.append(f"Quote for {citation.source_id} is absent from approved source text.")
        if f"[{citation.source_id}]" not in request.draft_answer:
            issues.append(f"Draft answer does not cite [{citation.source_id}].")
    draft_sha256 = _sha256(request.draft_answer)
    decision = "revise" if issues else "pass"
    safe_answer = (
        "当前回答的来源引用未通过检查，请依据已审批资料重新生成。"
        if issues else request.draft_answer.strip()
    )
    updated = db.execute(
        update(HistoryReviewRun)
        .where(
            HistoryReviewRun.id == run.id,
            HistoryReviewRun.status.in_(("prepared", "reviewed")),
        )
        .values(
            draft_sha256=draft_sha256,
            decision=decision,
            issues=" | ".join(issues),
            safe_answer=safe_answer,
            status="reviewed",
        ),
        execution_options={"synchronize_session": False},
    )
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("History review run was already finalized or changed; prepare a new run.")
    record_audit_log(
        db,
        action="history_review_run_checked",
        resource_type="history_review_run",
        resource_id=run.id,
        details={
            "decision": decision,
            "draft_sha256": draft_sha256,
            "citations": [
                {"source_id": citation.source_id, "quote_sha256": _sha256(citation.evidence_quote)}
                for citation in request.citations
            ],
        },
    )
    db.commit()
    db.refresh(run)
    return run


def finalize_history_run(db: Session, run_id: str, *, draft_answer: str) -> HistoryReviewRun:
    run = _current_run(db, run_id)
    if run.status != "reviewed" or run.decision != "pass":
        raise ValueError("Run has no finalizable review decision.")
    _assert_snapshot_current(db, run)
    if run.draft_sha256 != _sha256(draft_answer):
        raise ValueError("Final answer does not match the reviewed draft.")
    finalized_at = datetime.now(timezone.utc)
    updated = db.execute(
        update(HistoryReviewRun)
        .where(
            HistoryReviewRun.id == run.id,
            HistoryReviewRun.status == "reviewed",
            HistoryReviewRun.decision == run.decision,
            HistoryReviewRun.draft_sha256 == run.draft_sha256,
        )
        .values(status="finalized", finalized_at=finalized_at),
        execution_options={"synchronize_session": False},
    )
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("History review run was already finalized or changed; prepare a new run.")
    record_audit_log(
        db,
        action="history_review_run_finalized",
        resource_type="history_review_run",
        resource_id=run.id,
        details={"decision": run.decision},
    )
    db.commit()
    db.refresh(run)
    return run


def _current_run(db: Session, run_id: str) -> HistoryReviewRun:
    run = db.get(HistoryReviewRun, run_id)
    if run is None:
        raise LookupError(f"History review run '{run_id}' was not found.")
    expiry = run.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expiry:
        raise ValueError("History review run has expired; prepare a new run.")
    return run


def _assert_snapshot_current(db: Session, run: HistoryReviewRun) -> list[EvidenceSource]:
    sources = _approved_sources(db, run.source_ids)
    if _snapshot_sha256(sources) != run.snapshot_sha256:
        raise ValueError("Approved source state changed; prepare a new history review run.")
    return sources


def _approved_sources(db: Session, source_ids: list[str]) -> list[EvidenceSource]:
    sources: list[EvidenceSource] = []
    for source_id in source_ids:
        source = db.get(EvidenceSource, source_id)
        if source is None or source.status != "approved" or source.id.startswith("fixture-"):
            raise ValueError(f"Source {source_id} is not approved for history answers.")
        if _sha256(source.content_text) != source.content_sha256:
            raise ValueError(f"Source {source_id} changed after approval.")
        sources.append(source)
    return sources


def _snapshot_sha256(sources: list[EvidenceSource]) -> str:
    payload = [
        {
            "id": source.id,
            "title": source.title,
            "source_uri": source.source_uri,
            "status": source.status,
            "content_sha256": source.content_sha256,
        }
        for source in sources
    ]
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
