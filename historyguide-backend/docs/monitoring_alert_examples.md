# Monitoring Alert Examples

Use these examples when connecting NK HistoryGuide backend signals to a staging or production-like monitoring platform.

The goal is to detect failures that affect a real museum visit flow: backend readiness, API access, exhibit source safety, Visitor State integrity, Web/H5 scan events, GeniOS handoff readiness, and request-log correlation.

This monitoring guidance does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not prove historical accuracy.

## Required Inputs

Collect these backend signals:

- `GET /ready`
- `GET /api/system/database`
- `GET /api/system/access-policy`
- `GET /api/system/security-status`
- `GET /api/system/operational-alerts`
- structured request logs with `HISTORYGUIDE_LOG_FORMAT=json`
- request correlation through `X-HistoryGuide-Request-Id`

For visit-flow checks, also collect:

- `POST /api/visitor-states/{session_id}/visit-events`
- `GET /api/visitor-states/{session_id}/integrity`
- `GET /api/visitor-states/{session_id}/visit-events`
- `GET /api/genios/grounding/{session_id}`
- `GET /api/genios/preflight/{session_id}`
- `GET /api/genios/handoff/{session_id}`

For source-safety checks, preserve:

- `source_safety.ready_for_generation`
- `grounding_sources_complete`
- `missing_exhibit_ids`
- `unsourced_exhibit_ids`

## Operational Alerts Endpoint

Poll:

```http
GET /api/system/operational-alerts
```

Example response:

```text
docs/examples/operational_alerts_attention_required.example.json
```

Alert names currently produced by the backend:

- `no_exhibit_records`
- `unsourced_exhibits`
- `exhibit_metadata_gaps`
- `visitor_state_integrity_issues`
- `audit_logs_empty`

Treat `severity=fail` as a stop condition before public demos, GeniOS generated explanation display, or production-like promotion.

Treat `severity=warn` as a review condition. A local fixture demo may continue with warnings when the operator records the reason, but a real museum run should clear or explicitly accept warnings before visitors rely on the system.

## Example Alert Rules

### Backend Readiness Failure

Trigger when:

- `GET /ready` returns `503`
- structured request log has `path = "/ready"` and `status_code >= 500`
- deployment self-check cannot complete the readiness step

Impact:

- Web/H5 and GeniOS should not start a new visit flow.
- Existing generated explanation should not be shown as fresh backend-validated output.

Triage:

- check `GET /api/system/database`
- run `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs` for staging or production-like databases
- preserve `X-HistoryGuide-Request-Id`
- follow `docs/incident_response_checklist.md`

### Repeated Auth Failure

Trigger when:

- structured request logs show repeated `status_code = 401`
- affected paths include `/api/visitor-states`, `/api/genios/`, `/api/audit-logs`, or `/api/system/operational-alerts`

Impact:

- Web/H5 scan events may not update Visitor State.
- GeniOS may receive stale or missing handoff context.
- Operator checks may be blocked.

Triage:

- check `GET /api/system/access-policy`
- check `GET /api/system/security-status`
- confirm callers use `X-HistoryGuide-Api-Key` or `X-HistoryGuide-Operator-Key` as appropriate
- do not copy `HISTORYGUIDE_API_KEY` or `HISTORYGUIDE_OPERATOR_API_KEY` values into logs or incident notes

### Source-Safety Block

Trigger when:

- `GET /api/system/operational-alerts` includes `unsourced_exhibits`
- `GET /api/genios/grounding/{session_id}` reports `grounding_sources_complete=false`
- `GET /api/genios/handoff/{session_id}` reports `source_safety.ready_for_generation=false`
- `missing_exhibit_ids` or `unsourced_exhibit_ids` is not empty

Impact:

- GeniOS generated explanation should not be displayed for the affected session.

Triage:

- check `GET /api/exhibits/source-report`
- check `GET /api/exhibits/quality-report`
- check `GET /api/genios/preflight/{session_id}`
- correct verified exhibit data or Visitor State references
- do not create, infer, rewrite, or generate historical facts to clear the alert

### Visitor State Drift

Trigger when:

- `GET /api/system/operational-alerts` includes `visitor_state_integrity_issues`
- `GET /api/visitor-states/{session_id}/integrity` reports issues
- `GET /api/genios/handoff/{session_id}` includes Visitor State integrity failures

Impact:

- route suggestions, visit summaries, and GeniOS context may not match the physical visit.

Triage:

- inspect `GET /api/visitor-states/{session_id}/visit-events`
- preserve Web/H5 scan request ids
- record future physical movement with `POST /api/visitor-states/{session_id}/visit-events`
- avoid manual state patches that hide drift before evidence is captured

### GeniOS Handoff Slow Or Failing

Trigger when:

- structured request logs show `path starts with "/api/genios/"` and `status_code >= 500`
- structured request logs show `path starts with "/api/genios/"` and `elapsed_ms > 1000`
- GeniOS handoff evidence cannot record request ids for context, grounding, preflight, and handoff

Impact:

- GeniOS may not have current visit context or source-safety gates.

Triage:

- check `GET /api/genios/context/{session_id}`
- check `GET /api/genios/grounding/{session_id}`
- check `GET /api/genios/preflight/{session_id}`
- check `GET /api/genios/handoff/{session_id}`
- preserve `grounding_exhibit_ids`, `grounding_sources_complete`, and `source_safety.ready_for_generation`

This rule covers backend handoff latency and failures only. It does not debug GeniOS RAG internals or judge generated historical prose.

### Audit Evidence Missing

Trigger when:

- `GET /api/system/operational-alerts` includes `audit_logs_empty`
- state-changing demo or staging actions occurred but `GET /api/audit-logs/stats` shows no relevant audit activity

Impact:

- operator evidence is incomplete for real data import, visit-event recording, or staging validation.

Triage:

- inspect `GET /api/audit-logs/stats`
- inspect `GET /api/audit-logs`
- rerun only the missing operator check when it is safe and non-destructive
- preserve command output and request ids

## Suggested Escalation

Use these levels consistently:

- `info`: clean check or local fixture-only warning
- `warn`: operator review required before demo or handoff
- `fail`: stop generated explanation, stop production-like promotion, or enter incident response
- `rollback_candidate`: follow `docs/backup_rollback_drill.md`

Escalate to `rollback_candidate` when source-safety regresses after import, a migration affects the wrong database, verified exhibit records disappear, or recovery requires restoring previous data or deployment state.

## Dashboard Panels

Minimum production-like dashboard panels:

- readiness status from `GET /ready`
- operational alert status and `fail_count`
- repeated `401` by path group
- repeated `5xx` by path group
- slow `/api/genios/` requests
- `unsourced_exhibits` count
- `visitor_state_integrity_issues` count
- audit log total and latest timestamp from `GET /api/audit-logs/stats`
- request-id search panel for `X-HistoryGuide-Request-Id`

## Redaction Boundary

Never export or display:

- `HISTORYGUIDE_API_KEY`
- `HISTORYGUIDE_OPERATOR_API_KEY`
- `X-HistoryGuide-Api-Key`
- `X-HistoryGuide-Operator-Key`
- raw database credentials
- raw source packages
- private GeniOS prompts
- unreviewed generated historical text

Monitoring records are not visitor identity, not visitor profile data, not historical evidence, not source references, not GeniOS prompt input, not RAG content, and not generated explanation content.

## Related Documents

- `docs/centralized_logging.md`
- `docs/incident_response_checklist.md`
- `docs/operator_runbook.md`
- `docs/operator_evidence_package_checklist.md`
- `docs/backup_rollback_drill.md`
- `docs/production_hardening.md`
