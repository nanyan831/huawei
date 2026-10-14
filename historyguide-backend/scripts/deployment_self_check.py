from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


API_KEY_HEADER = "X-HistoryGuide-Api-Key"
OPERATOR_API_KEY_HEADER = "X-HistoryGuide-Operator-Key"
REQUEST_ID_HEADER = "X-HistoryGuide-Request-Id"

PUBLIC_CHECKS = (
    ("health", "/health"),
    ("readiness", "/ready"),
    ("database_status", "/api/system/database"),
    ("openapi", "/openapi.json"),
)
OPERATOR_CHECKS = (
    ("access_policy", "/api/system/access-policy"),
    ("security_status", "/api/system/security-status"),
    ("operational_alerts", "/api/system/operational-alerts"),
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    path: str
    ok: bool
    status_code: int | None
    detail: str
    request_id: str | None


def build_headers(api_key: str | None, operator_key: str | None, *, operator: bool = False) -> dict[str, str]:
    if operator and operator_key:
        return {OPERATOR_API_KEY_HEADER: operator_key}
    if api_key:
        return {API_KEY_HEADER: api_key}
    return {}


def run_checks(
    base_url: str,
    *,
    api_key: str | None = None,
    operator_key: str | None = None,
    timeout: float = 5.0,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    for name, path in PUBLIC_CHECKS:
        results.append(_check_endpoint(base_url, name, path, headers={}, timeout=timeout))

    for name, path in OPERATOR_CHECKS:
        headers = build_headers(api_key, operator_key, operator=True)
        results.append(_check_endpoint(base_url, name, path, headers=headers, timeout=timeout))

    return results


def _check_endpoint(
    base_url: str,
    name: str,
    path: str,
    *,
    headers: dict[str, str],
    timeout: float,
) -> CheckResult:
    url = urljoin(_normalized_base_url(base_url), path.lstrip("/"))
    request = Request(url, headers=headers, method="GET")

    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = response.status
            request_id = response.headers.get(REQUEST_ID_HEADER)
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = _safe_error_detail(exc)
        request_id = exc.headers.get(REQUEST_ID_HEADER) if exc.headers else None
        return CheckResult(
            name=name,
            path=path,
            ok=False,
            status_code=exc.code,
            detail=detail,
            request_id=request_id,
        )
    except URLError as exc:
        return CheckResult(
            name=name,
            path=path,
            ok=False,
            status_code=None,
            detail=str(exc.reason),
            request_id=None,
        )
    except TimeoutError:
        return CheckResult(
            name=name,
            path=path,
            ok=False,
            status_code=None,
            detail="request timed out",
            request_id=None,
        )

    if status_code != 200:
        return CheckResult(
            name=name,
            path=path,
            ok=False,
            status_code=status_code,
            detail="expected HTTP 200",
            request_id=request_id,
        )

    detail = _summarize_payload(name, payload)
    return CheckResult(
        name=name,
        path=path,
        ok=True,
        status_code=status_code,
        detail=detail,
        request_id=request_id,
    )


def _safe_error_detail(exc: HTTPError) -> str:
    try:
        payload = exc.read().decode("utf-8")
    except Exception:
        payload = ""
    if not payload:
        return exc.reason
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return payload[:200]
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail
    return payload[:200]


def _summarize_payload(name: str, payload: str) -> str:
    try:
        data: Any = json.loads(payload)
    except json.JSONDecodeError:
        return "received non-JSON response"

    if name == "health":
        return f"status={data.get('status')}, service={data.get('service')}"
    if name == "readiness":
        return f"status={data.get('status')}, database={data.get('database')}"
    if name == "database_status":
        return f"backend={data.get('backend')}, persistence={data.get('persistence')}"
    if name == "security_status":
        return (
            "business_key_configured="
            f"{data.get('business_api_key_configured')}, "
            "operator_key_configured="
            f"{data.get('operator_api_key_configured')}"
        )
    if name == "access_policy":
        policies = data.get("policies", [])
        return f"policies={len(policies) if isinstance(policies, list) else 'unknown'}"
    if name == "operational_alerts":
        return f"status={data.get('status')}, total_alerts={data.get('total_alerts')}"
    if name == "openapi":
        paths = data.get("paths", {})
        return f"paths={len(paths) if isinstance(paths, dict) else 'unknown'}"
    return "ok"


def _normalized_base_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run read-only deployment checks against a running NK HistoryGuide backend. "
            "The script does not write to the database and never prints configured key values."
        )
    )
    parser.add_argument("--base-url", default=os.getenv("HISTORYGUIDE_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--api-key", default=os.getenv("HISTORYGUIDE_API_KEY"))
    parser.add_argument("--operator-key", default=os.getenv("HISTORYGUIDE_OPERATOR_API_KEY"))
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = run_checks(
        args.base_url,
        api_key=args.api_key,
        operator_key=args.operator_key,
        timeout=args.timeout,
    )

    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        status = result.status_code if result.status_code is not None else "n/a"
        request_id = result.request_id or "n/a"
        print(
            f"[{marker}] {result.name} {result.path} "
            f"status={status} request_id={request_id} {result.detail}"
        )

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
