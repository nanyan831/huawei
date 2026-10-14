from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceSource
from app.models.history_review_run import HistoryReviewRun
from app.schemas.history_review_run import HistoryReviewRequest
from app.services.evidence_service import approve_source, create_source, revoke_source
from app.services.history_review_run_service import finalize_history_run, review_history_run
from app.services.review_run_stats_service import get_review_run_stats


QUESTION = "南开大学哪年创办？"
SOURCE_TEXT = "南开大学正式创办于1919年。"
DRAFT = "南开大学正式创办于1919年。[S01]"


def _seed_source(db_session, source_id: str = "S01", *, approved: bool = True) -> None:
    create_source(
        db_session,
        source_id=source_id,
        title="University archive",
        source_uri=f"university-archive:{source_id}",
        content_text=SOURCE_TEXT,
    )
    if approved:
        approve_source(db_session, source_id, reviewer="museum-reviewer")


def _prepare(client, source_ids=None):
    return client.post(
        "/api/genios/history-runs",
        json={"question": QUESTION, "source_ids": source_ids or ["S01"]},
    )


def _review(client, run_id: str, *, draft: str = DRAFT, citations=None):
    if citations is None:
        citations = [{"source_id": "S01", "evidence_quote": SOURCE_TEXT}]
    return client.post(
        f"/api/genios/history-runs/{run_id}/review",
        json={"draft_answer": draft, "citations": citations},
    )


def _finalize(client, run_id: str, draft: str = DRAFT):
    return client.post(
        f"/api/genios/history-runs/{run_id}/finalize",
        json={"draft_answer": draft},
    )


def test_history_run_releases_reviewed_cited_answer(client, db_session) -> None:
    _seed_source(db_session)
    response = _prepare(client)
    assert response.status_code == 201
    body = response.json()
    assert body["approved_evidence"][0]["source_id"] == "S01"
    assert body["approved_evidence"][0]["excerpt_text"] == SOURCE_TEXT
    run_id = body["run_id"]
    assert _finalize(client, run_id).status_code == 409

    review = _review(client, run_id)
    assert review.status_code == 200
    assert review.json()["decision"] == "pass"
    assert review.json()["semantic_verified"] is False
    assert _finalize(client, run_id, DRAFT + " ").status_code == 409

    final = _finalize(client, run_id)
    assert final.status_code == 200
    assert final.json()["answer"] == DRAFT
    assert final.json()["semantic_verified"] is False
    assert _finalize(client, run_id).status_code == 409

    stats = get_review_run_stats(db_session)
    assert stats.history_total == 1
    assert stats.history_finalized == 1
    assert stats.history_passed == 1

    audit = db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "history_review_run_checked", AuditLog.resource_id == run_id
        )
    )
    assert audit.details["citations"][0]["source_id"] == "S01"
    assert QUESTION not in str(audit.details)
    assert DRAFT not in str(audit.details)
    assert SOURCE_TEXT not in str(audit.details)


def test_history_finalize_rejects_stale_loaded_status(client, db_session) -> None:
    _seed_source(db_session)
    run_id = _prepare(client).json()["run_id"]
    assert _review(client, run_id).status_code == 200
    stale_run = db_session.get(HistoryReviewRun, run_id)
    assert stale_run.status == "reviewed"
    db_session.execute(
        update(HistoryReviewRun).where(HistoryReviewRun.id == run_id).values(status="finalized"),
        execution_options={"synchronize_session": False},
    )
    assert stale_run.status == "reviewed"
    with pytest.raises(ValueError, match="already finalized or changed"):
        finalize_history_run(db_session, run_id, draft_answer=DRAFT)


def test_history_review_cannot_reopen_finalized_run(client, db_session) -> None:
    _seed_source(db_session)
    run_id = _prepare(client).json()["run_id"]
    stale_run = db_session.get(HistoryReviewRun, run_id)
    assert stale_run.status == "prepared"
    db_session.execute(
        update(HistoryReviewRun).where(HistoryReviewRun.id == run_id).values(status="finalized"),
        execution_options={"synchronize_session": False},
    )
    with pytest.raises(ValueError, match="already finalized or changed"):
        review_history_run(
            db_session, run_id,
            HistoryReviewRequest(
                draft_answer=DRAFT,
                citations=[{"source_id": "S01", "evidence_quote": SOURCE_TEXT}],
            ),
        )


def test_history_run_requires_approved_nonfixture_source(client, db_session) -> None:
    assert _prepare(client).status_code == 409
    _seed_source(db_session, approved=False)
    assert _prepare(client).status_code == 409
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    assert _prepare(client).status_code == 201

    _seed_source(db_session, "fixture-history")
    assert _prepare(client, ["fixture-history"]).status_code == 409
    assert _prepare(client, ["S01", "S01"]).status_code == 409
    assert client.post(
        "/api/genios/history-runs",
        json={"question": "   ", "source_ids": ["S01"]},
    ).status_code == 409


def test_history_run_revises_missing_or_false_citation(client, db_session) -> None:
    _seed_source(db_session)
    run_id = _prepare(client).json()["run_id"]

    missing = _review(client, run_id, citations=[])
    assert missing.json()["decision"] == "revise"
    assert _finalize(client, run_id).status_code == 409

    false_quote = _review(
        client, run_id,
        citations=[{"source_id": "S01", "evidence_quote": "这段话不在审批来源中。"}],
    )
    assert false_quote.json()["decision"] == "revise"
    assert "absent from approved source text" in false_quote.json()["issues"]

    no_visible_citation = _review(client, run_id, draft="南开大学创办于1919年。")
    assert no_visible_citation.json()["decision"] == "revise"
    assert "does not cite [S01]" in no_visible_citation.json()["issues"]

    assert _review(client, run_id).json()["decision"] == "pass"
    assert _finalize(client, run_id).status_code == 200


def test_history_run_invalidates_revoked_or_changed_source(client, db_session) -> None:
    _seed_source(db_session)
    run_id = _prepare(client).json()["run_id"]
    revoke_source(db_session, "S01", reviewer="museum-reviewer")
    assert _review(client, run_id).status_code == 409

    _seed_source(db_session, "S02")
    second_run = _prepare(client, ["S02"]).json()["run_id"]
    source = db_session.get(EvidenceSource, "S02")
    source.content_text = "Changed after approval."
    db_session.commit()
    assert _review(client, second_run).status_code == 409


def test_history_run_expiry_and_missing_run(client, db_session) -> None:
    _seed_source(db_session)
    run_id = _prepare(client).json()["run_id"]
    run = db_session.get(HistoryReviewRun, run_id)
    run.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    assert _review(client, run_id).status_code == 409
    assert _review(client, "missing-run").status_code == 404
