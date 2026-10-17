from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main as main_module
from app.core.config import Settings
from app.core.visitor_tokens import issue_visitor_token, verify_visitor_token
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.visitor_access_grant import VisitorAccessGrant
from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.evidence_service import approve_exhibit, approve_source, create_source, link_source
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


def _create_exhibit(db_session, exhibit_id: str, *, approved: bool) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id=exhibit_id, name=exhibit_id, description="Local test exhibit.",
            period="test", keywords=["history"], importance=3,
            people=[], time_range=None, themes=["history"],
            source_reference="Local test source.",
        ),
    )
    if approved:
        link_source(db_session, exhibit_id, "visitor-source")
        approve_exhibit(db_session, exhibit_id, reviewer="test-reviewer")


def test_visitor_gateway_defaults_closed(client) -> None:
    assert client.get("/api/visitor/me").status_code == 404
    assert client.post("/api/visitor/grants", json={"session_id": "any"}).status_code == 404


def test_visitor_gateway_requires_independent_keys(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "settings", Settings(visitor_gateway_enabled=True, api_key="business"),
    )
    try:
        main_module.create_app()
        assert False, "gateway started without a signing key"
    except ValueError as exc:
        assert "requires business and visitor signing keys" in str(exc)

    monkeypatch.setattr(
        main_module, "settings",
        Settings(visitor_gateway_enabled=True, api_key="business", visitor_signing_key="business"),
    )
    try:
        main_module.create_app()
        assert False, "gateway accepted a reused business key"
    except ValueError as exc:
        assert "must be separate" in str(exc)

    monkeypatch.setattr(
        main_module, "settings",
        Settings(visitor_gateway_enabled=True, api_key="business", visitor_signing_key="too-short"),
    )
    try:
        main_module.create_app()
        assert False, "gateway accepted a short signing key"
    except ValueError as exc:
        assert "at least 32" in str(exc)


def test_visitor_token_is_scoped_signed_and_expires(monkeypatch) -> None:
    from app.core import visitor_tokens

    monkeypatch.setattr(visitor_tokens.time, "time", lambda: 1000)
    token, expiry = issue_visitor_token("visit-one", "visitor-signing-key", 5)
    assert expiry == 1300
    assert verify_visitor_token(token, "visitor-signing-key") == "visit-one"
    assert verify_visitor_token(token + "x", "visitor-signing-key") is None
    assert verify_visitor_token(token, "another-key") is None
    monkeypatch.setattr(visitor_tokens.time, "time", lambda: 1300)
    assert verify_visitor_token(token, "visitor-signing-key") is None


