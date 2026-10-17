from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings
from app.database.session import get_db
from app.models.evidence import EvidenceSource
from app.services.evidence_service import approve_source, create_source
from app.schemas.approved_source_search import ApprovedSourceSearchRequest
from app.services.approved_source_search_service import search_approved_sources


def _source(db_session, source_id: str, text: str, *, approved: bool = True) -> None:
    create_source(
        db_session, source_id=source_id, title=f"Archive {source_id}",
        source_uri=f"museum:{source_id}", content_text=text,
    )
    if approved:
        approve_source(db_session, source_id, reviewer="museum-reviewer")


def test_search_only_returns_publishable_backend_excerpts(db_session, monkeypatch) -> None:
    text = "南开大学正式创办于1919年。"
    _source(db_session, "S01", text)
    _source(db_session, "draft-source", text, approved=False)
    _source(db_session, "fixture-source", text, approved=False)
    fixture = db_session.get(EvidenceSource, "fixture-source")
    fixture.status = "approved"
    fixture.reviewed_by = "legacy-record"
    fixture.reviewed_at = datetime.now(timezone.utc)
    _source(db_session, "stale-source", text)
    db_session.get(EvidenceSource, "stale-source").content_text += " Unreviewed edit."
    _source(db_session, "unreviewed-source", text, approved=False)
    db_session.get(EvidenceSource, "unreviewed-source").status = "approved"
    _source(db_session, "deep-source", "A" * 8000 + "南开大学创办")
    db_session.commit()

    monkeypatch.setattr(main_module, "settings", Settings(api_key="test-business-key"))
    app = main_module.create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as client:
            path = "/api/genios/sources/search"
            payload = {"keywords": ["南开大学"]}
            assert client.post(path, json=payload).status_code == 401
            headers = {"X-HistoryGuide-Api-Key": "test-business-key"}
            response = client.post(path, json=payload, headers=headers)
            assert response.status_code == 200
            assert response.headers["Cache-Control"] == "no-store"
            assert response.json()["retrieval_mode"] == "lexical"
            matches = response.json()["matches"]
            assert [match["source_id"] for match in matches] == ["S01"]
            assert matches[0]["excerpt_text"] == text
            assert len(matches[0]["content_sha256"]) == 64
            assert client.post(path, json={"keywords": ["1919%"]}, headers=headers).json()["matches"] == []
            assert client.post(path, json={"keywords": ["not-present"]}, headers=headers).json()["matches"] == []
            assert client.post(path, json={"keywords": ["南开大学创办"]}, headers=headers).json()["matches"] == []
            assert client.post(path, json={"keywords": ["南开大学", "南开大学"]}, headers=headers).status_code == 422
            assert client.post(path, json={"keywords": ["南"]}, headers=headers).status_code == 422

            schema = client.get("/openapi-genios-sources.json").json()
            operation = schema["paths"][path]["post"]
            assert operation["operationId"] == "search_historyguide_approved_sources"
            assert operation["security"] == [{"HistoryGuideApiKey": []}]
    finally:
        app.dependency_overrides.clear()


def test_search_does_not_lose_valid_source_behind_invalid_candidates(db_session) -> None:
    for index in range(51):
        source_id = f"a-invalid-{index:02d}"
        _source(db_session, source_id, "Target history source", approved=False)
        db_session.get(EvidenceSource, source_id).status = "approved"
    _source(db_session, "z-valid", "Target history source")
    db_session.commit()

    matches = search_approved_sources(
        db_session, ApprovedSourceSearchRequest(keywords=["Target history"], limit=1)
    )
    assert [match.source_id for match in matches] == ["z-valid"]
