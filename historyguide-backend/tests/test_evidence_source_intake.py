from sqlalchemy import func, select

from app.core.config import Settings
from app.core.security import OPERATOR_API_KEY_HEADER
from app.models.evidence import EvidenceSource


HEADERS = {OPERATOR_API_KEY_HEADER: "operator-test"}
SOURCES = [
    {
        "id": "S01",
        "title": "University archive",
        "source_uri": "https://example.edu/history",
        "content_text": "The source excerpt must be checked by museum staff.",
    },
    {
        "id": "S02",
        "title": "Museum record",
        "source_uri": "museum-archive:record-2",
        "content_text": "Another original excerpt for staff review.",
    },
]


def test_source_intake_requires_operator_key(client, monkeypatch) -> None:
    monkeypatch.setattr(client.app.state, "settings", Settings())
    assert client.get("/api/evidence/sources").status_code == 503
    assert client.post("/api/evidence/sources/batch", json={"sources": SOURCES}).status_code == 503

    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    assert client.get("/api/evidence/sources").status_code == 401
    assert client.get("/api/evidence/sources/S01").status_code == 401
    assert client.post("/api/evidence/sources/batch", json={"sources": SOURCES}).status_code == 401


def test_batch_import_is_draft_and_reviewable(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    response = client.post("/api/evidence/sources/batch", json={"sources": SOURCES}, headers=HEADERS)
    assert response.status_code == 201
    assert response.json()["imported_count"] == 2
    assert all(item["status"] == "draft" for item in response.json()["items"])
    assert "content_text" not in response.json()["items"][0]

    page = client.get("/api/evidence/sources?status=draft&limit=1", headers=HEADERS)
    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert len(page.json()["items"]) == 1
    assert page.json()["items"][0]["id"] == "S01"
    assert "content_text" not in page.json()["items"][0]
    assert client.get("/api/evidence/sources?status=approved", headers=HEADERS).json()["total"] == 0

    detail = client.get("/api/evidence/sources/S01", headers=HEADERS)
    assert detail.status_code == 200
    assert detail.json()["content_text"] == SOURCES[0]["content_text"]
    assert detail.json()["status"] == "draft"
    assert client.get("/api/evidence/sources/missing", headers=HEADERS).status_code == 404

    prepare = client.post(
        "/api/genios/history-runs",
        json={"question": "When?", "source_ids": ["S01"]},
    )
    assert prepare.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 2


def test_batch_import_is_atomic_on_duplicate_ids(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    duplicated = [SOURCES[0], {**SOURCES[1], "id": "S01"}]
    response = client.post("/api/evidence/sources/batch", json={"sources": duplicated}, headers=HEADERS)
    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 0

    assert client.post(
        "/api/evidence/sources", json=SOURCES[0], headers=HEADERS
    ).status_code == 201
    response = client.post("/api/evidence/sources/batch", json={"sources": SOURCES}, headers=HEADERS)
    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(EvidenceSource)) == 1
    assert db_session.get(EvidenceSource, "S02") is None
