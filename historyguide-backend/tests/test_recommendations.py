from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


def seed_recommendation_exhibits(db_session: Session) -> None:
    exhibits = [
        ExhibitCreate(
            id="visited-exhibit",
            name="Visited Exhibit",
            description="Already visited orientation exhibit.",
            period="test-period",
            keywords=["orientation"],
            importance=5,
            people=[],
            time_range=None,
            themes=["freshman"],
            source_reference="Test fixture only.",
        ),
        ExhibitCreate(
            id="interest-match",
            name="Interest Match Exhibit",
            description="A context exhibit about architecture and culture.",
            period="test-period",
            keywords=["architecture", "context"],
            importance=3,
            people=[],
            time_range=None,
            themes=["culture"],
            source_reference="Test fixture only.",
        ),
        ExhibitCreate(
            id="high-importance",
            name="High Importance Exhibit",
            description="A major exhibit without the visitor interest term.",
            period="other-period",
            keywords=["legacy"],
            importance=5,
            people=[],
            time_range=None,
            themes=["memory"],
            source_reference="Test fixture only.",
        ),
    ]
    for exhibit in exhibits:
        create_exhibit(db_session, exhibit)


def test_recommendations_prioritize_interest_and_skip_visited(client, db_session: Session) -> None:
    seed_recommendation_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="recommend-session-001",
            visitor_type="tourist",
            current_exhibit=None,
            visited_history=["visited-exhibit"],
            interest=["architecture"],
            remaining_time=30,
        ),
    )

    response = client.get("/api/recommendations/recommend-session-001")

    assert response.status_code == 200
    body = response.json()
    assert [item["exhibit_id"] for item in body] == ["interest-match", "high-importance"]
    assert body[0]["priority"] == 1
    assert "matches interests: architecture" in body[0]["reason"]
    assert "visited-exhibit" not in [item["exhibit_id"] for item in body]


def test_recommendations_respect_limit(client, db_session: Session) -> None:
    seed_recommendation_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="recommend-session-002",
            visitor_type="alumnus",
            current_exhibit=None,
            visited_history=[],
            interest=[],
            remaining_time=10,
        ),
    )

    response = client.get("/api/recommendations/recommend-session-002?limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["priority"] == 1


def test_recommendations_return_empty_when_all_exhibits_visited(client, db_session: Session) -> None:
    seed_recommendation_exhibits(db_session)
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="recommend-session-003",
            visitor_type="freshman",
            current_exhibit=None,
            visited_history=["visited-exhibit", "interest-match", "high-importance"],
            interest=["architecture"],
            remaining_time=20,
        ),
    )

    response = client.get("/api/recommendations/recommend-session-003")

    assert response.status_code == 200
    assert response.json() == []


def test_recommendations_return_404_for_missing_session(client) -> None:
    response = client.get("/api/recommendations/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."

