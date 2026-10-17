from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app import main as main_module
from app.core.config import Settings
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceSource
from app.models.claim_support_review import ClaimSupportReview
from app.models.visitor_state import VisitorVisitEventLog
from app.services.evidence_service import approve_source, create_source
from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.evidence_service import approve_exhibit, link_source
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


SOURCE = "南开大学正式创办于1919年。"
CITATION = {"source_id": "S01", "evidence_quote": SOURCE, "claim_text": SOURCE}
ANSWER = SOURCE + "[S01]"


def test_strict_history_release_requires_human_claim_support(db_session, monkeypatch) -> None:
    create_source(
        db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE,
    )
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    monkeypatch.setattr(main_module, "settings", Settings(
        api_key="business-test", operator_api_key="operator-test", claim_support_required=True,
    ))
    app = main_module.create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    business = {"X-HistoryGuide-Api-Key": "business-test"}
    operator = {"X-HistoryGuide-Operator-Key": "operator-test"}
    payload = {
        "question": "南开大学哪年创办？", "source_ids": ["S01"],
        "draft_answer": ANSWER, "citations": [CITATION],
    }
    try:
        with TestClient(app) as client:
            path = "/api/genios/answers/history"
            assert client.post(path, json=payload, headers=business).status_code == 409
            assert client.post("/api/evidence/claim-support", json=CITATION, headers=business).status_code == 401
            candidate = client.post("/api/evidence/claim-support", json=CITATION, headers=operator)
            assert candidate.status_code == 201
            review_id = candidate.json()["id"]
            assert candidate.json()["status"] == "draft"
            assert client.post(path, json=payload, headers=business).status_code == 409
            assert client.post(
                f"/api/evidence/claim-support/{review_id}/approve",
                json={"reviewer": "curator", "support_confirmed": False}, headers=operator,
            ).status_code == 422
            approved = client.post(
                f"/api/evidence/claim-support/{review_id}/approve",
                json={"reviewer": "curator", "support_confirmed": True}, headers=operator,
            )
            assert approved.status_code == 200
            released = client.post(path, json=payload, headers=business)
            assert released.status_code == 200
            assert released.json()["answer"] == ANSWER
            assert released.json()["claim_support_reviewed"] is True
            assert released.json()["semantic_verified"] is False
            release_log = db_session.scalar(select(AuditLog).where(
                AuditLog.action == "history_review_run_finalized",
                AuditLog.resource_id == released.json()["run_id"],
            ))
            assert release_log.details["claim_support_review_ids"] == [review_id]
            assert SOURCE not in str(release_log.details)

            assert client.post("/api/genios/history-runs", json={
                "question": payload["question"], "source_ids": ["S01"],
            }, headers=business).status_code == 409
            assert client.post(
                f"/api/evidence/claim-support/{review_id}/revoke",
                json={"reviewer": "curator"}, headers=operator,
            ).status_code == 200
            assert client.post(path, json=payload, headers=business).status_code == 409
            assert db_session.scalar(select(AuditLog).where(
                AuditLog.action == "claim_support_revoked", AuditLog.resource_id == review_id,
            )) is not None
    finally:
        app.dependency_overrides.clear()


def test_source_metadata_change_invalidates_claim_support(db_session) -> None:
    from app.services.claim_support_review_service import (
        approve_candidate, claim_support_issue, create_candidate,
    )

    create_source(
        db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE,
    )
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    review = create_candidate(db_session, **CITATION)
    approve_candidate(db_session, review.id, reviewer="curator")
    assert claim_support_issue(db_session, **CITATION) is None
    db_session.get(EvidenceSource, "S01").title = "Unreviewed title"
    db_session.commit()
    assert claim_support_issue(db_session, **CITATION) is not None


def test_unreviewed_negation_fragment_cannot_be_released(db_session) -> None:
    from app.services.claim_support_review_service import claim_support_issue, create_candidate

    text = "南开大学并非创办于1919年。"
    create_source(db_session, source_id="S02", title="Archive", source_uri="museum:S02", content_text=text)
    approve_source(db_session, "S02", reviewer="museum-reviewer")
    citation = {"source_id": "S02", "evidence_quote": text, "claim_text": "创办于1919年"}
    create_candidate(db_session, **citation)
    assert claim_support_issue(db_session, **citation) == "claim-to-quote support has not been approved"


