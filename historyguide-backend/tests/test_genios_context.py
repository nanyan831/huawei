from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState, VisitorVisitEventLog
from app.services.evidence_service import approve_exhibit, approve_source, create_source, link_source
from app.schemas.exhibit import ExhibitCreate
from app.schemas.visitor_state import VisitorStateCreate
from app.services.exhibit_service import create_exhibit
from app.services.visitor_state_service import create_visitor_state


def test_genios_capabilities_describe_backend_contract_and_workflow(client) -> None:
    response = client.get("/api/genios/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["service_id"] == "nk-historyguide-backend"
    assert body["supported_visitor_types"] == ["freshman", "alumnus", "tourist"]
    assert "does not generate museum explanation text" in body["collaboration_contract"]["generation_boundary"]
    assert any("GeniOS context package" == endpoint["name"] for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/genios/grounding/{session_id}" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/genios/preflight/{session_id}" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/genios/handoff/{session_id}" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/genios/review" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/genios/history-runs" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/visitor-states/integrity-report" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/visitor-states/{session_id}/integrity" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/api/exhibits/source-report" for endpoint in body["endpoints"])
    assert any("verified RAG sources" in note for note in body["integration_notes"])
    assert any("grounding_exhibit_ids" in note for note in body["integration_notes"])
    assert any("grounding_sources_complete" in note for note in body["integration_notes"])


def seed_context_exhibit(
    db_session: Session,
    *,
    exhibit_id: str,
    name: str,
    keywords: list[str],
    importance: int,
    source_reference: str | None = "Test fixture only.",
) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id=exhibit_id,
            name=name,
            description=f"{name} description for GeniOS context tests.",
            period="test-period",
            keywords=keywords,
            importance=importance,
            people=[],
            time_range=None,
            themes=keywords,
            source_reference=source_reference,
        ),
    )


def approve_context_exhibits(db_session: Session, exhibit_ids: list[str]) -> None:
    for exhibit_id in exhibit_ids:
        source_id = f"source-{exhibit_id}"
        create_source(
            db_session,
            source_id=source_id,
            title=f"Approved archive for {exhibit_id}",
            source_uri=f"museum-archive:{source_id}",
            content_text=f"Reviewed evidence for {exhibit_id}.",
        )
        approve_source(db_session, source_id, reviewer="museum-reviewer")
        link_source(db_session, exhibit_id, source_id)
        approve_exhibit(db_session, exhibit_id, reviewer="museum-reviewer")


def test_genios_context_package_contains_visit_state_exhibits_and_recommendations(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="current-exhibit",
        name="Current Exhibit",
        keywords=["orientation"],
        importance=4,
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="next-exhibit",
        name="Next Exhibit",
        keywords=["architecture"],
        importance=3,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-session-001",
            visitor_type="tourist",
            current_exhibit="current-exhibit",
            visited_history=["current-exhibit"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-session-001",
            exhibit_id="next-exhibit",
            remaining_time=20,
        )
    )
    db_session.commit()

    response = client.get("/api/genios/context/genios-session-001")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "genios-session-001"
    assert body["visitor_state"]["visitor_type"] == "tourist"
    assert body["current_exhibit"]["id"] == "current-exhibit"
    assert [item["id"] for item in body["visited_exhibits"]] == ["current-exhibit"]
    assert body["visit_events"][0]["exhibit_id"] == "next-exhibit"
    assert body["visit_events"][0]["remaining_time"] == 20
    assert body["recommendations"][0]["exhibit_id"] == "next-exhibit"
    assert body["grounding_exhibit_ids"] == ["current-exhibit", "next-exhibit"]
    assert body["missing_exhibit_ids"] == []
    assert "does not generate museum explanation text" in body["collaboration_contract"]["generation_boundary"]


