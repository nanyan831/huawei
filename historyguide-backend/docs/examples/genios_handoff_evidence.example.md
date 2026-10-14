# GeniOS Handoff Evidence Example

This example uses non-historical fixture-style placeholder values only. It is not evidence that GeniOS handoff has been validated in staging or in the museum.

Do not use the generated-looking fields below as historical content, prompt text, RAG content, or museum source evidence.

## Run Metadata

- Date: 2026-09-26
- Operator: example-operator
- Environment name: staging-example
- Backend base URL: https://historyguide-backend.example
- Backend version or source revision: example-revision
- Database URL label, not secret: staging-db-label
- Web/H5 origin: https://historyguide.example
- GeniOS environment: genios-staging-example
- Test session id: staging-session-example
- Current exhibit id: fixture-exhibit-001
- Expected sourced exhibit ids: fixture-exhibit-001, fixture-exhibit-002
- Related request ids: example-request-201, example-request-202, example-request-203, example-request-204

## Pre-Handoff Gates

- Readiness result: PASS
- Database backend: sqlite-example
- Access policy checked: yes
- Security status checked: yes
- Unsourced real exhibit count: 0
- Quality issue count: 0
- Visitor State integrity passed: yes
- Notes: Example only. This does not prove historical accuracy.

## Visit Context Evidence

- Visitor type: tourist
- Interest values: architecture, university-history
- Remaining time: 25
- Current exhibit id: fixture-exhibit-001
- Visited history: fixture-exhibit-001
- Visit-event count: 1
- Visit-event request id: example-request-201
- Repeated scans handled without duplicate visited history: yes
- Notes: Example only. The exhibit ids are placeholder fixture ids.

## GeniOS Backend Package Evidence

- Context request id: example-request-202
- Grounding request id: example-request-203
- Preflight request id: example-request-204
- Handoff request id: example-request-205
- Context contains `visitor_state`: yes
- Context contains `visit_events`: yes
- Context contains `grounding_exhibit_ids`: yes
- Grounding contains `source_references`: yes
- `grounding_sources_complete`: true
- `missing_exhibit_ids`: none
- `unsourced_exhibit_ids`: none
- `preflight.ready_for_handoff`: true
- `source_safety.ready_for_generation`: true
- `source_safety.blocking_check_names`: none
- Handoff contains `route_plan`: yes
- Handoff contains `visit_summary`: yes
- Handoff contains `handoff_note`: yes
- Notes: Example only. The backend still does not generate explanation content.

## GeniOS Consumption Evidence

- GeniOS used backend `grounding_exhibit_ids`: yes
- GeniOS used exhibit source references or knowledge-base mappings: yes
- GeniOS paused generation when `source_safety.ready_for_generation=false`: not triggered in this example
- GeniOS proceeded only when `source_safety.ready_for_generation=true`: yes
- GeniOS did not infer missing exhibit ids from chat history: yes
- GeniOS did not treat `X-HistoryGuide-Request-Id` as prompt input: yes
- GeniOS output was checked against verified knowledge sources outside this backend template: example-placeholder
- Notes: Example only. Do not paste private prompts or unreviewed generated historical text here.

## Logging Evidence

- Web/H5 request ids: example-web-request-001
- GeniOS request ids: example-genios-request-001
- Backend request ids: example-request-201, example-request-202, example-request-203, example-request-204, example-request-205
- Deployment self-check request ids: example-self-check-request-001
- Centralized log query or dashboard link: logging-dashboard.example/query/request-id
- `request_id` searchable: yes
- `status_code` searchable: yes
- `elapsed_ms` searchable: yes
- No `HISTORYGUIDE_API_KEY` values observed in logs: yes
- No `HISTORYGUIDE_OPERATOR_API_KEY` values observed in logs: yes
- Notes: Example only.

## Pass Criteria

- `GET /ready` is ready: yes
- Stable `session_id` for the physical visit: yes
- Current exhibit id exists in exhibit database: yes
- Real exhibit records used for grounding have non-empty `source_reference`: yes
- Visitor State integrity passes: yes
- `grounding_sources_complete=true`: yes
- `source_safety.ready_for_generation=true`: yes
- `missing_exhibit_ids` is empty: yes
- `unsourced_exhibit_ids` is empty: yes
- Request ids captured across Web/H5, GeniOS, backend logs, and operator notes: yes

## Stop Conditions

- Backend readiness failed: no
- Session id could not be created or recovered: no
- Visit-event timeline failed to reflect physical scan: no
- Current exhibit id missing: no
- Source references empty for real exhibit records: no
- `grounding_sources_complete=false`: no
- `source_safety.ready_for_generation=false`: no
- Preflight failed grounding or integrity checks: no
- Request ids could not be correlated: no
- GeniOS attempted generation without verified source grounding: no

## Boundary Reminder

This example is placeholder-only and not staging evidence. It does not define a GeniOS prompt, does not run RAG, does not generate explanation content, does not train models, and does not implement digital human or AR/VR features.