def test_approved_review_text_edit_invalidates_support(db_session) -> None:
    from app.models.claim_support_review import ClaimSupportReview
    from app.services.claim_support_review_service import (
        approve_candidate, claim_support_issue, create_candidate,
    )

    create_source(db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE)
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    review = create_candidate(db_session, **CITATION)
    approve_candidate(db_session, review.id, reviewer="curator")
    assert claim_support_issue(db_session, **CITATION) is None
    db_session.get(ClaimSupportReview, review.id).claim_text = "Changed after review"
    db_session.commit()
    assert claim_support_issue(db_session, **CITATION) == "approved claim support record changed"


def test_operator_can_filter_claim_candidates(client, db_session, monkeypatch) -> None:
    from app.core.config import Settings

    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    create_source(db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE)
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    headers = {"X-HistoryGuide-Operator-Key": "operator-test"}
    assert client.get("/api/evidence/claim-support", headers=headers).json()["total"] == 0
    created = client.post("/api/evidence/claim-support", json=CITATION, headers=headers)
    assert created.status_code == 201
    review_id = created.json()["id"]
    listing = client.get("/api/evidence/claim-support?status=draft&limit=1", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == review_id
    assert client.get("/api/evidence/claim-support?status=approved", headers=headers).json()["total"] == 0
    assert client.get("/api/evidence/claim-support", headers={}).status_code == 401


def test_strict_release_uses_postgresql_row_locks(db_session, monkeypatch) -> None:
    from app.services import claim_support_review_service as service

    create_source(db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE)
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    review = service.create_candidate(db_session, **CITATION)
    service.approve_candidate(db_session, review.id, reviewer="curator")
    statements = []
    original_scalar = db_session.scalar

    def capture(statement, *args, **kwargs):
        statements.append(str(statement.compile(dialect=postgresql.dialect())))
        return original_scalar(statement, *args, **kwargs)

    monkeypatch.setattr(db_session, "scalar", capture)
    assert service.claim_support_issue(db_session, **CITATION, lock_for_release=True) is None
    assert any("FROM evidence_sources" in sql and "FOR UPDATE" in sql for sql in statements)
    assert any("FROM claim_support_reviews" in sql and "FOR UPDATE" in sql for sql in statements)


def test_strict_exhibit_release_audits_support_and_rejects_revocation(db_session, monkeypatch) -> None:
    from app.services.claim_support_review_service import approve_candidate, create_candidate, revoke_candidate

    create_exhibit(db_session, ExhibitCreate(
        id="E01", name="Reviewed exhibit", description="Reviewed description", period="test",
        importance=3, source_reference="museum:S01", keywords=[], people=[], themes=[],
    ))
    create_visitor_state(db_session, VisitorStateCreate(
        session_id="visit-01", visitor_type="tourist", current_exhibit="E01",
        visited_history=["E01"], interest=[], remaining_time=15,
    ))
    db_session.add(VisitorVisitEventLog(session_id="visit-01", exhibit_id="E01", remaining_time=15))
    db_session.commit()
    create_source(db_session, source_id="S01", title="Archive", source_uri="museum:S01", content_text=SOURCE)
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    link_source(db_session, "E01", "S01")
    approve_exhibit(db_session, "E01", reviewer="museum-reviewer")
    monkeypatch.setattr(main_module, "settings", Settings(
        api_key="business-test", operator_api_key="operator-test", claim_support_required=True,
    ))
    app = main_module.create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    headers = {"X-HistoryGuide-Api-Key": "business-test"}
    payload = {
        "session_id": "visit-01", "cited_exhibit_ids": "E01", "draft_answer": ANSWER,
        "citations": [{"exhibit_id": "E01", **CITATION}],
    }
    try:
        with TestClient(app) as client:
            assert client.post("/api/genios/review", json={
                "session_id": "visit-01", "draft_answer": ANSWER, "cited_exhibit_ids": "E01",
            }, headers=headers).status_code == 409
            initial = client.post("/api/genios/answers/exhibit", json=payload, headers=headers)
            assert initial.status_code == 409, initial.json()
            review = create_candidate(db_session, **CITATION)
            approve_candidate(db_session, review.id, reviewer="curator")
            released = client.post("/api/genios/answers/exhibit", json=payload, headers=headers)
            assert released.status_code == 200
            assert released.json()["decision"] == "pass"
            assert released.json()["claim_support_reviewed"] is True
            log = db_session.scalar(select(AuditLog).where(
                AuditLog.action == "review_run_finalized",
                AuditLog.resource_id == released.json()["run_id"],
            ))
            assert log.details["claim_support_review_ids"] == [review.id]
            assert SOURCE not in str(log.details)
            revoke_candidate(db_session, review.id, reviewer="curator")
            revoked = client.post("/api/genios/answers/exhibit", json=payload, headers=headers)
            assert revoked.status_code == 409, revoked.json()
    finally:
        app.dependency_overrides.clear()
