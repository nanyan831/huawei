from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorVisitEventLog
from app.schemas.exhibit import ExhibitCreate
from app.services.exhibit_service import create_exhibit


def seed_exhibit(db_session: Session, exhibit_id: str = "test-exhibit-001") -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id=exhibit_id,
            name="Visitor State Test Exhibit",
            description="A verified test exhibit for visitor state references.",
            period="test-period",
            keywords=["visitor"],
            importance=3,
            people=[],
            time_range=None,
            themes=["state"],
            source_reference="Test fixture only.",
        ),
    )


def test_create_visitor_state(client, db_session: Session) -> None:
    seed_exhibit(db_session)

    response = client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-001",
            "visitor_type": "freshman",
            "current_exhibit": "test-exhibit-001",
            "visited_history": ["test-exhibit-001"],
            "interest": ["校训", "人物"],
            "remaining_time": 30,
        },
    )

    assert response.status_code == 201
    assert response.json()["session_id"] == "session-001"
    assert response.json()["visitor_type"] == "freshman"
    assert response.json()["current_exhibit"] == "test-exhibit-001"


def test_read_visitor_state(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-002",
            "visitor_type": "tourist",
            "current_exhibit": "test-exhibit-001",
            "visited_history": [],
            "interest": ["建筑"],
            "remaining_time": 20,
        },
    )

    response = client.get("/api/visitor-states/session-002")

    assert response.status_code == 200
    assert response.json()["interest"] == ["建筑"]
    assert response.json()["remaining_time"] == 20


def test_list_visitor_states_supports_type_filter_and_pagination(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    for session_id, visitor_type in [
        ("session-list-001", "tourist"),
        ("session-list-002", "freshman"),
        ("session-list-003", "tourist"),
    ]:
        client.post(
            "/api/visitor-states",
            json={
                "session_id": session_id,
                "visitor_type": visitor_type,
                "current_exhibit": None,
                "visited_history": [],
                "interest": [],
                "remaining_time": 20,
            },
        )

    response = client.get("/api/visitor-states?visitor_type=tourist&limit=1&offset=1")

    assert response.status_code == 200
    assert [item["session_id"] for item in response.json()] == ["session-list-003"]


def test_get_visitor_state_stats_returns_structured_counts(client, db_session: Session) -> None:
    seed_exhibit(db_session, "stats-exhibit-001")
    for payload in [
        {
            "session_id": "session-stats-001",
            "visitor_type": "tourist",
            "current_exhibit": "stats-exhibit-001",
            "visited_history": ["stats-exhibit-001"],
            "interest": ["architecture", "memory"],
            "remaining_time": 20,
        },
        {
            "session_id": "session-stats-002",
            "visitor_type": "freshman",
            "current_exhibit": None,
            "visited_history": [],
            "interest": ["architecture"],
            "remaining_time": 30,
        },
    ]:
        client.post("/api/visitor-states", json=payload)

    response = client.get("/api/visitor-states/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 2
    assert body["visitor_types"] == [
        {"value": "freshman", "count": 1},
        {"value": "tourist", "count": 1},
    ]
    assert body["current_exhibits"] == [{"value": "stats-exhibit-001", "count": 1}]
    assert body["interests"][0] == {"value": "architecture", "count": 2}
    assert {"value": "memory", "count": 1} in body["interests"]
    assert body["no_current_exhibit_count"] == 1
    assert body["remaining_time"] == {"min": 20, "max": 30, "average": 25.0}


def test_get_visitor_state_integrity_report_returns_no_issues_for_consistent_event_state(
    client,
    db_session: Session,
) -> None:
    seed_exhibit(db_session, "integrity-exhibit-001")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-integrity-ok",
            "visitor_type": "tourist",
            "current_exhibit": None,
            "visited_history": [],
            "interest": [],
            "remaining_time": 20,
        },
    )
    client.post(
        "/api/visitor-states/session-integrity-ok/visit-events",
        json={"exhibit_id": "integrity-exhibit-001", "remaining_time": 18},
    )

    response = client.get("/api/visitor-states/integrity-report")

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 1
    assert body["total_visit_events"] == 1
    assert body["sessions_with_visit_events"] == 1
    assert body["issue_count"] == 0
    assert body["issues"] == []


