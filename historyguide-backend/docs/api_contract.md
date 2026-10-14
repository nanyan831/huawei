# API Contract

This document describes the NK HistoryGuide backend API surface for Web/H5 and GeniOS integration.

The backend provides structured exhibit data, Visitor State, recommendation candidates, and GeniOS context packages. It does not generate museum explanation text and does not call large language models.

Base URL for local development:

```text
http://127.0.0.1:8000
```

## Request Id

Every response includes:

```http
X-HistoryGuide-Request-Id: <request-id>
```

Web/H5, GeniOS, or operator tooling may send `X-HistoryGuide-Request-Id` to correlate client logs, backend request logs, and error reports. Accepted request ids use letters, numbers, `.`, `_`, or `-`, up to 128 characters. If the header is missing or invalid, the backend generates a request id and returns it in the response.

The request id is for troubleshooting only. It is not authentication, an API key, visitor identity, visitor profile, historical source reference, historical evidence, or GeniOS prompt input.

## Optional API Key

By default, local development does not require an API key.

When `HISTORYGUIDE_API_KEY` is configured, business APIs require this request header:

```http
X-HistoryGuide-Api-Key: <configured-api-key>
```

When `HISTORYGUIDE_OPERATOR_API_KEY` is configured, operator APIs require this request header:

```http
X-HistoryGuide-Operator-Key: <configured-operator-api-key>
```

Operator APIs include:

- `GET /api/audit-logs`
- `GET /api/audit-logs/stats`
- `GET /api/system/operational-alerts`
- `GET /api/system/security-status`

If both keys are configured, operator APIs require `X-HistoryGuide-Operator-Key`; ordinary business APIs require `X-HistoryGuide-Api-Key`.

Public deployment probe paths remain available without the header:

- `GET /health`
- `GET /ready`
- `GET /api/system/database`
- `GET /openapi.json`
- `GET /docs`

Missing or invalid key response:

```json
{
  "detail": "Valid HistoryGuide API key is required."
}
```

Missing or invalid operator key response:

```json
{
  "detail": "Valid HistoryGuide operator API key is required."
}
```