def test_genios_grounding_package_contains_ordered_exhibits_and_sources(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="grounding-current",
        name="Grounding Current",
        keywords=["orientation"],
        importance=4,
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="grounding-next",
        name="Grounding Next",
        keywords=["architecture"],
        importance=3,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-grounding-001",
            visitor_type="tourist",
            current_exhibit="grounding-current",
            visited_history=["grounding-current"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )

    response = client.get("/api/genios/grounding/genios-grounding-001")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "genios-grounding-001"
    assert body["grounding_exhibit_ids"] == ["grounding-current", "grounding-next"]
    assert [exhibit["id"] for exhibit in body["exhibits"]] == ["grounding-current", "grounding-next"]
    assert body["source_references"] == ["Test fixture only."]
    assert body["source_reference_count"] == 1
    assert body["sourced_exhibit_ids"] == ["grounding-current", "grounding-next"]
    assert body["unsourced_exhibit_ids"] == []
    assert body["grounding_sources_complete"] is True
    assert body["missing_exhibit_ids"] == []
    assert "does not generate museum explanation text" in body["collaboration_contract"]["generation_boundary"]


def test_genios_grounding_and_preflight_flag_unsourced_grounding_exhibits(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="grounding-unsourced",
        name="Grounding Unsourced",
        keywords=["orientation"],
        importance=4,
        source_reference="  ",
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="grounding-sourced-next",
        name="Grounding Sourced Next",
        keywords=["architecture"],
        importance=3,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-grounding-unsourced",
            visitor_type="tourist",
            current_exhibit="grounding-unsourced",
            visited_history=["grounding-unsourced"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-grounding-unsourced",
            exhibit_id="grounding-unsourced",
            remaining_time=20,
        )
    )
    db_session.commit()

    grounding_response = client.get("/api/genios/grounding/genios-grounding-unsourced")

    assert grounding_response.status_code == 200
    grounding_body = grounding_response.json()
    assert grounding_body["grounding_exhibit_ids"] == ["grounding-unsourced", "grounding-sourced-next"]
    assert grounding_body["source_references"] == ["Test fixture only."]
    assert grounding_body["source_reference_count"] == 1
    assert grounding_body["sourced_exhibit_ids"] == ["grounding-sourced-next"]
    assert grounding_body["unsourced_exhibit_ids"] == ["grounding-unsourced"]
    assert grounding_body["grounding_sources_complete"] is False

    preflight_response = client.get("/api/genios/preflight/genios-grounding-unsourced")

    assert preflight_response.status_code == 200
    preflight_body = preflight_response.json()
    checks = {check["name"]: check["status"] for check in preflight_body["checks"]}
    assert preflight_body["ready_for_handoff"] is False
    assert checks["exhibit_references"] == "pass"
    assert checks["grounding_source_references"] == "fail"
    assert checks["visitor_state_integrity"] == "pass"
    assert checks["visit_event_timeline"] == "pass"
    assert checks["recommendations"] == "pass"

    handoff_response = client.get("/api/genios/handoff/genios-grounding-unsourced")

    assert handoff_response.status_code == 200
    source_safety = handoff_response.json()["source_safety"]
    assert source_safety["ready_for_generation"] is False
    assert source_safety["grounding_sources_complete"] is False
    assert source_safety["source_reference_count"] == 1
    assert source_safety["sourced_exhibit_ids"] == ["grounding-sourced-next"]
    assert source_safety["unsourced_exhibit_ids"] == ["grounding-unsourced"]
    assert source_safety["missing_exhibit_ids"] == []
    assert source_safety["blocking_check_names"] == ["grounding_source_references", "museum_approval"]


def test_genios_handoff_package_combines_context_route_plan_and_summary(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-current",
        name="Handoff Current",
        keywords=["orientation"],
        importance=4,
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-next",
        name="Handoff Next",
        keywords=["architecture"],
        importance=3,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-handoff-001",
            visitor_type="tourist",
            current_exhibit="handoff-current",
            visited_history=["handoff-current"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-handoff-001",
            exhibit_id="handoff-next",
            remaining_time=20,
        )
    )
    db_session.commit()

    response = client.get("/api/genios/handoff/genios-handoff-001?route_max_items=1")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "genios-handoff-001"
    assert body["source_safety"]["ready_for_generation"] is False
    assert body["source_safety"]["grounding_sources_complete"] is True
    assert body["source_safety"]["source_reference_count"] == 1
    assert body["source_safety"]["unsourced_exhibit_ids"] == []
    assert body["source_safety"]["blocking_check_names"] == ["visitor_state_integrity", "museum_approval"]
    assert body["preflight"]["ready_for_handoff"] is False
    assert body["preflight"]["visit_event_count"] == 1
    assert body["preflight"]["recommendation_count"] == 1
    assert body["preflight"]["integrity_report"]["issue_count"] == 2
    assert body["context"]["current_exhibit"]["id"] == "handoff-current"
    assert body["context"]["visit_events"][0]["exhibit_id"] == "handoff-next"
    assert body["context"]["grounding_exhibit_ids"] == ["handoff-current", "handoff-next"]
    assert body["route_plan"]["items"][0]["exhibit_id"] == "handoff-next"
    assert len(body["route_plan"]["items"]) == 1
    assert body["visit_summary"]["visited_count"] == 1
    assert "does not generate explanation text" in body["handoff_note"]


def test_genios_handoff_package_exposes_ready_source_safety_summary(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-ready-current",
        name="Handoff Ready Current",
        keywords=["orientation"],
        importance=4,
        source_reference="Museum archive source.",
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-ready-next",
        name="Handoff Ready Next",
        keywords=["architecture"],
        importance=3,
        source_reference="Museum archive source.",
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-handoff-ready",
            visitor_type="tourist",
            current_exhibit="handoff-ready-current",
            visited_history=["handoff-ready-current"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-handoff-ready",
            exhibit_id="handoff-ready-current",
            remaining_time=20,
        )
    )
    db_session.commit()

    approve_context_exhibits(
        db_session, ["handoff-ready-current", "handoff-ready-next"]
    )

    response = client.get("/api/genios/handoff/genios-handoff-ready")

    assert response.status_code == 200
    source_safety = response.json()["source_safety"]
    assert source_safety["ready_for_generation"] is True
    assert source_safety["grounding_sources_complete"] is True
    assert source_safety["source_reference_count"] == 1
    assert source_safety["sourced_exhibit_ids"] == ["handoff-ready-current", "handoff-ready-next"]
    assert source_safety["unsourced_exhibit_ids"] == []
    assert source_safety["missing_exhibit_ids"] == []
    assert source_safety["blocking_check_names"] == []
    assert "complete" in source_safety["safety_note"]


def test_handoff_blocks_structurally_ready_but_unapproved_exhibit(
    client, db_session: Session
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="unapproved-current",
        name="Unapproved Current",
        keywords=["history"],
        importance=3,
        source_reference="Archive reference awaiting museum approval.",
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="unapproved-session",
            visitor_type="tourist",
            current_exhibit="unapproved-current",
            visited_history=["unapproved-current"],
            interest=["history"],
            remaining_time=20,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="unapproved-session",
            exhibit_id="unapproved-current",
            remaining_time=20,
        )
    )
    db_session.commit()

    handoff = client.get("/api/genios/handoff/unapproved-session")
    assert handoff.status_code == 200
    assert handoff.json()["preflight"]["ready_for_handoff"] is True
    assert handoff.json()["source_safety"]["grounding_sources_complete"] is True
    assert handoff.json()["source_safety"]["ready_for_generation"] is False
    assert handoff.json()["source_safety"]["blocking_check_names"] == ["museum_approval"]

    flat = client.get("/api/genios/handoff-flat/unapproved-session")
    assert flat.status_code == 200
    assert flat.json()["ready_for_generation"] is False
    assert flat.json()["blocking_check_names"] == "museum_approval"


