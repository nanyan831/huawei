from datetime import datetime, timezone

import pytest

from app.models.evidence import EvidenceSource
from app.core.config import Settings
from app.core.security import OPERATOR_API_KEY_HEADER
from app.models.exhibit import Exhibit
from app.models.visitor_state import VisitorVisitEventLog
from app.schemas.visitor_state import VisitorStateCreate
from app.services.evidence_service import (
    approve_exhibit,
    approve_source,
    create_source,
    link_source,
    revoke_source,
    exhibit_approval_issue,
)
from app.services.visitor_state_service import create_visitor_state


def _seed_exhibit(db_session, exhibit_id: str = "evidence-exhibit") -> Exhibit:
    exhibit = Exhibit(
        id=exhibit_id,
        name="Reviewed exhibit",
        description="A historical exhibit.",
        period="1919",
        keywords=["history"],
        importance=3,
        people=[],
        time_range=None,
        themes=[],
        source_reference="Museum archive source S01.",
    )
    db_session.add(exhibit)
    db_session.commit()
    return exhibit


def _seed_session(db_session, exhibit_id: str = "evidence-exhibit") -> None:
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="evidence-session",
            visitor_type="tourist",
            current_exhibit=exhibit_id,
            visited_history=[exhibit_id],
            interest=["history"],
            remaining_time=20,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="evidence-session",
            exhibit_id=exhibit_id,
            remaining_time=20,
        )
    )
    db_session.commit()


