from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState, VisitorVisitEventLog
from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


def seed_summary_exhibit(db_session: Session) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="summary-exhibit-001",
            name="Summary Exhibit",
            description="Non-historical summary fixture.",
            period="fixture-period",
            keywords=["summary"],
            importance=3,
            people=[],
            time_range=None,
            themes=["summary"],
            source_reference="Test fixture only.",
        ),
    )


def test_visit_summary_returns_structured_visit_context(client, db_session: Session) -> None:
    seed_summary_exhibit(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="summary-session-001",
            visitor_type="tourist",
            current_exhibit="summary-exhibit-001",
            visited_history=["summary-exhibit-001"],
            interest=["summary"],
            remaining_time=12,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="summary-session-001",
            exhibit_id="summary-exhibit-001",
            remaining_time=12,
        )
    )
    db_session.commit()

    response = client.get("/api/visits/summary-session-001/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "summary-session-001"
    assert body["visited_count"] == 1
    assert body["visited_exhibits"][0]["id"] == "summary-exhibit-001"
    assert body["visit_events"][0]["exhibit_id"] == "summary-exhibit-001"
    assert body["visit_events"][0]["remaining_time"] == 12
    assert body["interests"] == ["summary"]
    assert body["remaining_time"] == 12
    assert "generate a grounded visit recap" in body["genios_next_step"]


def test_visit_summary_reports_missing_visited_exhibits(client, db_session: Session) -> None:
    db_session.add(
        VisitorState(
            session_id="summary-session-002",
            visitor_type="freshman",
            current_exhibit=None,
            visited_history=["missing-visited"],
            interest=[],
            remaining_time=5,
        )
    )
    db_session.commit()

    response = client.get("/api/visits/summary-session-002/summary")

    assert response.status_code == 200
    assert response.json()["visited_count"] == 0
    assert response.json()["missing_exhibit_ids"] == ["missing-visited"]


def test_visit_summary_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/visits/missing-session/summary")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."