def test_get_visitor_state_integrity_report_flags_snapshot_timeline_drift(
    client,
    db_session: Session,
) -> None:
    seed_exhibit(db_session, "integrity-exhibit-001")
    seed_exhibit(db_session, "integrity-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-integrity-drift",
            "visitor_type": "tourist",
            "current_exhibit": "integrity-exhibit-001",
            "visited_history": ["integrity-exhibit-001"],
            "interest": [],
            "remaining_time": 20,
        },
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="session-integrity-drift",
            exhibit_id="integrity-exhibit-002",
            remaining_time=18,
        )
    )
    db_session.commit()

    response = client.get("/api/visitor-states/integrity-report")

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 1
    assert body["total_visit_events"] == 1
    assert body["sessions_with_visit_events"] == 1
    issues = {item["issue"]: item for item in body["issues"]}
    assert issues["latest_event_not_current_exhibit"]["session_id"] == "session-integrity-drift"
    assert issues["latest_event_not_current_exhibit"]["exhibit_ids"] == ["integrity-exhibit-002"]
    assert issues["visit_events_missing_from_visited_history"]["exhibit_ids"] == ["integrity-exhibit-002"]


def test_get_single_visitor_state_integrity_report_scopes_to_session(
    client,
    db_session: Session,
) -> None:
    seed_exhibit(db_session, "integrity-exhibit-001")
    seed_exhibit(db_session, "integrity-exhibit-002")
    for session_id in ["session-integrity-scoped-ok", "session-integrity-scoped-drift"]:
        client.post(
            "/api/visitor-states",
            json={
                "session_id": session_id,
                "visitor_type": "tourist",
                "current_exhibit": "integrity-exhibit-001",
                "visited_history": ["integrity-exhibit-001"],
                "interest": [],
                "remaining_time": 20,
            },
        )
    db_session.add(
        VisitorVisitEventLog(
            session_id="session-integrity-scoped-ok",
            exhibit_id="integrity-exhibit-001",
            remaining_time=18,
        )
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="session-integrity-scoped-drift",
            exhibit_id="integrity-exhibit-002",
            remaining_time=17,
        )
    )
    db_session.commit()

    response = client.get("/api/visitor-states/session-integrity-scoped-ok/integrity")

    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 1
    assert body["total_visit_events"] == 1
    assert body["sessions_with_visit_events"] == 1
    assert body["issue_count"] == 0
    assert body["issues"] == []


def test_get_single_visitor_state_integrity_report_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/visitor-states/missing-session/integrity")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_update_visitor_state(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-003",
            "visitor_type": "alumnus",
            "current_exhibit": None,
            "visited_history": [],
            "interest": [],
            "remaining_time": 45,
        },
    )

    response = client.patch(
        "/api/visitor-states/session-003",
        json={
            "current_exhibit": "test-exhibit-001",
            "visited_history": ["test-exhibit-001"],
            "interest": ["院系记忆"],
            "remaining_time": 35,
        },
    )

    assert response.status_code == 200
    assert response.json()["current_exhibit"] == "test-exhibit-001"
    assert response.json()["visited_history"] == ["test-exhibit-001"]
    assert response.json()["remaining_time"] == 35


def test_record_visit_event_updates_current_exhibit_and_history(client, db_session: Session) -> None:
    seed_exhibit(db_session, "test-exhibit-001")
    seed_exhibit(db_session, "test-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-event-001",
            "visitor_type": "tourist",
            "current_exhibit": "test-exhibit-001",
            "visited_history": ["test-exhibit-001"],
            "interest": [],
            "remaining_time": 25,
        },
    )

    response = client.post(
        "/api/visitor-states/session-event-001/visit-events",
        json={"exhibit_id": "test-exhibit-002", "remaining_time": 18},
    )

    assert response.status_code == 200
    assert response.json()["current_exhibit"] == "test-exhibit-002"
    assert response.json()["visited_history"] == ["test-exhibit-001", "test-exhibit-002"]
    assert response.json()["remaining_time"] == 18


