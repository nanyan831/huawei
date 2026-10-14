from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import OPERATOR_API_KEY_HEADER
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceSource
from app.models.exhibit import Exhibit
from app.models.review_run import ReviewRun
from app.models.visitor_state import VisitorVisitEventLog
from app.schemas.review_run import ReviewRunRequest
from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.evidence_service import (
    approve_exhibit,
    approve_source,
    create_source,
    link_source,
    revoke_source,
)
from app.services.review_run_service import finalize_run, review_run
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


SESSION_ID = "run-session"
EXHIBIT_ID = "run-exhibit"
DRAFT = "请参观经过核验的展品。"


def _seed(db: Session) -> None:
    create_exhibit(
        db,
        ExhibitCreate(
            id=EXHIBIT_ID,
            name="Reviewed Exhibit",
            description="Reviewed exhibit for workflow tests.",
            period="test-period",
            keywords=["history"],
            importance=3,
            people=[],
            time_range=None,
            themes=["history"],
            source_reference="Museum archive record 1.",
        ),
    )
    create_visitor_state(
        db,
        VisitorStateCreate(
            session_id=SESSION_ID,
            visitor_type="tourist",
            current_exhibit=EXHIBIT_ID,
            visited_history=[EXHIBIT_ID],
            interest=["history"],
            remaining_time=15,
        ),
    )
    db.add(
        VisitorVisitEventLog(
            session_id=SESSION_ID,
            exhibit_id=EXHIBIT_ID,
            remaining_time=15,
        )
    )
    db.commit()
    create_source(
        db,
        source_id="run-source",
        title="Museum archive record 1",
        source_uri="museum-archive:record-1",
        content_text="Reviewed source text.",
    )
    approve_source(db, "run-source", reviewer="museum-reviewer")
    link_source(db, EXHIBIT_ID, "run-source")
    approve_exhibit(db, EXHIBIT_ID, reviewer="museum-reviewer")


def _prepare(client) -> str:
    response = client.post("/api/genios/runs", json={"session_id": SESSION_ID})
    assert response.status_code == 201
    assert response.json()["handoff"]["session_id"] == SESSION_ID
    assert response.json()["approved_evidence"][0]["source_id"] == "run-source"
    assert response.json()["approved_evidence"][0]["excerpt_text"] == "Reviewed source text."
    return response.json()["run_id"]


def _review(client, run_id: str, draft: str = DRAFT):
    return client.post(
        f"/api/genios/runs/{run_id}/review",
        json={
            "draft_answer": draft,
            "cited_exhibit_ids": EXHIBIT_ID,
            "citations": [{
                "exhibit_id": EXHIBIT_ID,
                "source_id": "run-source",
                "evidence_quote": "Reviewed source text.",
            }],
        },
    )


def _finalize(client, run_id: str, draft: str = DRAFT):
    return client.post(
        f"/api/genios/runs/{run_id}/finalize",
        json={"draft_answer": draft},
    )


def test_review_run_releases_only_reviewed_draft(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)

    assert _finalize(client, run_id).status_code == 409
    review = _review(client, run_id)
    assert review.status_code == 200
    assert review.json()["decision"] == "pass"
    audit = db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "review_run_checked", AuditLog.resource_id == run_id
        )
    )
    assert audit.details["citations"][0]["source_id"] == "run-source"
    assert DRAFT not in str(audit.details)
    assert "Reviewed source text." not in str(audit.details)
    assert _finalize(client, run_id, DRAFT + "未经审核的新句子").status_code == 409
    assert _finalize(client, run_id, DRAFT + " ").status_code == 409

    final = _finalize(client, run_id)
    assert final.status_code == 200
    assert final.json() == {"run_id": run_id, "decision": "pass", "answer": DRAFT}
    assert _finalize(client, run_id).status_code == 409
    assert _review(client, run_id).status_code == 409