def _review(client, exhibit_id: str = "evidence-exhibit") -> dict:
    response = client.post(
        "/api/genios/review",
        json={
            "session_id": "evidence-session",
            "draft_answer": "A source-backed explanation.",
            "cited_exhibit_ids": exhibit_id,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_unapproved_exhibit_blocks_review(client, db_session) -> None:
    _seed_exhibit(db_session)
    _seed_session(db_session)

    result = _review(client)

    assert result["decision"] == "block"
    assert result["ready_for_generation"] is False
    assert result["source_references_valid"] is False
    assert "no current museum approval" in result["issues"]


def test_review_requires_approved_linked_source(client, db_session, monkeypatch) -> None:
    _seed_exhibit(db_session)
    _seed_session(db_session)
    create_source(
        db_session,
        source_id="S01",
        title="Archive record",
        source_uri="museum-archive:S01",
        content_text="Museum-confirmed text.",
    )
    link_source(db_session, "evidence-exhibit", "S01")

    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    response = client.post(
        "/api/evidence/exhibits/evidence-exhibit/approve",
        json={"reviewer": "museum-reviewer"},
        headers={OPERATOR_API_KEY_HEADER: "operator-test"},
    )
    assert response.status_code == 409
    assert "approved evidence source" in response.json()["detail"]

    approve_source(db_session, "S01", reviewer="museum-reviewer")
    approve_exhibit(db_session, "evidence-exhibit", reviewer="museum-reviewer")
    assert _review(client)["decision"] == "pass"


def test_revoked_source_blocks_previously_approved_exhibit(client, db_session) -> None:
    exhibit = _seed_exhibit(db_session)
    _seed_session(db_session)
    create_source(
        db_session,
        source_id="S01",
        title="Archive record",
        source_uri="museum-archive:S01",
        content_text="Museum-confirmed text.",
    )
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, "S01")
    approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")
    assert _review(client)["decision"] == "pass"

    revoke_source(db_session, "S01", reviewer="museum-reviewer")
    result = _review(client)
    assert result["decision"] == "block"
    assert "revoked evidence" in result["issues"]


def test_exhibit_change_invalidates_approval(client, db_session) -> None:
    exhibit = _seed_exhibit(db_session)
    _seed_session(db_session)
    source = create_source(
        db_session,
        source_id="S01",
        title="Archive record",
        source_uri="museum-archive:S01",
        content_text="Museum-confirmed text.",
    )
    assert db_session.get(EvidenceSource, source.id).content_sha256 == source.content_sha256
    approve_source(db_session, source.id, reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, source.id)
    approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")
    assert _review(client)["decision"] == "pass"

    exhibit.description = "Changed after approval."
    db_session.commit()
    result = _review(client)
    assert result["decision"] == "block"
    assert "changed after approval" in result["issues"]


def test_source_content_change_invalidates_approval(client, db_session) -> None:
    exhibit = _seed_exhibit(db_session)
    _seed_session(db_session)
    source = create_source(
        db_session,
        source_id="S01",
        title="Archive record",
        source_uri="museum-archive:S01",
        content_text="Museum-confirmed text.",
    )
    approve_source(db_session, source.id, reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, source.id)
    approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")
    assert _review(client)["decision"] == "pass"

    source.content_text = "Changed without updating the stored hash."
    db_session.commit()
    result = _review(client)
    assert result["decision"] == "block"
    assert "evidence content changed" in result["issues"]


@pytest.mark.parametrize("field,new_value", [
    ("title", "An unreviewed title"),
    ("source_uri", "museum-archive:unreviewed-record"),
])
def test_source_metadata_change_invalidates_approval(client, db_session, field, new_value) -> None:
    exhibit = _seed_exhibit(db_session)
    _seed_session(db_session)
    source = create_source(
        db_session, source_id="S01", title="Archive record",
        source_uri="museum-archive:S01", content_text="Museum-confirmed text.",
    )
    approve_source(db_session, source.id, reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, source.id)
    approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")
    assert _review(client)["decision"] == "pass"

    setattr(source, field, new_value)
    db_session.commit()
    result = _review(client)
    assert result["decision"] == "block"
    assert "evidence metadata changed after approval" in result["issues"]


def test_fixture_cannot_be_approved(client, db_session) -> None:
    _seed_exhibit(db_session, exhibit_id="fixture-exhibit")
    from app.services.evidence_service import approve_exhibit

    try:
        approve_exhibit(db_session, "fixture-exhibit", reviewer="museum-reviewer")
        assert False, "Fixture approval must fail."
    except ValueError as exc:
        assert "Development fixtures" in str(exc)


def test_fixture_source_cannot_back_an_approved_exhibit(db_session) -> None:
    exhibit = _seed_exhibit(db_session)
    source = create_source(
        db_session, source_id="fixture-archive", title="Development fixture",
        source_uri="fixture:archive", content_text="Synthetic test text.",
    )
    with pytest.raises(ValueError, match="fixture evidence"):
        approve_source(db_session, source.id, reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, source.id)
    source.status = "approved"
    source.reviewed_by = "legacy-record"
    source.reviewed_at = datetime.now(timezone.utc)
    db_session.commit()
    with pytest.raises(ValueError, match="approved evidence source"):
        approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")


def test_legacy_fixture_link_invalidates_existing_exhibit_approval(db_session) -> None:
    exhibit = _seed_exhibit(db_session)
    create_source(
        db_session, source_id="S01", title="Reviewed archive",
        source_uri="museum:S01", content_text="Reviewed archive excerpt.",
    )
    approve_source(db_session, "S01", reviewer="museum-reviewer")
    link_source(db_session, exhibit.id, "S01")
    approve_exhibit(db_session, exhibit.id, reviewer="museum-reviewer")
    assert exhibit_approval_issue(db_session, exhibit) is None

    create_source(
        db_session, source_id="fixture-old", title="Synthetic fixture",
        source_uri="fixture:old", content_text="Synthetic test content.",
    )
    fixture = db_session.get(EvidenceSource, "fixture-old")
    fixture.status = "approved"
    fixture.reviewed_by = "legacy-record"
    fixture.reviewed_at = datetime.now(timezone.utc)
    db_session.commit()
    link_source(db_session, exhibit.id, fixture.id)
    assert "development fixture evidence" in exhibit_approval_issue(db_session, exhibit)


def test_evidence_api_requires_operator_key(client, monkeypatch) -> None:
    payload = {
        "id": "S01",
        "title": "Archive record",
        "source_uri": "museum-archive:S01",
        "content_text": "Evidence text.",
    }
    assert client.post("/api/evidence/sources", json=payload).status_code == 503

    monkeypatch.setattr(client.app.state, "settings", Settings(operator_api_key="operator-test"))
    assert client.post("/api/evidence/sources", json=payload).status_code == 401
    response = client.post(
        "/api/evidence/sources",
        json=payload,
        headers={OPERATOR_API_KEY_HEADER: "operator-test"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "draft"
