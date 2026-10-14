# Centralized Logging

This document describes how to collect NK HistoryGuide request logs in a centralized logging platform during staging or production-like deployment.

## Boundary

Centralized request logs are operational metadata only. They help operators correlate Web/H5, GeniOS, deployment self-check, and backend events.

Structured request logs are not authentication, not historical evidence, and not GeniOS prompt input.

They are also not:

- authentication
- visitor identity
- visitor profile data
- historical evidence
- source references
- GeniOS prompt input
- RAG content
- generated explanation content

The backend does not train models, run RAG, or generate explanation content through logging.

## Enable JSON Logs

Set:

```text
HISTORYGUIDE_LOG_FORMAT=json
HISTORYGUIDE_LOG_LEVEL=INFO
```

Then run the backend normally:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Stable Fields

Every request completion log should include:

- `timestamp`
- `level`
- `logger`
- `service_id`
- `message`
- `event`
- `request_id`
- `http_method`
- `path`
- `status_code`
- `elapsed_ms`

Example:

```json
{
  "timestamp": "2026-09-25T12:00:00+00:00",
  "level": "INFO",
  "logger": "historyguide.request",
  "service_id": "nk-historyguide-backend",
  "message": "request completed request_id=demo-request-001 method=GET path=/api/genios/context/demo-session-001 status_code=200 elapsed_ms=12.34",
  "event": "http_request_completed",
  "request_id": "demo-request-001",
  "http_method": "GET",
  "path": "/api/genios/context/demo-session-001",
  "status_code": 200,
  "elapsed_ms": 12.34
}
```

The same example is stored at `docs/examples/structured_request_log.json`.

## Correlation Flow

Use `X-HistoryGuide-Request-Id` as the correlation id:

- Web/H5 may send `X-HistoryGuide-Request-Id` when creating or updating Visitor State.
- GeniOS may send `X-HistoryGuide-Request-Id` when requesting context, grounding, preflight, or handoff.
- `scripts\deployment_self_check.py` prints returned request ids for every read-only endpoint check.
- Backend JSON request logs include the same value in `request_id`.

If the caller omits the header or sends an invalid value, the backend generates a valid request id and returns it in the response.

## Suggested Filters

Useful staging filters:

- `event = "http_request_completed"`
- `service_id = "nk-historyguide-backend"`
- `status_code >= 500`
- `status_code = 401`
- `path starts with "/api/genios/"`
- `path starts with "/api/system/"`
- `elapsed_ms > 1000`

Useful demo or museum-site checks:

- repeated `401` from expected Web/H5 or GeniOS clients
- repeated `5xx`
- slow GeniOS context, grounding, preflight, or handoff calls
- failed operator access to audit logs, operational alerts, security status, or access policy
- deployment self-check request ids that do not appear in backend logs

Use `docs/monitoring_alert_examples.md` for production-like alert rule examples that combine structured request logs with `GET /api/system/operational-alerts`, source-safety fields, Visitor State integrity checks, and GeniOS handoff readiness.

## Redaction

Do not add secret values to request logs.

Never log:

- `HISTORYGUIDE_API_KEY`
- `HISTORYGUIDE_OPERATOR_API_KEY`
- `X-HistoryGuide-Api-Key`
- `X-HistoryGuide-Operator-Key`
- raw source packages
- unreviewed historical content
- generated explanation text

## Related Checks

Before relying on centralized logs:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Use `GET /api/system/access-policy` to confirm coarse access boundaries and `GET /api/system/security-status` to confirm key controls. Neither endpoint returns configured key values.
