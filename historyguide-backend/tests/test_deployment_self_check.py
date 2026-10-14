from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import pytest

from scripts import deployment_self_check


def test_build_headers_uses_operator_key_for_operator_checks() -> None:
    headers = deployment_self_check.build_headers(
        "business-secret",
        "operator-secret",
        operator=True,
    )

    assert headers == {"X-HistoryGuide-Operator-Key": "operator-secret"}


def test_build_headers_falls_back_to_business_key_when_no_operator_key() -> None:
    headers = deployment_self_check.build_headers(
        "business-secret",
        None,
        operator=True,
    )

    assert headers == {"X-HistoryGuide-Api-Key": "business-secret"}


def test_run_checks_reports_success_for_all_expected_read_only_endpoints(monkeypatch) -> None:
    seen_paths: list[str] = []

    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        path = "/" + request.full_url.split("/", 3)[3]
        seen_paths.append(path)
        payloads = {
            "/health": {"status": "ok", "service": "nk-historyguide-backend"},
            "/ready": {"status": "ready", "database": "ok"},
            "/api/system/database": {"backend": "sqlite", "persistence": "local_file"},
            "/openapi.json": {"paths": {"/health": {}}},
            "/api/system/access-policy": {"policies": [{"name": "operator_api"}]},
            "/api/system/security-status": {
                "business_api_key_configured": True,
                "operator_api_key_configured": True,
            },
            "/api/system/operational-alerts": {"status": "ok", "total_alerts": 0},
        }
        return _response(payloads[path])

    monkeypatch.setattr(deployment_self_check, "urlopen", fake_urlopen)

    results = deployment_self_check.run_checks(
        "http://testserver",
        api_key="business-secret",
        operator_key="operator-secret",
    )

    assert all(result.ok for result in results)
    assert seen_paths == [
        "/health",
        "/ready",
        "/api/system/database",
        "/openapi.json",
        "/api/system/access-policy",
        "/api/system/security-status",
        "/api/system/operational-alerts",
    ]
    assert [result.request_id for result in results] == [
        "self-check-request-id",
        "self-check-request-id",
        "self-check-request-id",
        "self-check-request-id",
        "self-check-request-id",
        "self-check-request-id",
        "self-check-request-id",
    ]


def test_operator_checks_send_operator_key_without_printing_secret(monkeypatch, capsys) -> None:
    captured_headers: list[dict[str, str]] = []

    def fake_urlopen(request: Any, timeout: float) -> Any:
        del timeout
        captured_headers.append(dict(request.header_items()))
        return _response({"status": "ok", "paths": {}, "total_alerts": 0})

    monkeypatch.setattr(deployment_self_check, "urlopen", fake_urlopen)

    exit_code = deployment_self_check.main(
        [
            "--base-url",
            "http://testserver",
            "--api-key",
            "business-secret",
            "--operator-key",
            "operator-secret",
        ]
    )

    assert exit_code == 0
    assert {"X-historyguide-operator-key": "operator-secret"} in captured_headers
    output = capsys.readouterr().out
    assert "request_id=self-check-request-id" in output
    assert "business-secret" not in output
    assert "operator-secret" not in output


@contextmanager
def _response(
    payload: dict[str, object],
    request_id: str | None = "self-check-request-id",
) -> Callable[[], bytes]:
    class Response:
        status = 200
        headers = (
            {deployment_self_check.REQUEST_ID_HEADER: request_id}
            if request_id is not None
            else {}
        )

        def read(self) -> bytes:
            import json

            return json.dumps(payload).encode("utf-8")

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    yield Response()