def test_genios_flat_handoff_returns_platform_friendly_scalar_fields(
    client,
    db_session: Session,
) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-flat-current",
        name="Handoff Flat Current",
        keywords=["orientation"],
        importance=4,
        source_reference="Museum archive source.",
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="handoff-flat-next",
        name="Handoff Flat Next",
        keywords=["architecture"],
        importance=3,
        source_reference="Museum archive source.",
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-handoff-flat",
            visitor_type="tourist",
            current_exhibit="handoff-flat-current",
            visited_history=["handoff-flat-current"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-handoff-flat",
            exhibit_id="handoff-flat-current",
            remaining_time=20,
        )
    )
    db_session.commit()

    approve_context_exhibits(
        db_session, ["handoff-flat-current", "handoff-flat-next"]
    )

    response = client.get("/api/genios/handoff-flat/genios-handoff-flat?route_max_items=1")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "genios-handoff-flat"
    assert body["ready_for_generation"] is True
    assert body["grounding_sources_complete"] is True
    assert body["source_reference_count"] == 1
    assert body["sourced_exhibit_ids"] == "handoff-flat-current,handoff-flat-next"
    assert body["unsourced_exhibit_ids"] == ""
    assert body["missing_exhibit_ids"] == ""
    assert body["blocking_check_names"] == ""
    assert body["visitor_type"] == "tourist"
    assert body["current_exhibit_id"] == "handoff-flat-current"
    assert body["visited_count"] == 1
    assert body["recommendation_count"] == 1
    assert body["recommendation_exhibit_ids"] == "handoff-flat-next"
    assert body["route_exhibit_ids"] == "handoff-flat-next"
    assert body["planned_minutes"] == 7
    assert body["remaining_time"] == 25
    assert "does not generate explanation text" in body["handoff_note"]


