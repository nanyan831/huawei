import logging

from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings
from app.core.request_context import REQUEST_ID_HEADER


def test_request_context_returns_generated_request_id() -> None:
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id
    assert "\n" not in request_id


def test_request_context_echoes_valid_incoming_request_id() -> None:
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/health", headers={REQUEST_ID_HEADER: "genios-demo-001"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "genios-demo-001"


def test_request_context_logs_structured_correlation_fields(caplog) -> None:
    app = main_module.create_app()
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="historyguide.request"):
        response = client.get("/health", headers={REQUEST_ID_HEADER: "structured-log-001"})

    request_log = next(record for record in caplog.records if record.name == "historyguide.request")
    assert response.status_code == 200
    assert request_log.event == "http_request_completed"
    assert request_log.request_id == "structured-log-001"
    assert request_log.http_method == "GET"
    assert request_log.path == "/health"
    assert request_log.status_code == 200
    assert isinstance(request_log.elapsed_ms, float)


def test_request_context_replaces_invalid_incoming_request_id() -> None:
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/health", headers={REQUEST_ID_HEADER: "bad id with spaces"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] != "bad id with spaces"


def test_request_context_is_present_on_auth_failures(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="business-secret"))
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/api/genios/capabilities", headers={REQUEST_ID_HEADER: "auth-failure-001"})

    assert response.status_code == 401
    assert response.headers[REQUEST_ID_HEADER] == "auth-failure-001"
