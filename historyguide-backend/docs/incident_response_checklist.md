# Incident Response Checklist

Use this checklist when the NK HistoryGuide backend fails during a real visit demo, Web/H5 integration run, GeniOS handoff, staging validation, or production-like operator check.

This checklist is for backend incident triage. It preserves evidence, identifies the failing backend gate, and decides whether to continue, pause generated explanation, or enter the backup and rollback drill. It does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## First Five Minutes

Capture evidence before changing data, secrets, or deployment settings:

- incident start time and environment
- backend base URL
- affected caller: Web/H5, GeniOS, operator tooling, or local demo
- affected `session_id`
- affected exhibit ids
- latest returned `X-HistoryGuide-Request-Id` values
- latest backend request logs or centralized log query link
- exact endpoint, command, status code, and response body
- database URL label, not the secret value
- whether `HISTORYGUIDE_API_KEY` and `HISTORYGUIDE_OPERATOR_API_KEY` are expected in this environment

Do not rotate secrets, patch Visitor State manually, reset a database, import exhibit data, or redeploy until the initial evidence is captured.

## 1. Readiness Or Database Failure

Symptoms:

- `GET /ready` returns non-ready or `503`
- deployment self-check fails before business endpoints
- the service starts but cannot read the database
- migrations or staging validation appear out of sync

Check:

```http
GET /ready
GET /api/system/database
GET /api/system/operational-alerts
```

Then run, when operating against a staging or production-like database:

```powershell
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Preserve:

- response body from `GET /ready`
- response body from `GET /api/system/database`
- current Alembic head reported by staging database validation
- core table status
- returned `X-HistoryGuide-Request-Id`

Stop when:

- the backend cannot reach the intended database
- the database is not at the expected Alembic head
- core tables are missing
- the target database label does not match the intended environment

## 2. Repeated 401 Or Access Boundary Failure

Symptoms:

- expected Web/H5 or GeniOS calls repeatedly return `401`
- operator endpoints accept the wrong key type
- operator endpoints are reachable without the expected operator key

Check:

```http
GET /api/system/access-policy
GET /api/system/security-status
```

Confirm:

- the trusted visitor gateway and GeniOS integration send `X-HistoryGuide-Api-Key` when business API protection is enabled; visitor browser code never holds it
- trusted operator tooling sends `X-HistoryGuide-Operator-Key`
- `HISTORYGUIDE_API_KEY` is configured for shared or public business APIs
- `HISTORYGUIDE_OPERATOR_API_KEY` is configured for shared or production-like operator endpoints
- the operator key is not reused as the business key

Preserve the status code, response detail, caller name, and returned `X-HistoryGuide-Request-Id`. Do not copy secret values into incident notes.

## 3. Source-Safety Or Generated Explanation Block

Symptoms:

- GeniOS should not produce generated explanation yet
- `source_safety.ready_for_generation=false`
- `grounding_sources_complete=false`
- `missing_exhibit_ids` or `unsourced_exhibit_ids` is non-empty

Check:

```http
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Stop generated explanation when:

- `source_safety.ready_for_generation` is false or unknown
- `grounding_sources_complete` is false or unknown
- any grounding exhibit lacks `source_reference`
- any Visitor State reference points to a missing exhibit

Resolution must come from corrected verified exhibit data or corrected Visitor State references. Do not create, infer, rewrite, or generate historical facts to clear the incident.

## 4. Visitor State Drift

Symptoms:

- current exhibit and visit-event timeline disagree
- repeated QR scans do not appear in the timeline
- GeniOS context references unexpected visited exhibits
- Web/H5 shows a route or recap inconsistent with the physical visit

Check:

```http
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/genios/context/{session_id}
GET /api/genios/handoff/{session_id}
```

Expected operating rule:

- future physical movement should be recorded through `POST /api/visitor-states/{session_id}/visit-events`
- manual `PATCH /api/visitor-states/{session_id}` should not be used to hide timeline drift during incident response

