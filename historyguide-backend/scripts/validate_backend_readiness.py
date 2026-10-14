from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


API_KEY_HEADER = "X-HistoryGuide-Api-Key"
OPERATOR_API_KEY_HEADER = "X-HistoryGuide-Operator-Key"
REQUEST_ID_HEADER = "X-HistoryGuide-Request-Id"


@dataclass(frozen=True)
class ValidationResult:
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


def run_validation(
    base_url: str,
    *,
    api_key: str | None = None,
    operator_key: str | None = None,
    session_id: str | None = None,
    timeout: float = 5.0,
    require_exhibits: bool = False,
    require_sourced_exhibits: bool = False,
    require_audit_logs: bool = False,
    require_clean_operational_alerts: bool = False,
    require_visit_events: bool = False,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    public_headers: dict[str, str] = {}
    business_headers = build_headers(api_key, operator_key)
    operator_headers = build_headers(api_key, operator_key, operator=True)

    results.append(
        _check_json_endpoint(
            base_url,
            "readiness",
            "/ready",
            headers=public_headers,
            timeout=timeout,
            validator=_validate_readiness,
        )
    )
    results.append(
        _check_json_endpoint(
            base_url,
            "database_status",
            "/api/system/database",
            headers=public_headers,
            timeout=timeout,
            validator=_validate_database_status,
        )
    )
    results.append(
        _check_json_endpoint(
            base_url,
            "operational_alerts",
            "/api/system/operational-alerts",
            headers=operator_headers,
            timeout=timeout,
            validator=lambda data: _validate_operational_alerts(
                data,
                require_clean=require_clean_operational_alerts,
            ),
        )
    )
    results.append(
        _check_json_endpoint(
            base_url,
            "exhibit_source_report",
            "/api/exhibits/source-report",
            headers=business_headers,
            timeout=timeout,
            validator=lambda data: _validate_source_report(
                data,
                require_exhibits=require_exhibits,
                require_sourced=require_sourced_exhibits,
            ),
        )
    )
    results.append(
        _check_json_endpoint(
            base_url,
            "exhibit_quality_report",
            "/api/exhibits/quality-report",
            headers=business_headers,
            timeout=timeout,
            validator=_validate_quality_report,
        )
    )
    results.append(
        _check_json_endpoint(
            base_url,
            "audit_log_stats",
            "/api/audit-logs/stats",
            headers=operator_headers,
            timeout=timeout,
            validator=lambda data: _validate_audit_stats(
                data,
                require_audit_logs=require_audit_logs,
            ),
        )
    )

    if session_id:
        session_path = _session_path(session_id)
        results.extend(
            [
                _check_json_endpoint(
                    base_url,
                    "visitor_state_integrity",
                    f"/api/visitor-states/{session_path}/integrity",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_visitor_integrity,
                ),
                _check_json_endpoint(
                    base_url,
                    "visit_events",
                    f"/api/visitor-states/{session_path}/visit-events",
                    headers=business_headers,
                    timeout=timeout,
                    validator=lambda data: _validate_visit_events(
                        data,
                        require_visit_events=require_visit_events,
                    ),
                ),
                _check_json_endpoint(
                    base_url,
                    "recommendations",
                    f"/api/recommendations/{session_path}",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_recommendations,
                ),
                _check_json_endpoint(
                    base_url,
                    "route_plan",
                    f"/api/visit-routes/{session_path}/plan",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_route_plan,
                ),
                _check_json_endpoint(
                    base_url,
                    "visit_summary",
                    f"/api/visits/{session_path}/summary",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_visit_summary,
                ),
                _check_json_endpoint(
                    base_url,
                    "genios_grounding",
                    f"/api/genios/grounding/{session_path}",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_genios_grounding,
                ),
                _check_json_endpoint(
                    base_url,
                    "genios_preflight",
                    f"/api/genios/preflight/{session_path}",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_genios_preflight,
                ),
                _check_json_endpoint(
                    base_url,
                    "genios_handoff",
                    f"/api/genios/handoff/{session_path}",
                    headers=business_headers,
                    timeout=timeout,
                    validator=_validate_genios_handoff,
                ),
            ]
        )

    return results


def _check_json_endpoint(
    base_url: str,
    name: str,
    path: str,
    *,
    headers: dict[str, str],
    timeout: float,
    validator: Callable[[Any], tuple[bool, str]],
) -> ValidationResult:
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
        return ValidationResult(
            name=name,
            path=path,
            ok=False,
            status_code=exc.code,
            detail=detail,
            request_id=request_id,
        )
    except URLError as exc:
        return ValidationResult(
            name=name,
            path=path,
            ok=False,
            status_code=None,
            detail=str(exc.reason),
            request_id=None,
        )
    except TimeoutError:
        return ValidationResult(
            name=name,
            path=path,
            ok=False,
            status_code=None,
            detail="request timed out",
            request_id=None,
        )

    if status_code != 200:
        return ValidationResult(
            name=name,
            path=path,
            ok=False,
            status_code=status_code,
            detail="expected HTTP 200",
            request_id=request_id,
        )

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return ValidationResult(
            name=name,
            path=path,
            ok=False,
            status_code=status_code,
            detail="expected JSON response",
            request_id=request_id,
        )

    ok, detail = validator(data)
    return ValidationResult(
        name=name,
        path=path,
        ok=ok,
        status_code=status_code,
        detail=detail,
        request_id=request_id,
    )


def _validate_readiness(data: dict[str, Any]) -> tuple[bool, str]:
    status_value = data.get("status")
    database = data.get("database")
    ok = status_value == "ready" and database == "ok"
    return ok, f"status={status_value}, database={database}"


def _validate_database_status(data: dict[str, Any]) -> tuple[bool, str]:
    backend = data.get("backend")
    persistence = data.get("persistence")
    schema_management = data.get("schema_management")
    return True, f"backend={backend}, persistence={persistence}, schema_management={schema_management}"


def _validate_operational_alerts(data: dict[str, Any], *, require_clean: bool) -> tuple[bool, str]:
    status_value = data.get("status")
    fail_count = _int_value(data.get("fail_count"))
    warn_count = _int_value(data.get("warn_count"))
    ok = fail_count == 0 if require_clean else True
    return ok, f"status={status_value}, fail_count={fail_count}, warn_count={warn_count}"


def _validate_source_report(
    data: dict[str, Any],
    *,
    require_exhibits: bool,
    require_sourced: bool,
) -> tuple[bool, str]:
    total = _int_value(data.get("total"))
    sourced_count = _int_value(data.get("sourced_count"))
    unsourced_count = _int_value(data.get("unsourced_count"))
    ok = True
    if require_exhibits and total <= 0:
        ok = False
    if require_sourced and unsourced_count != 0:
        ok = False
    return ok, f"total={total}, sourced={sourced_count}, unsourced={unsourced_count}"


def _validate_quality_report(data: dict[str, Any]) -> tuple[bool, str]:
    total = _int_value(data.get("total"))
    coverage = data.get("source_reference_coverage_percent")
    issues = data.get("issues")
    issue_count = len(issues) if isinstance(issues, list) else "unknown"
    return True, f"total={total}, source_reference_coverage_percent={coverage}, issue_groups={issue_count}"


def _validate_audit_stats(data: dict[str, Any], *, require_audit_logs: bool) -> tuple[bool, str]:
    total_logs = _int_value(data.get("total_logs"))
    ok = total_logs > 0 if require_audit_logs else True
    return ok, f"total_logs={total_logs}, latest_created_at={data.get('latest_created_at')}"


def _validate_visitor_integrity(data: dict[str, Any]) -> tuple[bool, str]:
    issue_count = _int_value(data.get("issue_count"))
    return issue_count == 0, f"issue_count={issue_count}"


def _validate_visit_events(data: Any, *, require_visit_events: bool) -> tuple[bool, str]:
    if isinstance(data, list):
        visit_event_count = len(data)
    elif isinstance(data, dict):
        events = data.get("visit_events", [])
        visit_event_count = len(events) if isinstance(events, list) else 0
    else:
        visit_event_count = 0
    ok = visit_event_count > 0 if require_visit_events else True
    return ok, f"visit_event_count={visit_event_count}"


def _validate_recommendations(data: dict[str, Any]) -> tuple[bool, str]:
    recommendations = data if isinstance(data, list) else data.get("recommendations", [])
    count = len(recommendations) if isinstance(recommendations, list) else "unknown"
    return True, f"recommendation_count={count}"


def _validate_route_plan(data: dict[str, Any]) -> tuple[bool, str]:
    items = data.get("items", [])
    item_count = len(items) if isinstance(items, list) else "unknown"
    return True, f"planned_minutes={data.get('planned_minutes')}, item_count={item_count}"


def _validate_visit_summary(data: dict[str, Any]) -> tuple[bool, str]:
    return True, f"visited_count={data.get('visited_count')}, missing_exhibit_ids={data.get('missing_exhibit_ids')}"


def _validate_genios_grounding(data: dict[str, Any]) -> tuple[bool, str]:
    complete = data.get("grounding_sources_complete")
    missing = data.get("missing_exhibit_ids")
    unsourced = data.get("unsourced_exhibit_ids")
    ok = complete is True and missing == [] and unsourced == []
    return ok, (
        f"grounding_sources_complete={complete}, "
        f"missing_exhibit_ids={missing}, unsourced_exhibit_ids={unsourced}"
    )


def _validate_genios_preflight(data: dict[str, Any]) -> tuple[bool, str]:
    ready = data.get("ready_for_handoff")
    checks = data.get("checks")
    blocking = [
        check.get("name")
        for check in checks
        if isinstance(check, dict) and check.get("status") == "fail"
    ] if isinstance(checks, list) else []
    return ready is True, f"ready_for_handoff={ready}, blocking_checks={blocking}"


def _validate_genios_handoff(data: dict[str, Any]) -> tuple[bool, str]:
    source_safety = data.get("source_safety", {})
    if not isinstance(source_safety, dict):
        return False, "missing source_safety object"
    ready = source_safety.get("ready_for_generation")
    complete = source_safety.get("grounding_sources_complete")
    blocking = source_safety.get("blocking_check_names")
    ok = ready is True and complete is True and blocking == []
    return ok, (
        f"source_safety.ready_for_generation={ready}, "
        f"grounding_sources_complete={complete}, blocking_check_names={blocking}"
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


def _normalized_base_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/"


def _session_path(session_id: str) -> str:
    return session_id.strip("/")


def _int_value(value: Any) -> int:
    return value if isinstance(value, int) else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run stronger read-only backend readiness validation against a running NK HistoryGuide backend. "
            "The script does not write to the database, does not run RAG, does not generate explanation content, "
            "does not print key values, and never prints configured key values."
        )
    )
    parser.add_argument("--base-url", default=os.getenv("HISTORYGUIDE_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--api-key", default=os.getenv("HISTORYGUIDE_API_KEY"))
    parser.add_argument("--operator-key", default=os.getenv("HISTORYGUIDE_OPERATOR_API_KEY"))
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--require-exhibits", action="store_true")
    parser.add_argument("--require-sourced-exhibits", action="store_true")
    parser.add_argument("--require-audit-logs", action="store_true")
    parser.add_argument("--require-clean-operational-alerts", action="store_true")
    parser.add_argument("--require-visit-events", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = run_validation(
        args.base_url,
        api_key=args.api_key,
        operator_key=args.operator_key,
        session_id=args.session_id,
        timeout=args.timeout,
        require_exhibits=args.require_exhibits,
        require_sourced_exhibits=args.require_sourced_exhibits,
        require_audit_logs=args.require_audit_logs,
        require_clean_operational_alerts=args.require_clean_operational_alerts,
        require_visit_events=args.require_visit_events,
    )

    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        status = result.status_code if result.status_code is not None else "n/a"
        request_id = result.request_id or "n/a"
        print(
            f"[{marker}] {result.name} {result.path} "
            f"status={status} request_id={request_id} {result.detail}"
        )

    print(
        "Boundary: read-only backend validation only; does not write to the database, "
        "does not validate historical accuracy, does not run RAG, and does not generate explanation content."
    )
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
