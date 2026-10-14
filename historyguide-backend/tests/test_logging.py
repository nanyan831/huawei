import json
import logging
from pathlib import Path

from app.core.logging import JsonLogFormatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_json_log_formatter_outputs_centralized_log_fields() -> None:
    record = logging.LogRecord(
        name="historyguide.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.event = "http_request_completed"
    record.request_id = "log-test-001"
    record.http_method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.elapsed_ms = 1.25

    output = JsonLogFormatter(service_id="test-service").format(record)
    payload = json.loads(output)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "historyguide.request"
    assert payload["service_id"] == "test-service"
    assert payload["message"] == "request completed"
    assert payload["event"] == "http_request_completed"
    assert payload["request_id"] == "log-test-001"
    assert payload["http_method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["elapsed_ms"] == 1.25
    assert "timestamp" in payload


def test_structured_request_log_example_matches_expected_fields() -> None:
    payload = json.loads(
        (PROJECT_ROOT / "docs" / "examples" / "structured_request_log.json").read_text(encoding="utf-8")
    )

    assert {
        "timestamp",
        "level",
        "logger",
        "service_id",
        "message",
        "event",
        "request_id",
        "http_method",
        "path",
        "status_code",
        "elapsed_ms",
    }.issubset(payload)
    assert payload["event"] == "http_request_completed"
    assert payload["logger"] == "historyguide.request"
    assert payload["service_id"] == "nk-historyguide-backend"
    assert payload["request_id"]
    assert isinstance(payload["status_code"], int)
    assert isinstance(payload["elapsed_ms"], float)