def test_finalize_rejects_stale_loaded_status(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    assert _review(client, run_id).status_code == 200
    stale_run = db_session.get(ReviewRun, run_id)
    assert stale_run.status == "reviewed"
    db_session.execute(
        update(ReviewRun).where(ReviewRun.id == run_id).values(status="finalized"),
        execution_options={"synchronize_session": False},
    )
    assert stale_run.status == "reviewed"
    with pytest.raises(ValueError, match="already finalized or changed"):
        finalize_run(db_session, run_id, draft_answer=DRAFT)


def test_review_cannot_reopen_finalized_run(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    stale_run = db_session.get(ReviewRun, run_id)
    assert stale_run.status == "prepared"
    db_session.execute(
        update(ReviewRun).where(ReviewRun.id == run_id).values(status="finalized"),
        execution_options={"synchronize_session": False},
    )
    with pytest.raises(ValueError, match="already finalized or changed"):
        review_run(
            db_session, run_id,
            ReviewRunRequest(
                draft_answer=DRAFT,
                cited_exhibit_ids=EXHIBIT_ID,
                citations=[{
                    "exhibit_id": EXHIBIT_ID,
                    "source_id": "run-source",
                    "evidence_quote": "Reviewed source text.",
                }],
            ),
        )


def test_review_run_invalidates_when_evidence_is_revoked(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    assert _review(client, run_id).json()["decision"] == "pass"
    revoke_source(db_session, "run-source", reviewer="museum-reviewer")

    response = _finalize(client, run_id)
    assert response.status_code == 409
    assert "state changed" in response.json()["detail"]


def test_review_run_invalidates_when_exhibit_changes(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    exhibit = db_session.get(Exhibit, EXHIBIT_ID)
    exhibit.description = "Updated after preparing handoff."
    db_session.commit()

    assert _review(client, run_id).status_code == 409


def test_review_run_invalidates_when_source_text_changes(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    source = db_session.get(EvidenceSource, "run-source")
    source.content_text = "Changed without a new approval."
    db_session.commit()

    assert _review(client, run_id).status_code == 409


def test_review_run_expires(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    run = db_session.get(ReviewRun, run_id)
    run.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    assert _review(client, run_id).status_code == 409


def test_review_run_requires_revision_for_unknown_exhibit(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    response = client.post(
        f"/api/genios/runs/{run_id}/review",
        json={"draft_answer": DRAFT, "cited_exhibit_ids": "unknown-exhibit"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "revise"
    assert _finalize(client, run_id).status_code == 409


def test_review_run_requires_approved_source_quote(client, db_session: Session) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    missing_citation = client.post(
        f"/api/genios/runs/{run_id}/review",
        json={"draft_answer": DRAFT, "cited_exhibit_ids": EXHIBIT_ID},
    )
    assert missing_citation.status_code == 200
    assert missing_citation.json()["decision"] == "revise"
    assert "approved evidence citation" in missing_citation.json()["issues"]

    false_quote = client.post(
        f"/api/genios/runs/{run_id}/review",
        json={
            "draft_answer": DRAFT,
            "cited_exhibit_ids": EXHIBIT_ID,
            "citations": [{
                "exhibit_id": EXHIBIT_ID,
                "source_id": "run-source",
                "evidence_quote": "This sentence is not in the source.",
            }],
        },
    )
    assert false_quote.status_code == 200
    assert false_quote.json()["decision"] == "revise"
    assert "absent from approved source text" in false_quote.json()["issues"]

    whitespace_quote = client.post(
        f"/api/genios/runs/{run_id}/review",
        json={
            "draft_answer": DRAFT,
            "cited_exhibit_ids": EXHIBIT_ID,
            "citations": [{
                "exhibit_id": EXHIBIT_ID,
                "source_id": "run-source",
                "evidence_quote": "          ",
            }],
        },
    )
    assert whitespace_quote.status_code == 200
    assert whitespace_quote.json()["decision"] == "revise"
    assert _finalize(client, run_id).status_code == 409


def test_review_run_rejects_unlinked_source(client, db_session: Session) -> None:
    _seed(db_session)
    create_source(
        db_session,
        source_id="other-source",
        title="Other archive",
        source_uri="museum-archive:other",
        content_text="Some unrelated approved text.",
    )
    approve_source(db_session, "other-source", reviewer="museum-reviewer")
    run_id = _prepare(client)
    response = client.post(
        f"/api/genios/runs/{run_id}/review",
        json={
            "draft_answer": DRAFT,
            "cited_exhibit_ids": EXHIBIT_ID,
            "citations": [{
                "exhibit_id": EXHIBIT_ID,
                "source_id": "other-source",
                "evidence_quote": "Some unrelated approved text.",
            }],
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "revise"
    assert "not approved and linked" in response.json()["issues"]


def test_review_run_missing_session_and_run(client) -> None:
    response = client.post("/api/genios/runs", json={"session_id": "absent"})
    assert response.status_code == 404
    response = _review(client, "absent-run")
    assert response.status_code == 404


def test_review_run_stats_are_operator_only_and_do_not_expose_drafts(
    client, db_session: Session, monkeypatch
) -> None:
    _seed(db_session)
    run_id = _prepare(client)
    assert _review(client, run_id).json()["decision"] == "pass"
    assert _finalize(client, run_id).status_code == 200

    assert client.get("/api/evidence/review-run-stats").status_code == 503
    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    assert client.get("/api/evidence/review-run-stats").status_code == 401
    response = client.get(
        "/api/evidence/review-run-stats",
        headers={OPERATOR_API_KEY_HEADER: "operator-test"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "total": 1,
        "prepared": 0,
        "reviewed": 0,
        "finalized": 1,
        "expired_open": 0,
        "passed": 1,
        "revise_requested": 0,
        "blocked": 0,
        "history_total": 0,
        "history_prepared": 0,
        "history_reviewed": 0,
        "history_finalized": 0,
        "history_expired_open": 0,
        "history_passed": 0,
        "history_revise_requested": 0,
    }
    assert DRAFT not in response.text
