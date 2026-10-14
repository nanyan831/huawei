from fastapi.testclient import TestClient

from app.main import app


def test_openapi_contains_core_mvp_paths() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    expected_paths = {
        "/health",
        "/ready",
        "/api/system/database",
        "/api/system/access-policy",
        "/api/system/operational-alerts",
        "/api/system/security-status",
        "/api/audit-logs",
        "/api/audit-logs/stats",
        "/api/exhibits",
        "/api/exhibits/facets",
        "/api/exhibits/quality-report",
        "/api/exhibits/source-report",
        "/api/exhibits/{exhibit_id}",
        "/api/visitor-states",
        "/api/visitor-states/stats",
        "/api/visitor-states/integrity-report",
        "/api/visitor-states/{session_id}",
        "/api/visitor-states/{session_id}/integrity",
        "/api/visitor-states/{session_id}/visit-events",
        "/api/recommendations/{session_id}",
        "/api/genios/capabilities",
        "/api/genios/context/{session_id}",
        "/api/genios/grounding/{session_id}",
        "/api/genios/preflight/{session_id}",
        "/api/genios/handoff/{session_id}",
        "/api/genios/handoff-flat/{session_id}",
        "/api/genios/review",
        "/api/genios/runs",
        "/api/genios/runs/{run_id}/review",
        "/api/genios/runs/{run_id}/finalize",
        "/api/genios/history-runs",
        "/api/genios/history-runs/{run_id}/review",
        "/api/genios/history-runs/{run_id}/finalize",
        "/api/evidence/review-run-stats",
        "/openapi-genios-handoff.json",
        "/openapi-genios-review.json",
        "/openapi-genios-runs.json",
        "/openapi-genios-history-runs.json",
        "/api/visits/{session_id}/summary",
        "/api/visit-routes/{session_id}/plan",
    }
    assert expected_paths.issubset(paths.keys())


def test_openapi_contains_core_route_tags() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    operations = [
        method_schema
        for path_schema in response.json()["paths"].values()
        for method_schema in path_schema.values()
        if isinstance(method_schema, dict)
    ]
    tags = {tag for operation in operations for tag in operation.get("tags", [])}

    assert {
        "health",
        "audit-logs",
        "exhibits",
        "visitor-states",
        "recommendations",
        "genios",
        "visit-summaries",
        "visit-routes",
    }.issubset(tags)


def test_openapi_visit_events_supports_record_and_timeline_read() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    visit_events_path = response.json()["paths"]["/api/visitor-states/{session_id}/visit-events"]
    assert {"get", "post"}.issubset(visit_events_path.keys())
    get_parameters = {parameter["name"] for parameter in visit_events_path["get"]["parameters"]}
    assert {"session_id", "limit", "offset"}.issubset(get_parameters)


def test_genios_handoff_openapi_is_minimal_plugin_contract() -> None:
    client = TestClient(app)

    response = client.get("/openapi-genios-handoff.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"] == "3.0.3"
    assert list(spec["paths"].keys()) == ["/api/genios/handoff/{session_id}"]
    handoff_operation = spec["paths"]["/api/genios/handoff/{session_id}"]["get"]
    assert handoff_operation["operationId"] == "get_genios_handoff"
    parameter_names = {parameter["name"] for parameter in handoff_operation["parameters"]}
    assert {"session_id", "recommendation_limit", "route_max_items"}.issubset(parameter_names)
    assert spec["components"]["securitySchemes"]["HistoryGuideApiKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-HistoryGuide-Api-Key",
    }


def test_genios_review_openapi_is_minimal_flat_plugin_contract() -> None:
    client = TestClient(app)

    response = client.get("/openapi-genios-review.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"] == "3.0.3"
    assert list(spec["paths"].keys()) == ["/api/genios/review"]
    operation = spec["paths"]["/api/genios/review"]["post"]
    assert operation["operationId"] == "review_genios_answer"
    request_schema = spec["components"]["schemas"]["ReviewRequest"]
    assert request_schema["required"] == ["session_id", "draft_answer", "cited_exhibit_ids"]
    response_properties = spec["components"]["schemas"]["ReviewResponse"]["properties"]
    assert all(property_schema["type"] != "array" for property_schema in response_properties.values())
    assert spec["components"]["securitySchemes"]["HistoryGuideApiKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-HistoryGuide-Api-Key",
    }


def test_genios_runs_openapi_matches_snapshot_workflow() -> None:
    client = TestClient(app)
    response = client.get("/openapi-genios-runs.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"] == "3.0.3"
    assert set(spec["paths"]) == {
        "/api/genios/runs",
        "/api/genios/runs/{run_id}/review",
        "/api/genios/runs/{run_id}/finalize",
    }
    operations = [path["post"] for path in spec["paths"].values()]
    assert len({operation["operationId"] for operation in operations}) == 3
    assert all(operation["security"] == [{"HistoryGuideApiKey": []}] for operation in operations)
    assert spec["components"]["securitySchemes"]["HistoryGuideApiKey"]["name"] == "X-HistoryGuide-Api-Key"
    citations = spec["components"]["schemas"]["ReviewRunRequest"]["properties"]["citations"]
    assert citations["items"]["$ref"] == "#/components/schemas/EvidenceCitation"


def test_genios_history_runs_openapi_requires_approved_sources() -> None:
    client = TestClient(app)
    response = client.get("/openapi-genios-history-runs.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"] == "3.0.3"
    assert set(spec["paths"]) == {
        "/api/genios/history-runs",
        "/api/genios/history-runs/{run_id}/review",
        "/api/genios/history-runs/{run_id}/finalize",
    }
    operations = [path["post"] for path in spec["paths"].values()]
    assert len({operation["operationId"] for operation in operations}) == 3
    assert all(operation["security"] == [{"HistoryGuideApiKey": []}] for operation in operations)
    assert spec["components"]["schemas"]["HistoryPrepareRequest"]["required"] == [
        "question", "source_ids"
    ]
    assert spec["components"]["schemas"]["HistoryReviewResponse"]["properties"]["semantic_verified"] == {
        "type": "boolean"
    }
