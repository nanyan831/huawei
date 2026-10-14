from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorVisitEventLog
from app.schemas.exhibit import ExhibitCreate
from app.services.audit_log_service import record_audit_log
from app.services.exhibit_service import create_exhibit


def seed_exhibit(
    db_session: Session,
    exhibit_id: str,
    *,
    source_reference: str | None = "Test fixture only.",
    keywords: list[str] | None = None,
    themes: list[str] | None = None,
    people: list[str] | None = None,
) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id=exhibit_id,
            name=f"Operational Alert Test Exhibit {exhibit_id}",
            description="A non-historical fixture for operational alert checks.",
            period="test-period",
            keywords=keywords if keywords is not None else ["ops"],
            importance=3,
            people=people if people is not None else ["Test Person"],
            time_range=None,
            themes=themes if themes is not None else ["operations"],
            source_reference=source_reference,
        ),
    )


def test_operational_alerts_warn_for_empty_database(client) -> None:
    response = client.get("/api/system/operational-alerts")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "attention_required"
    assert body["fail_count"] == 0
    alert_names = {alert["name"] for alert in body["alerts"]}
    assert {"no_exhibit_records", "audit_logs_empty"}.issubset(alert_names)


def test_operational_alerts_return_ok_when_core_operational_signals_are_clean(
    client,
    db_session: Session,
) -> None:
    seed_exhibit(db_session, "ops-clean-exhibit-001")
    record_audit_log(
        db_session,
        action="operator_smoke_check",
        resource_type="system",
        resource_id="ops-clean",
        actor="test",
        commit=True,
    )

    response = client.get("/api/system/operational-alerts")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "total_alerts": 0,
        "fail_count": 0,
        "warn_count": 0,
        "alerts": [],
    }


def test_operational_alerts_fail_for_unsourced_exhibits_and_visitor_state_drift(
    client,
    db_session: Session,
) -> None:
    seed_exhibit(db_session, "ops-alert-exhibit-001", source_reference=None)
    seed_exhibit(db_session, "ops-alert-exhibit-002")
    client.post(
        "/api/visitor-states",
        json={
            "session_id": "session-ops-alert",
            "visitor_type": "tourist",
            "current_exhibit": "ops-alert-exhibit-001",
            "visited_history": ["ops-alert-exhibit-001"],
            "interest": [],
            "remaining_time": 20,
        },
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="session-ops-alert",
            exhibit_id="ops-alert-exhibit-002",
            remaining_time=18,
        )
    )
    db_session.commit()

    response = client.get("/api/system/operational-alerts")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "attention_required"
    assert body["fail_count"] == 2
    alerts = {alert["name"]: alert for alert in body["alerts"]}
    assert alerts["unsourced_exhibits"]["severity"] == "fail"
    assert alerts["unsourced_exhibits"]["count"] == 1
    assert alerts["visitor_state_integrity_issues"]["severity"] == "fail"
    assert alerts["visitor_state_integrity_issues"]["count"] == 2
