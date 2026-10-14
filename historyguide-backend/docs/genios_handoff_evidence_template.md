# GeniOS Handoff Evidence Template

Use this template for each NK HistoryGuide backend and GeniOS handoff integration run. Keep one completed copy per test session, demo run, or staging validation run.

This is an evidence template for backend handoff readiness. It does not define a GeniOS prompt, does not run RAG, does not generate explanation content, does not train models, and does not implement digital human or AR/VR features.

For a placeholder-only example, see `docs/examples/genios_handoff_evidence.example.md`. The example is not evidence that staging or the museum environment has been validated.

## Run Metadata

- Date:
- Operator:
- Environment name:
- Backend base URL:
- Backend version or source revision:
- Database URL label, not secret:
- Web/H5 origin:
- GeniOS environment:
- Test session id:
- Current exhibit id:
- Expected sourced exhibit ids:
- Related request ids:

## Pre-Handoff Gates

Record the result of these checks before requesting generated explanation:

```http
GET /ready
GET /api/system/database
GET /api/system/access-policy
GET /api/system/security-status
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/visitor-states/{session_id}/integrity
```

Record:

- Readiness result:
- Database backend:
- Access policy checked:
- Security status checked:
- Unsourced real exhibit count:
- Quality issue count:
- Visitor State integrity passed:
- Notes:

## Visit Context Evidence

Record the visit session and physical exhibit movement evidence:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}
GET /api/visitor-states/{session_id}/visit-events
```

Record:

- Visitor type:
- Interest values:
- Remaining time:
- Current exhibit id:
- Visited history:
- Visit-event count:
- Visit-event request id:
- Repeated scans handled without duplicate visited history:
- Notes:

## GeniOS Backend Package Evidence

Record request ids and key fields from:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Record:

- Context request id:
- Grounding request id:
- Preflight request id:
- Handoff request id:
- Context contains `visitor_state`:
- Context contains `visit_events`:
- Context contains `grounding_exhibit_ids`:
- Grounding contains `source_references`:
- `grounding_sources_complete`:
- `missing_exhibit_ids`:
- `unsourced_exhibit_ids`:
- `preflight.ready_for_handoff`:
- `source_safety.ready_for_generation`:
- `source_safety.blocking_check_names`:
- Handoff contains `route_plan`:
- Handoff contains `visit_summary`:
- Handoff contains `handoff_note`:
- Notes:

## GeniOS Consumption Evidence

Record how GeniOS consumed the backend package. Do not paste secret keys, private prompts, or unreviewed generated historical text into this file.

Record:

- GeniOS used backend `grounding_exhibit_ids`:
- GeniOS used exhibit source references or knowledge-base mappings:
- GeniOS paused generation when `source_safety.ready_for_generation=false`:
- GeniOS proceeded only when `source_safety.ready_for_generation=true`:
- GeniOS did not infer missing exhibit ids from chat history:
- GeniOS did not treat `X-HistoryGuide-Request-Id` as prompt input:
- GeniOS output was checked against verified knowledge sources outside this backend template:
- Notes:

## Logging Evidence

Preserve operational evidence for correlation:

- Web/H5 request ids:
- GeniOS request ids:
- Backend request ids:
- Deployment self-check request ids:
- Centralized log query or dashboard link:
- `request_id` searchable:
- `status_code` searchable:
- `elapsed_ms` searchable:
- No `HISTORYGUIDE_API_KEY` values observed in logs:
- No `HISTORYGUIDE_OPERATOR_API_KEY` values observed in logs:
- Notes:

## Pass Criteria

All of these should be true before a generated personalized explanation is shown to a visitor:

- `GET /ready` is ready.
- The session has one stable `session_id` for the physical visit.
- The current exhibit id exists in the exhibit database.
- Real exhibit records used for grounding have non-empty `source_reference`.
- Visitor State integrity passes.
- `grounding_sources_complete=true`.
- `source_safety.ready_for_generation=true`.
- `missing_exhibit_ids` is empty.
- `unsourced_exhibit_ids` is empty.
- Request ids are captured in Web/H5, GeniOS, backend logs, and operator notes.

## Stop Conditions

Stop the handoff run and fix data, configuration, or integration behavior when:

- the backend readiness check fails.
- the session id cannot be created or recovered.
- the visit-event timeline does not reflect the physical scan or exhibit-entry event.
- the current exhibit id is missing.
- source references are empty for real exhibit records.
- `grounding_sources_complete=false`.
- `source_safety.ready_for_generation=false`.
- preflight reports failed grounding, missing exhibit ids, or Visitor State integrity issues.
- request ids cannot be correlated across Web/H5, GeniOS, backend logs, and operator notes.
- GeniOS tries to generate historical explanation without verified source grounding.

## Boundary Reminder

This template records backend handoff evidence only.

Do not use it as:

- proof of historical accuracy
- a replacement for museum or expert review
- a GeniOS prompt
- RAG content
- generated explanation text
- visitor identity
- visitor profile data
- a digital human, AR, or VR specification
