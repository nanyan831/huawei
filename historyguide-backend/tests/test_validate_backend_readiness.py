from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from scripts import validate_backend_readiness


def test_run_validation_checks_core_read_only_backend_gates(monkeypatch) -> None:
    seen_paths: list[str] = []

    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        path = "/" + request.full_url.split("/", 3)[3]
        seen_paths.append(path)
        payloads = _base_payloads()
        return _response(payloads[path])

    monkeypatch.setattr(validate_backend_readiness, "urlopen", fake_urlopen)

    results = validate_backend_readiness.run_validation(
        "http://testserver",
        api_key="business-secret",
        operator_key="operator-secret",
        require_exhibits=True,
        require_sourced_exhibits=True,
        require_audit_logs=True,
        require_clean_operational_alerts=True,
    )

    assert all(result.ok for result in results)
    assert seen_paths == [
        "/ready",
        "/api/system/database",
        "/api/system/operational-alerts",
        "/api/exhibits/source-report",
        "/api/exhibits/quality-report",
        "/api/audit-logs/stats",
    ]
    assert [result.request_id for result in results] == ["readiness-request-id"] * len(results)


def test_run_validation_checks_session_and_genios_source_safety(monkeypatch) -> None:
    seen_paths: list[str] = []

    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        path = "/" + request.full_url.split("/", 3)[3]
        seen_paths.append(path)
        payloads = _base_payloads()
        payloads.update(_ready_session_payloads())
        return _response(payloads[path])

    monkeypatch.setattr(validate_backend_readiness, "urlopen", fake_urlopen)

    results = validate_backend_readiness.run_validation(
        "http://testserver",
        api_key="business-secret",
        operator_key="operator-secret",
        session_id="ready-session",
        require_visit_events=True,
    )

    assert all(result.ok for result in results)
    assert "/api/visitor-states/ready-session/integrity" in seen_paths
    assert "/api/genios/grounding/ready-session" in seen_paths
    assert "/api/genios/preflight/ready-session" in seen_paths
    assert "/api/genios/handoff/ready-session" in seen_paths


def test_run_validation_fails_when_source_safety_is_not_ready(monkeypatch) -> None:
    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        path = "/" + request.full_url.split("/", 3)[3]
        payloads = _base_payloads()
        payloads.update(_ready_session_payloads())
        payloads["/api/genios/handoff/blocked-session"] = {
            "source_safety": {
                "ready_for_generation": False,
                "grounding_sources_complete": False,
                "blocking_check_names": ["grounding_source_references"],
            }
        }
        payloads["/api/genios/grounding/blocked-session"] = {
            "grounding_sources_complete": False,
            "missing_exhibit_ids": [],
            "unsourced_exhibit_ids": ["unsourced-exhibit"],
        }
        payloads["/api/genios/preflight/blocked-session"] = {
            "ready_for_handoff": False,
            "checks": [{"name": "grounding_source_references", "status": "fail"}],
        }
        payloads["/api/visitor-states/blocked-session/integrity"] = {"issue_count": 0}
        payloads["/api/visitor-states/blocked-session/visit-events"] = [
            {"exhibit_id": "unsourced-exhibit"}
        ]
        payloads["/api/recommendations/blocked-session"] = []
        payloads["/api/visit-routes/blocked-session/plan"] = {"planned_minutes": 0, "items": []}
        payloads["/api/visits/blocked-session/summary"] = {
            "visited_count": 1,
            "missing_exhibit_ids": [],
        }
        return _response(payloads[path])

    monkeypatch.setattr(validate_backend_readiness, "urlopen", fake_urlopen)

    results = validate_backend_readiness.run_validation(
        "http://testserver",
        api_key="business-secret",
        operator_key="operator-secret",
        session_id="blocked-session",
        require_visit_events=True,
    )

    failures = {result.name: result for result in results if not result.ok}
    assert {"genios_grounding", "genios_preflight", "genios_handoff"} <= set(failures)
    assert "source_safety.ready_for_generation=False" in failures["genios_handoff"].detail