Preserve the session id, current exhibit, `visited_history`, visit-event count, request ids, and the exact Web/H5 action that triggered the drift.

## 5. Web/H5 Scan Or Browser Integration Failure

Symptoms:

- QR scan does not update the active visit
- browser requests fail CORS preflight
- Web/H5 cannot correlate backend failures with frontend logs

Check:

```http
GET /api/system/access-policy
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/visit-events
GET /api/genios/handoff/{session_id}
```

Confirm:

- `HISTORYGUIDE_CORS_ORIGINS` includes the exact Web/H5 origin
- the trusted visitor gateway sends `X-HistoryGuide-Api-Key` when needed; the browser never holds the shared key
- Web/H5 preserves `X-HistoryGuide-Request-Id`
- one physical visit keeps one stable `session_id`
- exhibit ids scanned by Web/H5 exist in `GET /api/exhibits/{exhibit_id}`

## 6. GeniOS Handoff Failure

Symptoms:

- GeniOS receives incomplete backend context
- GeniOS cannot decide whether generated explanation is allowed
- GeniOS handoff evidence cannot be completed

Check:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Preserve:

- `grounding_exhibit_ids`
- `missing_exhibit_ids`
- `unsourced_exhibit_ids`
- `grounding_sources_complete`
- `source_safety.ready_for_generation`
- request ids for each backend call

This checklist only diagnoses backend handoff data and source-safety fields. It does not define GeniOS prompts, does not debug RAG retrieval internals, and does not judge generated historical prose.

## 7. Logging Or Request Correlation Failure

Symptoms:

- operator cannot connect a failed Web/H5 or GeniOS action to backend logs
- deployment self-check request ids are missing
- centralized logs do not expose stable request fields

Check:

```text
HISTORYGUIDE_LOG_FORMAT=json
X-HistoryGuide-Request-Id
```

Review:

```text
docs/centralized_logging.md
docs/monitoring_alert_examples.md
docs/operator_runbook.md
```

Expected stable fields:

- `event`
- `service_id`
- `request_id`
- `http_method`
- `path`
- `status_code`
- `elapsed_ms`

Logs are operational correlation metadata only. They are not visitor identity, visitor profile data, historical evidence, source references, GeniOS prompt input, or proof of historical accuracy.

## 8. Data Corruption Or Rollback Trigger

Enter `docs/backup_rollback_drill.md` when any of these are true:

- verified exhibit records were imported into the wrong environment
- source reports show unexpected unsourced real exhibits
- a migration changed the wrong database
- a reset or deployment lost verified exhibit data
- GeniOS handoff source-safety regressed after a data or deployment change
- incident resolution requires restoring previous exhibit data or deployment state

Before rollback, preserve:

- latest exhibit export path
- backup verification output
- restore rehearsal output
- `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs` output
- `GET /api/exhibits/source-report`
- `GET /api/genios/handoff/{session_id}`
- request ids and centralized log links

Rollback is incomplete until readiness, source report, Visitor State expectations, and GeniOS handoff source-safety are back to the known working state.

## Evidence Package

For every incident, keep:

- incident timeline
- changed configuration labels
- endpoint or command outputs
- request ids
- source and quality report summaries
- Visitor State integrity response
- GeniOS handoff response summary
- audit log or audit log stats evidence when state-changing operations occurred
- rollback decision, if any

Do not keep secret values, database credentials, unreviewed generated historical text, private prompts, or unverified historical claims in the evidence package.

## Boundary Reminder

This checklist supports backend incident response for a real museum visit Agent. It does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not prove historical accuracy.

Use `docs/operator_runbook.md` for the full operator sequence and `docs/backup_rollback_drill.md` when recovery requires restoring data or deployment state.

After the incident is closed or handed off, package the preserved evidence with `docs/operator_evidence_package_checklist.md`.
