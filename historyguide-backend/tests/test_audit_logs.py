import json

from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.exhibit_import_service import import_exhibits_from_file
from app.services.exhibit_service import create_exhibit
from app.services.audit_log_service import list_audit_logs


def seed_exhibit(db_session: Session, exhibit_id: str = "audit-exhibit-001") -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id=exhibit_id,
            name="Audit Test Exhibit",
            description="A non-historical fixture for audit log tests.",
            period="test-period",
            keywords=["audit"],
            importance=3,
            people=[],
            time_range=None,
            themes=["operations"],
            source_reference="Test fixture only.",
        ),
    )


def test_visitor_state_changes_write_audit_logs(client, db_session: Session) -> None:
    seed_exhibit(db_session, "audit-exhibit-001")
    seed_exhibit(db_session, "audit-exhibit-002")

    create_response = client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-audit-001",
            "visitor_type": "tourist",
            "current_exhibit": "audit-exhibit-001",
            "visited_history": ["audit-exhibit-001"],
            "interest": ["operations"],
            "remaining_time": 30,
        },
    )
    assert create_response.status_code == 201

    update_response = client.patch(
        "/api/visitor-states/session-audit-001",
        json={"remaining_time": 25, "interest": ["operations", "handoff"]},
    )
    assert update_response.status_code == 200

    event_response = client.post(
        "/api/visitor-states/session-audit-001/visit-events",
        json={"exhibit_id": "audit-exhibit-002", "remaining_time": 20},
    )
    assert event_response.status_code == 200

    response = client.get("/api/audit-logs?resource_type=visitor_state&resource_id=session-audit-001")

    assert response.status_code == 200
    body = response.json()
    assert [item["action"] for item in body] == [
        "visit_event_recorded",
        "visitor_state_updated",
        "visitor_state_created",
    ]
    assert body[0]["actor"] == "api"
    assert body[0]["details"]["exhibit_id"] == "audit-exhibit-002"
    assert body[1]["details"]["updated_fields"] == ["interest", "remaining_time"]
    assert body[2]["details"]["visitor_type"] == "tourist"


def test_audit_log_endpoint_supports_action_filter_and_pagination(client, db_session: Session) -> None:
    seed_exhibit(db_session, "audit-page-exhibit-001")
    for index in range(3):
        response = client.post(
            "/api/visitor-states",
            json={
                "session_id": f"session-audit-page-{index}",
                "visitor_type": "tourist",
                "current_exhibit": "audit-page-exhibit-001",
                "visited_history": ["audit-page-exhibit-001"],
                "interest": [],
                "remaining_time": 20,
            },
        )
        assert response.status_code == 201

    response = client.get("/api/audit-logs?action=visitor_state_created&limit=1&offset=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["action"] == "visitor_state_created"
    assert body[0]["resource_id"] == "session-audit-page-1"


def test_audit_log_stats_returns_empty_summary(client) -> None:
    response = client.get("/api/audit-logs/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_logs": 0,
        "actions": [],
        "resource_types": [],
        "actors": [],
        "latest_created_at": None,
    }


def test_audit_log_stats_counts_state_change_operations(client, db_session: Session) -> None:
    seed_exhibit(db_session, "audit-stats-exhibit-001")
    seed_exhibit(db_session, "audit-stats-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-audit-stats",
            "visitor_type": "tourist",
            "current_exhibit": "audit-stats-exhibit-001",
            "visited_history": ["audit-stats-exhibit-001"],
            "interest": [],
            "remaining_time": 20,
        },
    )
    client.patch(
        "/api/visitor-states/session-audit-stats",
        json={"remaining_time": 18},
    )
    client.post(
        "/api/visitor-states/session-audit-stats/visit-events",
        json={"exhibit_id": "audit-stats-exhibit-002", "remaining_time": 15},
    )

    response = client.get("/api/audit-logs/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_logs"] == 3
    assert body["actions"] == [
        {"value": "visit_event_recorded", "count": 1},
        {"value": "visitor_state_created", "count": 1},
        {"value": "visitor_state_updated", "count": 1},
    ]
    assert body["resource_types"] == [{"value": "visitor_state", "count": 3}]
    assert body["actors"] == [{"value": "api", "count": 3}]
    assert body["latest_created_at"]


def test_exhibit_import_writes_summary_audit_log(db_session: Session, tmp_path) -> None:
    seed_path = tmp_path / "audit-import.fixture.json"
    seed_path.write_text(
        json.dumps(
            [
                {
                    "id": "audit-import-exhibit-001",
                    "name": "Audit Import Exhibit",
                    "description": "A non-historical import fixture for audit log tests.",
                    "period": "test-period",
                    "keywords": ["audit"],
                    "importance": 3,
                    "people": [],
                    "time_range": None,
                    "themes": ["operations"],
                    "source_reference": "Test fixture only.",
                }
            ]
        ),
        encoding="utf-8",
    )

    imported_count = import_exhibits_from_file(db_session, seed_path)

    assert imported_count == 1
    logs = list_audit_logs(db_session, action="exhibits_imported")
    assert len(logs) == 1
    assert logs[0].resource_type == "exhibit_import"
    assert logs[0].resource_id == seed_path.name
    assert logs[0].actor == "import_cli"
    assert logs[0].details["imported_count"] == 1
    assert logs[0].details["exhibit_ids"] == ["audit-import-exhibit-001"]
