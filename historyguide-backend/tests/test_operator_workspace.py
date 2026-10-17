import asyncio
import json

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.evidence_body_limit import EvidenceBodyLimitMiddleware
from app.core.security import API_KEY_HEADER, OPERATOR_API_KEY_HEADER
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceSource, ExhibitApproval
from app.models.exhibit import Exhibit


HEADERS = {OPERATOR_API_KEY_HEADER: "operator-test"}
SOURCE = {
    "id": "S01", "title": "Archive excerpt", "source_uri": "museum-archive:record-1",
    "content_text": "Original text checked against the archive by a human reviewer.",
}
EXHIBIT = {
    "id": "museum-001", "name": "Museum record", "description": "Description to be reviewed.",
    "period": "Reviewed period", "importance": 3, "source_reference": "museum-archive:record-1",
}


@pytest.fixture()
def operator_client(client, monkeypatch):
    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    return client


def test_workspace_shell_is_public_but_evidence_requires_operator_key(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setattr(main, "settings", Settings(api_key="business-test", operator_api_key="operator-test"))
    client = TestClient(main.create_app())
    for path, content_type in (
        ("/operator", "text/html"), ("/operator/app.js", "text/javascript"),
        ("/operator/styles.css", "text/css"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(content_type)
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert "business-test" not in response.text
        assert "operator-test" not in response.text

    for path in ("/api/evidence/exhibits", "/api/evidence/sources"):
        response = client.get(path, headers={API_KEY_HEADER: "business-test"})
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/evidence/sources", headers={OPERATOR_API_KEY_HEADER: b"\xff"}).status_code == 401
    assert client.get("/api/exhibits", headers={API_KEY_HEADER: b"\xff"}).status_code == 401
    assert client.get("/operator/not-an-asset").status_code == 401


@pytest.mark.parametrize("kind", ["sources", "exhibits"])
def test_preview_and_import_fail_closed_without_operator_configuration(client, kind):
    payload = {kind: [SOURCE if kind == "sources" else EXHIBIT]}
    assert client.post(f"/api/evidence/{kind}/batch/preview", json=payload).status_code == 503
    assert client.post(f"/api/evidence/{kind}/batch", json=payload).status_code == 503


@pytest.mark.parametrize("headers", [{}, {API_KEY_HEADER: "business-test"}])
@pytest.mark.parametrize("kind", ["sources", "exhibits"])
@pytest.mark.parametrize("operation", ["list", "preview"])
def test_business_key_only_reports_missing_operator_configuration(monkeypatch, headers, kind, operation):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setattr(main, "settings", Settings(api_key="business-test"))
    with TestClient(main.create_app()) as client:
        if operation == "list":
            response = client.get(f"/api/evidence/{kind}", headers=headers)
        else:
            payload = {kind: [SOURCE if kind == "sources" else EXHIBIT]}
            response = client.post(f"/api/evidence/{kind}/batch/preview", json=payload, headers=headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Evidence operations require a configured operator API key."}
    assert response.headers["cache-control"] == "no-store"


def test_configured_operator_key_remains_required_when_business_key_is_configured(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setattr(main, "settings", Settings(api_key="business-test", operator_api_key="operator-test"))
    with TestClient(main.create_app()) as client:
        for kind in ("sources", "exhibits"):
            payload = {kind: [SOURCE if kind == "sources" else EXHIBIT]}
            for headers in ({}, {API_KEY_HEADER: "business-test"}):
                assert client.get(f"/api/evidence/{kind}", headers=headers).status_code == 401
                assert client.post(
                    f"/api/evidence/{kind}/batch/preview", json=payload, headers=headers,
                ).status_code == 401
            assert client.get(f"/api/evidence/{kind}", headers=HEADERS).status_code == 200
            assert client.post(
                f"/api/evidence/{kind}/batch/preview", json=payload, headers=HEADERS,
            ).status_code == 200


def test_source_preview_is_read_only_and_import_rechecks_conflicts(operator_client, db_session):
    payload = {"sources": [SOURCE]}
    preview = operator_client.post("/api/evidence/sources/batch/preview", json=payload, headers=HEADERS)
    assert preview.status_code == 200
    assert preview.json()["items"][0]["content_length"] == len(SOURCE["content_text"])
    assert "content_text" not in preview.json()["items"][0]
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0
    assert operator_client.post("/api/evidence/sources/batch", json=payload, headers=HEADERS).status_code == 201
    assert operator_client.post("/api/evidence/sources/batch", json=payload, headers=HEADERS).status_code == 409
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 1


def test_exhibit_intake_and_governance_cycle(operator_client, db_session):
    payload = {"exhibits": [EXHIBIT]}
    preview = operator_client.post("/api/evidence/exhibits/batch/preview", json=payload, headers=HEADERS)
    assert preview.status_code == 200
    assert db_session.scalar(select(func.count()).select_from(Exhibit)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0

    imported = operator_client.post("/api/evidence/exhibits/batch", json=payload, headers=HEADERS)
    assert imported.status_code == 201
    assert imported.json()["count"] == 1
    assert db_session.get(ExhibitApproval, EXHIBIT["id"]) is None
    page = operator_client.get("/api/evidence/exhibits?limit=1", headers=HEADERS).json()
    assert page["total"] == 1
    assert page["items"][0]["approval"] is None
    assert page["items"][0]["approval_issue"]
    assert operator_client.get("/api/evidence/exhibits/missing", headers=HEADERS).status_code == 404

    reviewer = {"reviewer": " museum-reviewer "}
    exhibit_path = f"/api/evidence/exhibits/{EXHIBIT['id']}"
    assert operator_client.post(exhibit_path + "/approve", json=reviewer, headers=HEADERS).status_code == 409
    assert operator_client.post("/api/evidence/sources", json=SOURCE, headers=HEADERS).status_code == 201
    assert operator_client.post("/api/evidence/sources/S01/approve", json=reviewer, headers=HEADERS).status_code == 200
    assert operator_client.post(exhibit_path + "/sources/S01", headers=HEADERS).status_code == 200
    approved = operator_client.post(exhibit_path + "/approve", json=reviewer, headers=HEADERS)
    assert approved.status_code == 200
    assert approved.json()["reviewed_by"] == "museum-reviewer"
    detail = operator_client.get(exhibit_path, headers=HEADERS).json()
    assert detail["source_ids"] == ["S01"]
    assert detail["approval_issue"] is None

    assert operator_client.post("/api/evidence/sources/S01/revoke", json=reviewer, headers=HEADERS).status_code == 200
    assert "revoked evidence" in operator_client.get(exhibit_path, headers=HEADERS).json()["approval_issue"]
    assert operator_client.post(exhibit_path + "/revoke", json=reviewer, headers=HEADERS).status_code == 200
    assert operator_client.get(exhibit_path, headers=HEADERS).json()["approval"]["status"] == "revoked"
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert {"exhibits_imported", "evidence_source_approved", "evidence_source_revoked",
            "exhibit_evidence_linked", "exhibit_approved", "exhibit_approval_revoked"} <= actions


def test_single_exhibit_upload_links_existing_sources_atomically(operator_client, db_session):
    assert operator_client.post("/api/evidence/sources", json=SOURCE, headers=HEADERS).status_code == 201

    response = operator_client.post(
        "/api/evidence/exhibits",
        json={"exhibit": EXHIBIT, "source_ids": ["S01"]},
        headers=HEADERS,
    )

    assert response.status_code == 201
    assert response.json()["source_ids"] == ["S01"]
    assert response.json()["approval"] is None
    assert response.json()["approval_issue"]
    log = db_session.scalar(select(AuditLog).where(AuditLog.action == "exhibit_uploaded"))
    assert log.resource_id == EXHIBIT["id"]
    assert log.details == {"source_ids": ["S01"], "status": "draft"}


def test_single_exhibit_upload_missing_source_writes_nothing(operator_client, db_session):
    response = operator_client.post(
        "/api/evidence/exhibits",
        json={"exhibit": EXHIBIT, "source_ids": ["missing-source"]},
        headers=HEADERS,
    )

    assert response.status_code == 404
    assert db_session.get(Exhibit, EXHIBIT["id"]) is None
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_single_exhibit_upload_rolls_back_if_audit_fails(
    operator_client, db_session, monkeypatch,
):
    from app.services import exhibit_import_service

    assert operator_client.post("/api/evidence/sources", json=SOURCE, headers=HEADERS).status_code == 201
    audit_count = db_session.scalar(select(func.count()).select_from(AuditLog))

    def fail_audit(*args, **kwargs):
        raise RuntimeError("injected upload audit failure")

    monkeypatch.setattr(exhibit_import_service, "record_audit_log", fail_audit)
    with pytest.raises(RuntimeError, match="injected upload audit failure"):
        operator_client.post(
            "/api/evidence/exhibits",
            json={"exhibit": EXHIBIT, "source_ids": ["S01"]},
            headers=HEADERS,
        )
    db_session.commit()
    assert db_session.get(Exhibit, EXHIBIT["id"]) is None
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == audit_count


def test_exhibit_import_rejects_duplicate_ids_atomically(operator_client, db_session):
    for records in ([EXHIBIT, EXHIBIT],):
        response = operator_client.post("/api/evidence/exhibits/batch", json={"exhibits": records}, headers=HEADERS)
        assert response.status_code == 409
        assert db_session.scalar(select(func.count()).select_from(Exhibit)) == 0
        assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0
    assert operator_client.post("/api/evidence/exhibits/batch", json={"exhibits": [EXHIBIT]}, headers=HEADERS).status_code == 201
    response = operator_client.post(
        "/api/evidence/exhibits/batch",
        json={"exhibits": [{**EXHIBIT, "id": "museum-002"}, EXHIBIT]}, headers=HEADERS,
    )
    assert response.status_code == 409
    assert db_session.get(Exhibit, "museum-002") is None
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 1


@pytest.mark.parametrize("kind,record,model", [("sources", SOURCE, EvidenceSource), ("exhibits", EXHIBIT, Exhibit)])
def test_import_rolls_back_records_if_audit_insert_fails(operator_client, db_session, kind, record, model):
    def fail_audit(mapper, connection, target):
        raise IntegrityError("injected audit insert failure", {}, Exception("failed"))

    event.listen(AuditLog, "before_insert", fail_audit)
    try:
        response = operator_client.post(f"/api/evidence/{kind}/batch", json={kind: [record]}, headers=HEADERS)
    finally:
        event.remove(AuditLog, "before_insert", fail_audit)
    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(model)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0
    assert operator_client.post(f"/api/evidence/{kind}/batch", json={kind: [record]}, headers=HEADERS).status_code == 201


@pytest.mark.parametrize("kind,record,model", [("sources", SOURCE, EvidenceSource), ("exhibits", EXHIBIT, Exhibit)])
def test_import_rolls_back_pending_records_if_audit_creation_raises(
    operator_client, db_session, monkeypatch, kind, record, model,
):
    from app.services import evidence_service, exhibit_import_service

    service = evidence_service if kind == "sources" else exhibit_import_service

    def fail_audit(*args, **kwargs):
        raise RuntimeError("injected audit creation failure")

    monkeypatch.setattr(service, "record_audit_log", fail_audit)
    with pytest.raises(RuntimeError, match="injected audit creation failure"):
        operator_client.post(f"/api/evidence/{kind}/batch", json={kind: [record]}, headers=HEADERS)
    # A later commit on this session must not silently import unaudited records.
    db_session.commit()
    assert db_session.scalar(select(func.count()).select_from(model)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0


@pytest.mark.parametrize("kind", ["sources", "exhibits"])
@pytest.mark.parametrize("suffix", ["/preview", ""])
def test_intake_rejects_missing_wrong_and_business_keys(operator_client, db_session, kind, suffix):
    payload = {kind: [SOURCE if kind == "sources" else EXHIBIT]}
    for headers in ({}, {OPERATOR_API_KEY_HEADER: "wrong"}, {API_KEY_HEADER: "operator-test"}):
        response = operator_client.post(f"/api/evidence/{kind}/batch{suffix}", json=payload, headers=headers)
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 0
    assert db_session.scalar(select(func.count()).select_from(Exhibit)) == 0
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0


@pytest.mark.parametrize("kind,record", [
    ("sources", {**SOURCE, "id": "S01/unsafe"}),
    ("sources", {**SOURCE, "content_text": " \n "}),
    ("sources", {**SOURCE, "title": " "}),
    ("sources", {**SOURCE, "status": "approved"}),
    ("exhibits", {**EXHIBIT, "id": "[museum-001]"}),
    ("exhibits", {**EXHIBIT, "source_reference": " "}),
    ("exhibits", {**EXHIBIT, "name": "x" * 201}),
    ("exhibits", {**EXHIBIT, "themes": [" " ]}),
    ("exhibits", {**EXHIBIT, "status": "approved"}),
])
def test_invalid_uploads_write_nothing(operator_client, db_session, kind, record):
    for suffix in ("/preview", ""):
        response = operator_client.post(f"/api/evidence/{kind}/batch{suffix}", json={kind: [record]}, headers=HEADERS)
        assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_blank_reviewer_and_fixture_exhibit_cannot_be_approved(operator_client, db_session):
    payload = {"exhibits": [{**EXHIBIT, "id": "fixture-example"}]}
    assert operator_client.post("/api/evidence/exhibits/batch", json=payload, headers=HEADERS).status_code == 201
    path = "/api/evidence/exhibits/fixture-example/approve"
    assert operator_client.post(path, json={"reviewer": " "}, headers=HEADERS).status_code == 422
    assert operator_client.post(path, json={"reviewer": "curator"}, headers=HEADERS).status_code == 409
    assert db_session.get(ExhibitApproval, "fixture-example") is None


def test_reviewer_length_matches_audit_actor_capacity(operator_client, db_session):
    assert operator_client.post("/api/evidence/sources", json=SOURCE, headers=HEADERS).status_code == 201
    path = "/api/evidence/sources/S01"
    response = operator_client.post(path + "/approve", json={"reviewer": "r" * 80}, headers=HEADERS)
    assert response.status_code == 200
    approved_log = db_session.scalar(select(AuditLog).where(AuditLog.action == "evidence_source_approved"))
    assert approved_log.actor == "r" * 80
    audit_count = db_session.scalar(select(func.count()).select_from(AuditLog))
    response = operator_client.post(path + "/revoke", json={"reviewer": "r" * 81}, headers=HEADERS)
    assert response.status_code == 422
    assert db_session.get(EvidenceSource, "S01").status == "approved"
    assert db_session.scalar(select(func.count()).select_from(AuditLog)) == audit_count


@pytest.mark.parametrize("chunks", [[b"x" * 33], [b"x" * 16, b"x" * 17]])
def test_body_limit_rejects_oversized_and_chunked_uploads(chunks):
    messages = []
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True

    pending = iter(chunks)

    async def receive():
        chunk = next(pending)
        return {"type": "http.request", "body": chunk, "more_body": True}

    async def send(message):
        messages.append(message)

    middleware = EvidenceBodyLimitMiddleware(downstream, max_bytes=32)
    asyncio.run(middleware({"type": "http", "method": "POST", "path": "/api/evidence/sources/batch"}, receive, send))
    assert downstream_called is False
    assert messages[0]["status"] == 413
    assert "limit" in json.loads(messages[1]["body"])["detail"]