def test_main_does_not_print_secret_values(monkeypatch, capsys) -> None:
    captured_headers: list[dict[str, str]] = []

    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        captured_headers.append(dict(request.header_items()))
        path = "/" + request.full_url.split("/", 3)[3]
        payloads = _base_payloads()
        return _response(payloads[path])

    monkeypatch.setattr(validate_backend_readiness, "urlopen", fake_urlopen)

    exit_code = validate_backend_readiness.main(
        [
            "--base-url",
            "http://testserver",
            "--api-key",
            "business-secret",
            "--operator-key",
            "operator-secret",
            "--require-exhibits",
            "--require-sourced-exhibits",
            "--require-audit-logs",
            "--require-clean-operational-alerts",
        ]
    )

    assert exit_code == 0
    assert {"X-historyguide-operator-key": "operator-secret"} in captured_headers
    output = capsys.readouterr().out
    assert "request_id=readiness-request-id" in output
    assert "business-secret" not in output
    assert "operator-secret" not in output
    assert "does not run RAG" in output
    assert "does not generate explanation content" in output


def test_run_validation_fails_when_required_audit_logs_are_missing(monkeypatch) -> None:
    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        path = "/" + request.full_url.split("/", 3)[3]
        payloads = _base_payloads()
        payloads["/api/audit-logs/stats"] = {
            "total_logs": 0,
            "latest_created_at": None,
        }
        return _response(payloads[path])

    monkeypatch.setattr(validate_backend_readiness, "urlopen", fake_urlopen)

    results = validate_backend_readiness.run_validation(
        "http://testserver",
        api_key="business-secret",
        operator_key="operator-secret",
        require_audit_logs=True,
    )

    audit_result = next(result for result in results if result.name == "audit_log_stats")
    assert audit_result.ok is False
    assert "total_logs=0" in audit_result.detail


def _base_payloads() -> dict[str, object]:
    return {
        "/ready": {"status": "ready", "database": "ok"},
        "/api/system/database": {
            "backend": "sqlite",
            "persistence": "local_file",
            "schema_management": "alembic",
        },
        "/api/system/operational-alerts": {
            "status": "ok",
            "fail_count": 0,
            "warn_count": 0,
        },
        "/api/exhibits/source-report": {
            "total": 2,
            "sourced_count": 2,
            "unsourced_count": 0,
        },
        "/api/exhibits/quality-report": {
            "total": 2,
            "source_reference_coverage_percent": 100.0,
            "issues": [],
        },
        "/api/audit-logs/stats": {
            "total_logs": 3,
            "latest_created_at": "2026-09-27T00:00:00",
        },
    }


def _ready_session_payloads() -> dict[str, object]:
    return {
        "/api/visitor-states/ready-session/integrity": {"issue_count": 0},
        "/api/visitor-states/ready-session/visit-events": [
            {"exhibit_id": "fixture-exhibit-001"}
        ],
        "/api/recommendations/ready-session": [{"exhibit_id": "fixture-exhibit-002"}],
        "/api/visit-routes/ready-session/plan": {
            "planned_minutes": 8,
            "items": [{"exhibit_id": "fixture-exhibit-002"}],
        },
        "/api/visits/ready-session/summary": {
            "visited_count": 1,
            "missing_exhibit_ids": [],
        },
        "/api/genios/grounding/ready-session": {
            "grounding_sources_complete": True,
            "missing_exhibit_ids": [],
            "unsourced_exhibit_ids": [],
        },
        "/api/genios/preflight/ready-session": {
            "ready_for_handoff": True,
            "checks": [{"name": "grounding_source_references", "status": "pass"}],
        },
        "/api/genios/handoff/ready-session": {
            "source_safety": {
                "ready_for_generation": True,
                "grounding_sources_complete": True,
                "blocking_check_names": [],
            }
        },
    }


@contextmanager
def _response(
    payload: object,
    request_id: str | None = "readiness-request-id",
) -> Callable[[], bytes]:
    class Response:
        status = 200
        headers = (
            {validate_backend_readiness.REQUEST_ID_HEADER: request_id}
            if request_id is not None
            else {}
        )

        def read(self) -> bytes:
            return json_dumps(payload).encode("utf-8")

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    yield Response()


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload)
