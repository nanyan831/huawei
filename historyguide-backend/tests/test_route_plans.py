from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


def seed_route_exhibits(db_session: Session) -> None:
    exhibits = [
        ExhibitCreate(
            id="route-current",
            name="Route Current",
            description="Already visited route fixture.",
            period="fixture-period",
            keywords=["current"],
            importance=3,
            people=[],
            time_range=None,
            themes=["route"],
            source_reference="Test fixture only.",
        ),
        ExhibitCreate(
            id="route-interest",
            name="Route Interest",
            description="Interest matching route fixture.",
            period="fixture-period",
            keywords=["architecture"],
            importance=3,
            people=[],
            time_range=None,
            themes=["route"],
            source_reference="Test fixture only.",
        ),
        ExhibitCreate(
            id="route-important",
            name="Route Important",
            description="High importance route fixture.",
            period="fixture-period",
            keywords=["legacy"],
            importance=5,
            people=[],
            time_range=None,
            themes=["route"],
            source_reference="Test fixture only.",
        ),
    ]
    for exhibit in exhibits:
        create_exhibit(db_session, exhibit)


def test_route_plan_uses_unvisited_exhibits_within_remaining_time(client, db_session: Session) -> None:
    seed_route_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="route-session-001",
            visitor_type="tourist",
            current_exhibit="route-current",
            visited_history=["route-current"],
            interest=["architecture"],
            remaining_time=17,
        ),
    )

    response = client.get("/api/visit-routes/route-session-001/plan")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "route-session-001"
    assert body["planned_minutes"] <= 17
    assert [item["exhibit_id"] for item in body["items"]] == ["route-interest", "route-important"]
    assert [item["order"] for item in body["items"]] == [1, 2]


def test_route_plan_returns_empty_when_no_time_remains(client, db_session: Session) -> None:
    seed_route_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="route-session-002",
            visitor_type="tourist",
            current_exhibit=None,
            visited_history=[],
            interest=["architecture"],
            remaining_time=0,
        ),
    )

    response = client.get("/api/visit-routes/route-session-002/plan")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["planned_minutes"] == 0


def test_route_plan_respects_max_items(client, db_session: Session) -> None:
    seed_route_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="route-session-003",
            visitor_type="tourist",
            current_exhibit=None,
            visited_history=[],
            interest=[],
            remaining_time=30,
        ),
    )

    response = client.get("/api/visit-routes/route-session-003/plan?max_items=1")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_route_plan_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/visit-routes/missing-session/plan")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."