## Health

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "nk-historyguide-backend",
  "version": "0.1.0"
}
```

## Readiness

```http
GET /ready
```

Response:

```json
{
  "status": "ready",
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "database": "ok"
}
```

This endpoint performs a lightweight database check for deployment readiness. It does not validate GeniOS availability or generated content.

## Database Status

```http
GET /api/system/database
```

Response:

```json
{
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "backend": "sqlite",
  "driver": "sqlite",
  "persistence": "local_file",
  "schema_management": "sqlalchemy_create_all_mvp_with_alembic_scaffold",
  "migration_target": "alembic_staging_then_postgresql",
  "production_note": "SQLite is the verified MVP backend. Alembic migration scaffolding is available, but production PostgreSQL still requires staging migration validation and verified exhibit backups."
}
```

This endpoint reports database backend status for deployment checks and migration planning. It does not expose the full database URL and does not perform schema migrations. See `docs/database_migrations.md` for the Alembic scaffold boundary and staging gate.

## Operational Alerts

Read backend operational alerts:

```http
GET /api/system/operational-alerts
```

Response:

```json
{
  "status": "attention_required",
  "total_alerts": 2,
  "fail_count": 1,
  "warn_count": 1,
  "alerts": [
    {
      "name": "unsourced_exhibits",
      "severity": "fail",
      "resource_type": "exhibit",
      "count": 1,
      "detail": "Some exhibit records do not have source_reference values."
    }
  ]
}
```

The endpoint summarizes backend readiness signals for demos, staging checks, and operations handoff. It can report empty exhibit data, unsourced exhibits, exhibit metadata gaps, Visitor State timeline drift, and missing audit evidence. It does not inspect historical accuracy, infer visitor profiles, retrieve RAG passages, or generate explanation content.

## Security Status

Read deployment security configuration status:

```http
GET /api/system/security-status
```

Response:

```json
{
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "business_api_key_configured": true,
  "operator_api_key_configured": true,
  "business_apis_require_api_key": true,
  "operator_apis_require_operator_key": true,
  "business_api_key_header": "X-HistoryGuide-Api-Key",
  "operator_api_key_header": "X-HistoryGuide-Operator-Key",
  "public_probe_paths": ["/api/system/database", "/docs", "/docs/oauth2-redirect", "/health", "/openapi.json", "/ready", "/redoc"],
  "operator_paths": ["/api/system/access-policy", "/api/system/operational-alerts", "/api/system/security-status"],
  "operator_path_prefixes": ["/api/audit-logs"],
  "production_note": "This endpoint reports whether optional API key controls are configured. It never returns configured key values and is not a replacement for full RBAC."
}
```

This endpoint is for deployment and operator verification before demos, staging checks, Web/H5 integration, or GeniOS handoff. It reports booleans and path/header names only; it never returns configured key values, does not implement full role-based access control, and does not generate explanation content.

## Access Policy

Read coarse backend access boundaries:

```http
GET /api/system/access-policy
```

Response:

```json
{
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "policies": [
    {
      "name": "public_probe",
      "access_level": "public",
      "required_header": null,
      "paths": ["/health", "/ready", "/api/system/database", "/openapi.json"],
      "path_prefixes": [],
      "notes": "Deployment probes and API documentation remain public when API key protection is enabled."
    },
    {
      "name": "business_api",
      "access_level": "business_api_key",
      "required_header": "X-HistoryGuide-Api-Key",
      "paths": [],
      "path_prefixes": ["/api"],
      "notes": "Ordinary backend APIs use the business API key when configured. Operator paths are excluded."
    },
    {
      "name": "operator_api",
      "access_level": "operator_api_key",
      "required_header": "X-HistoryGuide-Operator-Key",
      "paths": ["/api/system/access-policy", "/api/system/operational-alerts", "/api/system/security-status"],
      "path_prefixes": ["/api/audit-logs"],
      "notes": "Operator endpoints expose operational metadata and never return configured key values."
    },
    {
      "name": "local_operator_workflow",
      "access_level": "local_operator_workflow",
      "required_header": null,
      "paths": [],
      "path_prefixes": ["scripts/"],
      "notes": "Operator scripts are local workflows, not public HTTP APIs."
    }
  ],
  "production_note": "This endpoint documents current coarse access boundaries for deployment and integration checks. It does not implement user accounts, per-person authorization, or full RBAC."
}
```

When `HISTORYGUIDE_OPERATOR_API_KEY` is configured, this endpoint requires `X-HistoryGuide-Operator-Key`. It never returns configured key values, does not grant access, does not infer visitor profiles, and does not generate explanation content.

## Exhibits

List exhibits:

```http
GET /api/exhibits
```

Optional filters:

```http
GET /api/exhibits?keyword=fixture
GET /api/exhibits?period=fixture-period
GET /api/exhibits?importance_min=3
GET /api/exhibits?limit=20&offset=0
```

Pagination:

- `limit`: optional, 1 to 200
- `offset`: optional, defaults to 0

Response:

```json
[
  {
    "id": "fixture-exhibit-002",
    "name": "Fixture Exhibit Two",
    "description": "Second non-historical development fixture for recommendation flow checks.",
    "period": "fixture-period",
    "keywords": ["fixture", "recommendation"],
    "importance": 4,
    "people": [],
    "time_range": null,
    "themes": ["development"],
    "source_reference": "Development fixture only. Replace with verified museum source before production use."
  }
]
```

Read exhibit metadata facets:

```http
GET /api/exhibits/facets
```

Response:

```json
{
  "total": 2,
  "periods": [
    {
      "value": "fixture-period",
      "count": 2
    }
  ],
  "keywords": [
    {
      "value": "fixture",
      "count": 2
    }
  ],
  "people": [],
  "themes": [
    {
      "value": "development",
      "count": 2
    }
  ]
}
```

Facets are derived from structured exhibit metadata. They are intended for Web/H5 filters, data review, and GeniOS integration setup. They do not generate historical content.

Read exhibit quality report:

```http
GET /api/exhibits/quality-report
```

Response:

```json
{
  "total": 2,
  "source_reference_coverage_percent": 100.0,
  "importance_distribution": [
    {
      "value": "3",
      "count": 1
    }
  ],
  "issues": [
    {
      "issue": "missing_source_reference",
      "count": 0,
      "exhibit_ids": []
    },
    {
      "issue": "empty_keywords",
      "count": 0,
      "exhibit_ids": []
    },
    {
      "issue": "empty_themes",
      "count": 0,
      "exhibit_ids": []
    },
    {
      "issue": "empty_people",
      "count": 2,
      "exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"]
    }
  ]
}
```

The quality report checks structured metadata completeness for source references, keywords, themes, people, and importance distribution. It does not verify historical accuracy, generate missing content, or replace source review.

Read exhibit source report:

```http
GET /api/exhibits/source-report
```

Response:

```json
{
  "total": 2,
  "sourced_count": 2,
  "unsourced_count": 0,
  "unsourced_exhibit_ids": [],
  "source_references": [
    {
      "source_reference": "Development fixture only. Replace with verified museum source before production use.",
      "count": 2,
      "exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"]
    }
  ]
}
```

The source report groups exhibits by exact `source_reference` values and lists records without a source reference. It supports verified data batch review and GeniOS grounding setup. It does not judge source quality, verify historical accuracy, or generate missing source text.

Read one exhibit:

```http
GET /api/exhibits/{exhibit_id}
```

Missing exhibit response:

```json
{
  "detail": "Exhibit 'missing-exhibit' was not found."
}
```

## Audit Logs

Read structured operation logs:

```http
GET /api/audit-logs/stats
GET /api/audit-logs?action=visit_event_recorded&limit=20&offset=0
GET /api/audit-logs?resource_type=visitor_state&resource_id=demo-session-001
```

Optional query parameters:

- `action`: exact audit action, such as `visitor_state_created`, `visitor_state_updated`, `visit_event_recorded`, or `exhibits_imported`
- `resource_type`: exact resource type, such as `visitor_state` or `exhibit_import`
- `resource_id`: exact resource id, such as a Visitor State `session_id`
- `actor`: exact actor, such as `api` or `import_cli`
- `limit`: optional, 1 to 200
- `offset`: optional, defaults to 0

Response:

```json
[
  {
    "id": 3,
    "action": "visit_event_recorded",
    "resource_type": "visitor_state",
    "resource_id": "demo-session-001",
    "actor": "api",
    "details": {
      "exhibit_id": "fixture-exhibit-002",
      "remaining_time": 18,
      "visited_count": 2
    },
    "created_at": "2026-09-25T09:00:00"
  }
]
```

Audit logs support operator traceability for real visit state changes and exhibit seed imports. They do not infer visitor profiles, verify historical accuracy, retrieve RAG passages, or generate explanation content.

Read audit log stats:

```http
GET /api/audit-logs/stats
```

Response:

```json
{
  "total_logs": 3,
  "actions": [
    {
      "value": "visit_event_recorded",
      "count": 1
    }
  ],
  "resource_types": [
    {
      "value": "visitor_state",
      "count": 3
    }
  ],
  "actors": [
    {
      "value": "api",
      "count": 3
    }
  ],
  "latest_created_at": "2026-09-25T09:00:00"
}
```

The stats endpoint is a lightweight operational summary for demos, staging checks, and monitoring handoff. It does not inspect historical exhibit facts or generate explanation content.

## Visitor State

Create a visit session:

```http
POST /api/visitor-states
Content-Type: application/json
```

Request:

```json
{
  "session_id": "demo-session-001",
  "visitor_type": "tourist",
  "current_exhibit": "fixture-exhibit-001",
  "visited_history": ["fixture-exhibit-001"],
  "interest": ["recommendation"],
  "remaining_time": 25
}
```

Visitor types:

```text
freshman
alumnus
tourist
```

Response:

```json
{
  "visitor_type": "tourist",
  "current_exhibit": "fixture-exhibit-001",
  "visited_history": ["fixture-exhibit-001"],
  "interest": ["recommendation"],
  "remaining_time": 25,
  "session_id": "demo-session-001"
}
```

Read a visit session:

```http
GET /api/visitor-states/{session_id}
```

List visit sessions:

```http
GET /api/visitor-states?visitor_type=tourist&limit=20&offset=0
```

Optional query parameters:

- `visitor_type`: `freshman`, `alumnus`, or `tourist`
- `limit`: optional, 1 to 200
- `offset`: optional, defaults to 0

The list endpoint is for structured session review, Web/H5 recovery flows, and local integration checks. It does not infer visitor profiles beyond stored `visitor_type`.

Read Visitor State stats:

```http
GET /api/visitor-states/stats
```

Response:

```json
{
  "total_sessions": 8,
  "visitor_types": [
    {
      "value": "tourist",
      "count": 7
    }
  ],
  "current_exhibits": [
    {
      "value": "fixture-exhibit-001",
      "count": 4
    }
  ],
  "interests": [
    {
      "value": "recommendation",
      "count": 5
    }
  ],
  "no_current_exhibit_count": 3,
  "remaining_time": {
    "min": 18,
    "max": 25,
    "average": 20.75
  }
}
```

Stats are aggregated from stored Visitor State records. They are intended for local demos, integration checks, and lightweight operational visibility. They do not infer visitor profiles or generate explanation content.

Read Visitor State integrity report:

```http
GET /api/visitor-states/integrity-report
```

Read one visit session integrity report:

```http
GET /api/visitor-states/{session_id}/integrity
```

Response:

```json
{
  "total_sessions": 1,
  "total_visit_events": 1,
  "sessions_with_visit_events": 1,
  "issue_count": 0,
  "issues": []
}
```

The global integrity report compares Visitor State snapshots with visit-event timelines across stored sessions. The per-session integrity endpoint applies the same checks to one active visit session and returns `404` when the session does not exist. Both endpoints flag structural drift such as a latest event that differs from `current_exhibit`, event exhibits missing from `visited_history`, or `visited_history` without timeline events. They do not infer visitor intent or generate explanation content.

Update a visit session:

```http
PATCH /api/visitor-states/{session_id}
Content-Type: application/json
```

Request:

```json
{
  "current_exhibit": "fixture-exhibit-002",
  "visited_history": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "remaining_time": 15
}
```

The backend validates exhibit ids in `current_exhibit` and `visited_history`.

Record a real visit event:

```http
POST /api/visitor-states/{session_id}/visit-events
Content-Type: application/json
```

Request:

```json
{
  "exhibit_id": "fixture-exhibit-002",
  "remaining_time": 18
}
```

Response:

```json
{
  "visitor_type": "tourist",
  "current_exhibit": "fixture-exhibit-002",
  "visited_history": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "interest": ["recommendation"],
  "remaining_time": 18,
  "session_id": "demo-session-001"
}
```

Visit event behavior:

- validates that the exhibit exists
- sets `current_exhibit` to the event exhibit
- appends the exhibit to `visited_history` only once
- updates `remaining_time` when provided
- stores a timestamped event row for timeline review
- does not generate explanation text

Read recorded visit events:

```http
GET /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/visit-events?limit=20&offset=0
```

Optional query parameters:

- `limit`: optional, 1 to 200
- `offset`: optional, defaults to 0

Response:

```json
[
  {
    "id": 1,
    "session_id": "demo-session-001",
    "exhibit_id": "fixture-exhibit-002",
    "remaining_time": 18,
    "event_time": "2026-09-22T14:26:00"
  }
]
```

The visit-event timeline is structured state history for Web/H5 and GeniOS. It is ordered by event time and id, and pagination is applied after that stable ordering. It does not infer visitor intent, generate behavioral profiles, or produce explanation content.

## Recommendations

Read recommendation candidates:

```http
GET /api/recommendations/{session_id}?limit=3
```

Response:

```json
[
  {
    "exhibit_id": "fixture-exhibit-002",
    "name": "Fixture Exhibit Two",
    "reason": "importance level 4; matches interests: recommendation; not yet visited",
    "priority": 1
  }
]
```

Recommendation behavior:

- excludes the current exhibit
- excludes visited exhibits
- uses visitor type, remaining time, interest, and exhibit metadata
- returns structured recommendation reasons only
- does not generate explanation text

## Visit Route Plan

Read a rule-based visit route plan:

```http
GET /api/visit-routes/{session_id}/plan?max_items=5
```

Response:

```json
{
  "session_id": "demo-session-001",
  "remaining_time": 25,
  "planned_minutes": 7,
  "items": [
    {
      "order": 1,
      "exhibit_id": "fixture-exhibit-002",
      "name": "Fixture Exhibit Two",
      "estimated_minutes": 7,
      "reason": "importance level 4; matches interests: recommendation; continues the current exhibit context; not yet visited"
    }
  ],
  "planning_note": "Rule-based route plan using unvisited exhibits, visitor interests, and remaining time. It does not perform map navigation or generated explanation."
}
```

Route plan behavior:

- uses recommendation candidates as the source of route items
- excludes current and visited exhibits through the recommendation service
- fits selected exhibits within `remaining_time`
- estimates exhibit duration from structured importance metadata
- returns structured route items only
- does not perform indoor map navigation or generate explanation text

## GeniOS Capabilities

Read backend collaboration capabilities:

```http
GET /api/genios/capabilities
```

Response top-level fields:

- `service_id`
- `version`
- `collaboration_contract`
- `supported_visitor_types`
- `primary_workflow`
- `endpoints`
- `integration_notes`

This endpoint is a structured discovery document for GeniOS or Web/H5 integration. It describes the backend role, GeniOS role, generation boundary, supported visitor types, and relevant backend endpoints. It does not inspect a session and does not generate explanation content.

## GeniOS Context

Read a structured context package:

```http
GET /api/genios/context/{session_id}?recommendation_limit=3
```

Response:

```json
{
  "session_id": "demo-session-001",
  "visitor_state": {
    "visitor_type": "tourist",
    "current_exhibit": "fixture-exhibit-001",
    "visited_history": ["fixture-exhibit-001"],
    "interest": ["recommendation"],
    "remaining_time": 25,
    "session_id": "demo-session-001"
  },
  "current_exhibit": {
    "id": "fixture-exhibit-001",
    "name": "Fixture Exhibit One",
    "description": "Non-historical development fixture for validating import and API behavior.",
    "period": "fixture-period",
    "keywords": ["fixture", "context"],
    "importance": 3,
    "people": [],
    "time_range": null,
    "themes": ["development"],
    "source_reference": "Development fixture only. Replace with verified museum source before production use."
  },
  "visited_exhibits": [],
  "visit_events": [
    {
      "id": 1,
      "session_id": "demo-session-001",
      "exhibit_id": "fixture-exhibit-002",
      "remaining_time": 18,
      "event_time": "2026-09-22T14:26:00"
    }
  ],
  "recommendations": [
    {
      "exhibit_id": "fixture-exhibit-002",
      "name": "Fixture Exhibit Two",
      "reason": "importance level 4; matches interests: recommendation; not yet visited",
      "priority": 1
    }
  ],
  "grounding_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "missing_exhibit_ids": [],
  "collaboration_contract": {
    "backend_role": "Provide structured visit context, exhibit data, visitor state, and recommendation candidates.",
    "genios_role": "Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content.",
    "generation_boundary": "The backend does not generate museum explanation text or call large language models."
  }
}
```

GeniOS should use this package as structured input for dialogue, RAG retrieval, grounding, visit-continuity awareness, and personalized explanation generation. `grounding_exhibit_ids` is an ordered, de-duplicated list of known exhibit ids from the current exhibit, visited history, and recommendation candidates. It is intended as exhibit-level RAG input and does not contain generated historical content.

## GeniOS Grounding

Read a structured grounding package for exhibit-level RAG preparation:

```http
GET /api/genios/grounding/{session_id}?recommendation_limit=3
```

Response:

```json
{
  "session_id": "demo-session-001",
  "grounding_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "exhibits": [
    {
      "id": "fixture-exhibit-001",
      "name": "Fixture Exhibit One",
      "description": "Non-historical development fixture for validating import and API behavior.",
      "period": "fixture-period",
      "keywords": ["fixture", "context"],
      "importance": 3,
      "people": [],
      "time_range": null,
      "themes": ["development"],
      "source_reference": "Development fixture only. Replace with verified museum source before production use."
    }
  ],
  "source_references": [
    "Development fixture only. Replace with verified museum source before production use."
  ],
  "source_reference_count": 1,
  "sourced_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "unsourced_exhibit_ids": [],
  "grounding_sources_complete": true,
  "missing_exhibit_ids": [],
  "collaboration_contract": {
    "backend_role": "Provide structured visit context, exhibit data, visitor state, and recommendation candidates.",
    "genios_role": "Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content.",
    "generation_boundary": "The backend does not generate museum explanation text or call large language models."
  }
}
```

The grounding package resolves `grounding_exhibit_ids` to structured exhibit records and source references. It also reports `sourced_exhibit_ids`, `unsourced_exhibit_ids`, `source_reference_count`, and `grounding_sources_complete` so GeniOS can refuse or delay generated explanation when grounding records lack source references. It is intended to help GeniOS prepare exhibit-level RAG retrieval. It does not retrieve knowledge-base passages, judge historical accuracy, or generate explanation content.

## GeniOS Preflight

Read a structured preflight package before GeniOS handoff:

```http
GET /api/genios/preflight/{session_id}?recommendation_limit=3
```

Response:

```json
{
  "session_id": "demo-session-001",
  "ready_for_handoff": true,
  "checks": [
    {
      "name": "exhibit_references",
      "status": "pass",
      "detail": "Current and visited exhibit references resolve to known exhibit records."
    },
    {
      "name": "grounding_source_references",
      "status": "pass",
      "detail": "Grounding exhibit records include source_reference values."
    },
    {
      "name": "visitor_state_integrity",
      "status": "pass",
      "detail": "Visitor State snapshot and visit-event timeline are structurally aligned."
    },
    {
      "name": "visit_event_timeline",
      "status": "pass",
      "detail": "Visit-event timeline is available for continuity."
    },
    {
      "name": "recommendations",
      "status": "pass",
      "detail": "Recommendation candidates are available for route-aware dialogue."
    }
  ],
  "missing_exhibit_ids": [],
  "integrity_report": {
    "total_sessions": 1,
    "total_visit_events": 1,
    "sessions_with_visit_events": 1,
    "issue_count": 0,
    "issues": []
  },
  "visit_event_count": 1,
  "recommendation_count": 1,
  "collaboration_contract": {
    "backend_role": "Provide structured visit context, exhibit data, visitor state, and recommendation candidates.",
    "genios_role": "Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content.",
    "generation_boundary": "The backend does not generate museum explanation text or call large language models."
  }
}
```

The preflight package is a structured readiness check for one active visit session. It marks missing exhibit references, grounding exhibit records without source references, or Visitor State timeline drift as `fail`, and marks absent visit events or absent recommendations as `warn`. `ready_for_handoff` is false when any check fails. This endpoint does not perform dialogue, RAG retrieval, or generated explanation content.

## GeniOS Handoff

Read a combined structured handoff package:

```http
GET /api/genios/handoff/{session_id}?recommendation_limit=3&route_max_items=5
```

Response top-level fields:

- `session_id`
- `source_safety`
- `preflight`: same shape as `GET /api/genios/preflight/{session_id}`
- `context`: same shape as `GET /api/genios/context/{session_id}`
- `route_plan`: same shape as `GET /api/visit-routes/{session_id}/plan`
- `visit_summary`: same shape as `GET /api/visits/{session_id}/summary`
- `handoff_note`

`source_safety` shape:

```json
{
  "ready_for_generation": true,
  "grounding_sources_complete": true,
  "source_reference_count": 1,
  "sourced_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "unsourced_exhibit_ids": [],
  "missing_exhibit_ids": [],
  "blocking_check_names": [],
  "safety_note": "Grounding source references are complete for generated explanation."
}
```

Example ready handoff response using non-historical fixture data:

```json
{
  "session_id": "demo-session-001",
  "source_safety": {
    "ready_for_generation": true,
    "grounding_sources_complete": true,
    "source_reference_count": 1,
    "sourced_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
    "unsourced_exhibit_ids": [],
    "missing_exhibit_ids": [],
    "blocking_check_names": [],
    "safety_note": "Grounding source references are complete for generated explanation."
  },
  "preflight": {
    "session_id": "demo-session-001",
    "ready_for_handoff": true,
    "checks": [
      {
        "name": "exhibit_references",
        "status": "pass",
        "detail": "Current and visited exhibit references resolve to known exhibit records."
      },
      {
        "name": "grounding_source_references",
        "status": "pass",
        "detail": "Grounding exhibit records include source_reference values."
      },
      {
        "name": "visitor_state_integrity",
        "status": "pass",
        "detail": "Visitor State snapshot and visit-event timeline are structurally aligned."
      },
      {
        "name": "visit_event_timeline",
        "status": "pass",
        "detail": "Visit-event timeline is available for continuity."
      },
      {
        "name": "recommendations",
        "status": "pass",
        "detail": "Recommendation candidates are available for route-aware dialogue."
      }
    ],
    "missing_exhibit_ids": [],
    "integrity_report": {
      "total_sessions": 1,
      "total_visit_events": 1,
      "sessions_with_visit_events": 1,
      "issue_count": 0,
      "issues": []
    },
    "visit_event_count": 1,
    "recommendation_count": 1,
    "collaboration_contract": {
      "backend_role": "Provide structured visit context, exhibit data, visitor state, and recommendation candidates.",
      "genios_role": "Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content.",
      "generation_boundary": "The backend does not generate museum explanation text or call large language models."
    }
  },
  "context": {
    "session_id": "demo-session-001",
    "visitor_state": {
      "visitor_type": "tourist",
      "current_exhibit": "fixture-exhibit-001",
      "visited_history": ["fixture-exhibit-001"],
      "interest": ["recommendation"],
      "remaining_time": 25,
      "session_id": "demo-session-001"
    },
    "current_exhibit": {
      "id": "fixture-exhibit-001",
      "name": "Fixture Exhibit One",
      "description": "Non-historical development fixture for validating import and API behavior.",
      "period": "fixture-period",
      "keywords": ["fixture", "context"],
      "importance": 3,
      "people": [],
      "time_range": null,
      "themes": ["development"],
      "source_reference": "Development fixture only. Replace with verified museum source before production use."
    },
    "visited_exhibits": [
      {
        "id": "fixture-exhibit-001",
        "name": "Fixture Exhibit One",
        "description": "Non-historical development fixture for validating import and API behavior.",
        "period": "fixture-period",
        "keywords": ["fixture", "context"],
        "importance": 3,
        "people": [],
        "time_range": null,
        "themes": ["development"],
        "source_reference": "Development fixture only. Replace with verified museum source before production use."
      }
    ],
    "visit_events": [
      {
        "id": 1,
        "session_id": "demo-session-001",
        "exhibit_id": "fixture-exhibit-001",
        "remaining_time": 25,
        "event_time": "2026-09-24T15:53:38"
      }
    ],
    "recommendations": [
      {
        "exhibit_id": "fixture-exhibit-002",
        "name": "Fixture Exhibit Two",
        "reason": "importance level 4; matches interests: recommendation; not yet visited",
        "priority": 1
      }
    ],
    "grounding_exhibit_ids": ["fixture-exhibit-001", "fixture-exhibit-002"],
    "missing_exhibit_ids": [],
    "collaboration_contract": {
      "backend_role": "Provide structured visit context, exhibit data, visitor state, and recommendation candidates.",
      "genios_role": "Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content.",
      "generation_boundary": "The backend does not generate museum explanation text or call large language models."
    }
  },
  "route_plan": {
    "session_id": "demo-session-001",
    "remaining_time": 25,
    "planned_minutes": 7,
    "items": [
      {
        "order": 1,
        "exhibit_id": "fixture-exhibit-002",
        "name": "Fixture Exhibit Two",
        "estimated_minutes": 7,
        "reason": "importance level 4; matches interests: recommendation; continues the current exhibit context; not yet visited"
      }
    ],
    "planning_note": "Rule-based route plan using unvisited exhibits, visitor interests, and remaining time. It does not perform map navigation or generated explanation."
  },
  "visit_summary": {
    "session_id": "demo-session-001",
    "visitor_state": {
      "visitor_type": "tourist",
      "current_exhibit": "fixture-exhibit-001",
      "visited_history": ["fixture-exhibit-001"],
      "interest": ["recommendation"],
      "remaining_time": 25,
      "session_id": "demo-session-001"
    },
    "visited_count": 1,
    "visited_exhibits": [
      {
        "id": "fixture-exhibit-001",
        "name": "Fixture Exhibit One",
        "description": "Non-historical development fixture for validating import and API behavior.",
        "period": "fixture-period",
        "keywords": ["fixture", "context"],
        "importance": 3,
        "people": [],
        "time_range": null,
        "themes": ["development"],
        "source_reference": "Development fixture only. Replace with verified museum source before production use."
      }
    ],
    "visit_events": [
      {
        "id": 1,
        "session_id": "demo-session-001",
        "exhibit_id": "fixture-exhibit-001",
        "remaining_time": 25,
        "event_time": "2026-09-24T15:53:38"
      }
    ],
    "interests": ["recommendation"],
    "remaining_time": 25,
    "missing_exhibit_ids": [],
    "genios_next_step": "Use this structured summary with the knowledge base to generate a grounded visit recap."
  },
  "handoff_note": "Structured backend handoff for GeniOS. Use it for dialogue, RAG grounding, route-aware decisions, and recap generation. The backend does not generate explanation text."
}
```

GeniOS should treat this response as structured input for retrieval and generation. It should only generate explanation content after confirming `source_safety.ready_for_generation` is `true`.

The handoff package combines existing backend structures for GeniOS integration, including source-safety readiness, preflight readiness, and the context package's visit-event timeline. It does not call a large language model and does not generate museum explanation content.

## Visit Summary

Read a structured visit summary:

```http
GET /api/visits/{session_id}/summary
```

Response:

```json
{
  "session_id": "demo-session-001",
  "visitor_state": {
    "visitor_type": "tourist",
    "current_exhibit": "fixture-exhibit-001",
    "visited_history": ["fixture-exhibit-001"],
    "interest": ["recommendation"],
    "remaining_time": 25,
    "session_id": "demo-session-001"
  },
  "visited_count": 1,
  "visited_exhibits": [
    {
      "id": "fixture-exhibit-001",
      "name": "Fixture Exhibit One",
      "description": "Non-historical development fixture for validating import and API behavior.",
      "period": "fixture-period",
      "keywords": ["fixture", "context"],
      "importance": 3,
      "people": [],
      "time_range": null,
      "themes": ["development"],
      "source_reference": "Development fixture only. Replace with verified museum source before production use."
    }
  ],
  "visit_events": [
    {
      "id": 1,
      "session_id": "demo-session-001",
      "exhibit_id": "fixture-exhibit-001",
      "remaining_time": 25,
      "event_time": "2026-09-22T14:26:00"
    }
  ],
  "interests": ["recommendation"],
  "remaining_time": 25,
  "missing_exhibit_ids": [],
  "genios_next_step": "Use this structured summary with the knowledge base to generate a grounded visit recap."
}
```

This endpoint does not generate a natural-language visit recap. It prepares structured context, including the visit-event timeline, for GeniOS or the frontend.