def test_list_visit_events_returns_recorded_visit_event_timeline(client, db_session: Session) -> None:
    seed_exhibit(db_session, "timeline-exhibit-001")
    seed_exhibit(db_session, "timeline-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-event-timeline",
            "visitor_type": "tourist",
            "current_exhibit": None,
            "visited_history": [],
            "interest": [],
            "remaining_time": 30,
        },
    )
    client.post(
        "/api/visitor-states/session-event-timeline/visit-events",
        json={"exhibit_id": "timeline-exhibit-001", "remaining_time": 25},
    )
    client.post(
        "/api/visitor-states/session-event-timeline/visit-events",
        json={"exhibit_id": "timeline-exhibit-002"},
    )

    response = client.get("/api/visitor-states/session-event-timeline/visit-events")

    assert response.status_code == 200
    body = response.json()
    assert [item["exhibit_id"] for item in body] == ["timeline-exhibit-001", "timeline-exhibit-002"]
    assert body[0]["session_id"] == "session-event-timeline"
    assert body[0]["remaining_time"] == 25
    assert body[1]["remaining_time"] is None
    assert body[0]["event_time"]


def test_list_visit_events_supports_pagination(client, db_session: Session) -> None:
    seed_exhibit(db_session, "timeline-page-exhibit-001")
    seed_exhibit(db_session, "timeline-page-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-event-timeline-page",
            "visitor_type": "tourist",
            "current_exhibit": None,
            "visited_history": [],
            "interest": [],
            "remaining_time": 30,
        },
    )
    for exhibit_id, remaining_time in [
        ("timeline-page-exhibit-001", 25),
        ("timeline-page-exhibit-002", 20),
        ("timeline-page-exhibit-001", 15),
    ]:
        client.post(
            "/api/visitor-states/session-event-timeline-page/visit-events",
            json={"exhibit_id": exhibit_id, "remaining_time": remaining_time},
        )

    response = client.get("/api/visitor-states/session-event-timeline-page/visit-events?limit=1&offset=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["exhibit_id"] == "timeline-page-exhibit-002"
    assert body[0]["remaining_time"] == 20


def test_record_visit_event_does_not_duplicate_history(client, db_session: Session) -> None:
    seed_exhibit(db_session, "test-exhibit-001")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-event-002",
            "visitor_type": "tourist",
            "current_exhibit": "test-exhibit-001",
            "visited_history": ["test-exhibit-001"],
            "interest": [],
            "remaining_time": 25,
        },
    )

    response = client.post(
        "/api/visitor-states/session-event-002/visit-events",
        json={"exhibit_id": "test-exhibit-001"},
    )

    assert response.status_code == 200
    assert response.json()["visited_history"] == ["test-exhibit-001"]
    assert response.json()["remaining_time"] == 25


def test_record_visit_event_rejects_missing_exhibit(client, db_session: Session) -> None:
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-event-003",
            "visitor_type": "tourist",
            "current_exhibit": None,
            "visited_history": [],
            "interest": [],
            "remaining_time": 25,
        },
    )

    response = client.post(
        "/api/visitor-states/session-event-003/visit-events",
        json={"exhibit_id": "missing-exhibit"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Referenced exhibit 'missing-exhibit' was not found."


def test_record_visit_event_returns_404_for_missing_session(client) -> None:
    response = client.post(
        "/api/visitor-states/missing-session/visit-events",
        json={"exhibit_id": "test-exhibit-001"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_list_visit_events_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/visitor-states/missing-session/visit-events")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_create_visitor_state_rejects_missing_exhibit(client) -> None:
    response = client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-004",
            "visitor_type": "tourist",
            "current_exhibit": "missing-exhibit",
            "visited_history": [],
            "interest": [],
            "remaining_time": 15,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Referenced exhibit 'missing-exhibit' was not found."


def test_read_visitor_state_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/visitor-states/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."