def test_genios_preflight_package_reports_ready_session(client, db_session: Session) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="preflight-current",
        name="Preflight Current",
        keywords=["orientation"],
        importance=4,
    )
    seed_context_exhibit(
        db_session,
        exhibit_id="preflight-next",
        name="Preflight Next",
        keywords=["architecture"],
        importance=3,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="genios-preflight-ready",
            visitor_type="tourist",
            current_exhibit="preflight-current",
            visited_history=["preflight-current"],
            interest=["architecture"],
            remaining_time=25,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="genios-preflight-ready",
            exhibit_id="preflight-current",
            remaining_time=20,
        )
    )
    db_session.commit()

    response = client.get("/api/genios/preflight/genios-preflight-ready")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "genios-preflight-ready"
    assert body["ready_for_handoff"] is True
    assert body["missing_exhibit_ids"] == []
    assert body["integrity_report"]["issue_count"] == 0
    assert body["visit_event_count"] == 1
    assert body["recommendation_count"] == 1
    assert {check["name"]: check["status"] for check in body["checks"]} == {
        "exhibit_references": "pass",
        "grounding_source_references": "pass",
        "visitor_state_integrity": "pass",
        "visit_event_timeline": "pass",
        "recommendations": "pass",
    }
    assert "does not generate museum explanation text" in body["collaboration_contract"]["generation_boundary"]


def test_genios_preflight_package_flags_missing_exhibit_references(
    client,
    db_session: Session,
) -> None:
    db_session.add(
        VisitorState(
            session_id="genios-preflight-missing",
            visitor_type="freshman",
            current_exhibit="missing-current",
            visited_history=["missing-current", "missing-visited"],
            interest=[],
            remaining_time=10,
        )
    )
    db_session.commit()

    response = client.get("/api/genios/preflight/genios-preflight-missing")

    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_handoff"] is False
    assert body["missing_exhibit_ids"] == ["missing-current", "missing-visited"]
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["exhibit_references"]["status"] == "fail"
    assert checks["visitor_state_integrity"]["status"] == "fail"
    assert checks["visit_event_timeline"]["status"] == "warn"


def test_genios_context_package_reports_missing_exhibit_references(
    client,
    db_session: Session,
) -> None:
    db_session.add(
        VisitorState(
            session_id="genios-session-002",
            visitor_type="freshman",
            current_exhibit="missing-current",
            visited_history=["missing-current", "missing-visited"],
            interest=[],
            remaining_time=10,
        )
    )
    db_session.commit()

    response = client.get("/api/genios/context/genios-session-002")

    assert response.status_code == 200
    body = response.json()
    assert body["current_exhibit"] is None
    assert body["visited_exhibits"] == []
    assert body["grounding_exhibit_ids"] == []
    assert body["missing_exhibit_ids"] == ["missing-current", "missing-visited"]