def test_visitor_gateway_scopes_session_and_filters_unapproved_exhibits(
    db_session, monkeypatch,
) -> None:
    create_source(
        db_session, source_id="visitor-source", title="Local test source",
        source_uri="test:visitor", content_text="Local test exhibit evidence.",
    )
    approve_source(db_session, "visitor-source", reviewer="test-reviewer")
    _create_exhibit(db_session, "approved-exhibit", approved=True)
    _create_exhibit(db_session, "pending-exhibit", approved=False)
    for session_id in ("visit-one", "visit-two"):
        create_visitor_state(
            db_session,
            VisitorStateCreate(
                session_id=session_id, visitor_type="tourist", current_exhibit=None,
                visited_history=[], interest=["history"], remaining_time=20,
            ),
        )

    monkeypatch.setattr(
        main_module, "settings",
        Settings(
            api_key="business-key", visitor_gateway_enabled=True,
            visitor_signing_key="separate-visitor-signing-key-0123456789",
        ),
    )
    app = main_module.create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as client:
            assert client.post("/api/visitor/grants", json={"session_id": "visit-one"}).status_code == 401
            grant = client.post(
                "/api/visitor/grants", json={"session_id": "visit-one"},
                headers={"X-HistoryGuide-Api-Key": "business-key"},
            )
            assert grant.status_code == 201
            assert grant.headers["Cache-Control"] == "no-store"
            token = grant.json()["access_token"]
            assert "business-key" not in token
            visitor_headers = {"Authorization": f"Bearer {token}"}
            forged_but_signed, _ = issue_visitor_token(
                "visit-one", "separate-visitor-signing-key-0123456789", 5
            )
            assert client.get(
                "/api/visitor/me", headers={"Authorization": f"Bearer {forged_but_signed}"}
            ).status_code == 401

            assert client.get("/api/visitor/me", headers={"X-HistoryGuide-Api-Key": "business-key"}).status_code == 401
            me = client.get("/api/visitor/me", headers=visitor_headers)
            assert me.status_code == 200
            assert me.headers["Cache-Control"] == "no-store"
            assert me.json()["session_id"] == "visit-one"
            assert client.get("/api/visitor/me", headers={"Authorization": f"Bearer {token}x"}).status_code == 401
            assert client.get("/api/visitor/exhibits/pending-exhibit", headers=visitor_headers).status_code == 404
            assert client.get("/api/visitor/exhibits/approved-exhibit", headers=visitor_headers).status_code == 200

            route = client.get("/api/visitor/route", headers=visitor_headers)
            assert route.status_code == 200
            assert [item["exhibit_id"] for item in route.json()["items"]] == ["approved-exhibit"]
            assert client.post(
                "/api/visitor/visit-events", json={"exhibit_id": "pending-exhibit"},
                headers=visitor_headers,
            ).status_code == 404
            event = client.post(
                "/api/visitor/visit-events", json={"exhibit_id": "approved-exhibit"},
                headers=visitor_headers,
            )
            assert event.status_code == 200
            assert event.json()["session_id"] == "visit-one"
            history_payload = {
                "question": "What does this source say?",
                "source_ids": ["visitor-source"],
                "draft_answer": "Local test exhibit evidence.[visitor-source]",
                "citations": [{
                    "source_id": "visitor-source",
                    "evidence_quote": "Local test exhibit evidence.",
                    "claim_text": "Local test exhibit evidence.",
                }],
            }
            history_answer = client.post(
                "/api/visitor/answers/history", json=history_payload, headers=visitor_headers,
            )
            assert history_answer.status_code == 200
            assert history_answer.json()["answer"] == history_payload["draft_answer"]
            history_payload["draft_answer"] += " Unsupported extra sentence."
            rejected = client.post(
                "/api/visitor/answers/history", json=history_payload, headers=visitor_headers,
            )
            assert rejected.status_code == 409
            assert "Unsupported extra sentence" not in rejected.text

            exhibit_payload = {
                "draft_answer": "Local test exhibit evidence.[visitor-source]",
                "cited_exhibit_ids": "approved-exhibit",
                "citations": [{
                    "exhibit_id": "approved-exhibit",
                    "source_id": "visitor-source",
                    "evidence_quote": "Local test exhibit evidence.",
                    "claim_text": "Local test exhibit evidence.",
                }],
            }
            exhibit_answer = client.post(
                "/api/visitor/answers/exhibit", json=exhibit_payload, headers=visitor_headers,
            )
            assert exhibit_answer.status_code == 200
            assert exhibit_answer.json()["decision"] == "block"
            assert exhibit_answer.json()["answer"] != exhibit_payload["draft_answer"]
            link_source(db_session, "pending-exhibit", "visitor-source")
            approve_exhibit(db_session, "pending-exhibit", reviewer="test-reviewer")
            exhibit_answer = client.post(
                "/api/visitor/answers/exhibit", json=exhibit_payload, headers=visitor_headers,
            )
            assert exhibit_answer.status_code == 200
            assert exhibit_answer.json()["decision"] == "pass"
            assert exhibit_answer.json()["answer"] == exhibit_payload["draft_answer"]
            exhibit_payload["session_id"] = "visit-two"
            assert client.post(
                "/api/visitor/answers/exhibit", json=exhibit_payload, headers=visitor_headers,
            ).status_code == 422
            assert client.get("/api/visitor/me", headers=visitor_headers).json()["session_id"] == "visit-one"
            assert client.get("/api/visitor-states/visit-two", headers=visitor_headers).status_code == 401

            second_grant = client.post(
                "/api/visitor/grants", json={"session_id": "visit-two"},
                headers={"X-HistoryGuide-Api-Key": "business-key"},
            )
            assert second_grant.status_code == 201
            second_headers = {"Authorization": f"Bearer {second_grant.json()['access_token']}"}
            assert client.post(
                "/api/visitor/grants/revoke", json={"session_id": "visit-one"}
            ).status_code == 401
            revoked = client.post(
                "/api/visitor/grants/revoke", json={"session_id": "visit-one"},
                headers={"X-HistoryGuide-Api-Key": "business-key"},
            )
            assert revoked.status_code == 200
            assert revoked.json() == {"revoked_count": 1}
            assert client.get("/api/visitor/me", headers=visitor_headers).status_code == 401
            assert client.get("/api/visitor/me", headers=second_headers).status_code == 200
            own_revoke = client.post("/api/visitor/revoke", headers=second_headers)
            assert own_revoke.status_code == 200
            assert own_revoke.json() == {"revoked_count": 1}
            assert client.get("/api/visitor/me", headers=second_headers).status_code == 401
            actions = [row.action for row in db_session.query(AuditLog).all()]
            assert actions.count("visitor_grant_issued") == 2
            assert "visitor_grants_revoked" in actions
            assert "visitor_grant_self_revoked" in actions
            with Session(db_session.bind) as fresh_db:
                app.dependency_overrides[get_db] = lambda: fresh_db
                assert client.get("/api/visitor/me", headers=visitor_headers).status_code == 401
                assert client.get("/api/visitor/me", headers=second_headers).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_visitor_grant_and_revocation_roll_back_if_audit_fails(db_session, monkeypatch) -> None:
    from app.api.routes import visitor_gateway

    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="rollback-visit", visitor_type="tourist", current_exhibit=None,
            visited_history=[], interest=[], remaining_time=20,
        ),
    )
    monkeypatch.setattr(
        main_module, "settings",
        Settings(
            api_key="business-key", visitor_gateway_enabled=True,
            visitor_signing_key="separate-visitor-signing-key-0123456789",
        ),
    )
    app = main_module.create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    original_record_audit_log = visitor_gateway.record_audit_log

    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit write failure")

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            business_headers = {"X-HistoryGuide-Api-Key": "business-key"}
            monkeypatch.setattr(visitor_gateway, "record_audit_log", fail_audit)
            assert client.post(
                "/api/visitor/grants", json={"session_id": "rollback-visit"},
                headers=business_headers,
            ).status_code == 500
            assert db_session.query(VisitorAccessGrant).count() == 0

            monkeypatch.setattr(visitor_gateway, "record_audit_log", original_record_audit_log)
            grant = client.post(
                "/api/visitor/grants", json={"session_id": "rollback-visit"},
                headers=business_headers,
            )
            assert grant.status_code == 201
            visitor_headers = {"Authorization": f"Bearer {grant.json()['access_token']}"}

            monkeypatch.setattr(visitor_gateway, "record_audit_log", fail_audit)
            assert client.post(
                "/api/visitor/grants/revoke", json={"session_id": "rollback-visit"},
                headers=business_headers,
            ).status_code == 500
            assert client.get("/api/visitor/me", headers=visitor_headers).status_code == 200
            assert client.post("/api/visitor/revoke", headers=visitor_headers).status_code == 500
            assert client.get("/api/visitor/me", headers=visitor_headers).status_code == 200
    finally:
        app.dependency_overrides.clear()