def test_genios_context_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/genios/context/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_genios_grounding_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/genios/grounding/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_genios_handoff_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/genios/handoff/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def test_genios_preflight_returns_404_for_missing_session(client) -> None:
    response = client.get("/api/genios/preflight/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."


def _seed_review_session(db_session: Session, *, session_id: str) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id=f"{session_id}-current",
        name="Review Current",
        keywords=["orientation"],
        importance=4,
        source_reference="Nankai University History Museum verified archive A.",
    )
    seed_context_exhibit(
        db_session,
        exhibit_id=f"{session_id}-next-a",
        name="Review Next A",
        keywords=["architecture"],
        importance=5,
        source_reference="Nankai University History Museum verified archive B.",
    )
    seed_context_exhibit(
        db_session,
        exhibit_id=f"{session_id}-next-b",
        name="Review Next B",
        keywords=["architecture"],
        importance=3,
        source_reference="Nankai University History Museum verified archive C.",
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id=session_id,
            visitor_type="freshman",
            current_exhibit=f"{session_id}-current",
            visited_history=[f"{session_id}-current"],
            interest=["architecture"],
            remaining_time=30,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id=session_id,
            exhibit_id=f"{session_id}-current",
            remaining_time=30,
        )
    )
    db_session.commit()
    from app.services.evidence_service import approve_exhibit, approve_source, create_source, link_source

    for suffix in ("current", "next-a", "next-b"):
        exhibit_id = f"{session_id}-{suffix}"
        source_id = f"source-{exhibit_id}"
        create_source(
            db_session,
            source_id=source_id,
            title=f"Approved archive for {exhibit_id}",
            source_uri=f"museum-archive:{source_id}",
            content_text=f"Reviewed evidence for {exhibit_id}.",
        )
        approve_source(db_session, source_id, reviewer="museum-reviewer")
        link_source(db_session, exhibit_id, source_id)
        approve_exhibit(db_session, exhibit_id, reviewer="museum-reviewer")


def test_genios_review_passes_grounded_draft_in_route_order(client, db_session: Session) -> None:
    _seed_review_session(db_session, session_id="review-pass")

    response = client.post(
        "/api/genios/review",
        json={
            "session_id": "review-pass",
            "draft_answer": "请先参观 A，再参观 B。",
            "cited_exhibit_ids": "review-pass-next-a,review-pass-next-b",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "pass"
    assert body["issues"] == ""
    assert body["safe_answer"] == "请先参观 A，再参观 B。"
    assert body["route_order_valid"] is True
    assert body["exhibit_ids_valid"] is True
    assert body["source_references_valid"] is True
    assert body["fixture_data_detected"] is False


def test_genios_review_requests_revision_for_wrong_route_order(
    client,
    db_session: Session,
) -> None:
    _seed_review_session(db_session, session_id="review-revise")

    response = client.post(
        "/api/genios/review",
        json={
            "session_id": "review-revise",
            "draft_answer": "请先参观 B，再参观 A。",
            "cited_exhibit_ids": "review-revise-next-b,review-revise-next-a",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "revise"
    assert body["route_order_valid"] is False
    assert "route order" in body["issues"]


def test_genios_review_blocks_fixture_data(client, db_session: Session) -> None:
    seed_context_exhibit(
        db_session,
        exhibit_id="fixture-review-current",
        name="Fixture Review Current",
        keywords=["orientation"],
        importance=4,
    )
    create_visitor_state(
        db_session,
        VisitorStateCreate(
            session_id="review-fixture",
            visitor_type="tourist",
            current_exhibit="fixture-review-current",
            visited_history=["fixture-review-current"],
            interest=[],
            remaining_time=10,
        ),
    )
    db_session.add(
        VisitorVisitEventLog(
            session_id="review-fixture",
            exhibit_id="fixture-review-current",
            remaining_time=10,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/genios/review",
        json={
            "session_id": "review-fixture",
            "draft_answer": "这是一个开发数据讲解。",
            "cited_exhibit_ids": "fixture-review-current",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "block"
    assert body["fixture_data_detected"] is True
    assert "fixture data" in body["issues"]


def test_genios_review_returns_404_for_missing_session(client) -> None:
    response = client.post(
        "/api/genios/review",
        json={
            "session_id": "missing-session",
            "draft_answer": "Draft.",
            "cited_exhibit_ids": "missing-exhibit",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Visitor session 'missing-session' was not found."
