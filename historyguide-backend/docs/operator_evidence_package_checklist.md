# Operator Evidence Package Checklist

Use this checklist to package evidence after a local demo, staging validation, verified exhibit data import, Web/H5 integration check, GeniOS handoff run, incident response, or rollback-sensitive production-like change.

The package should let another operator understand what was checked, which backend signals were clean or blocked, and whether GeniOS generated explanation was allowed for the affected visit session.

This checklist is backend operational evidence only. It does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not prove historical accuracy.

## Package Metadata

Record:

- package name:
- run type:
- operator:
- date:
- environment:
- backend base URL:
- backend version or source revision:
- database backend:
- database URL label, not secret:
- Web/H5 origin:
- GeniOS environment:
- affected `session_id`:
- affected exhibit ids:
- final decision: proceed, proceed with warnings, blocked, rollback required

Allowed run types:

- local fixture demo
- verified exhibit data dry-run
- verified exhibit data import
- staging migration validation
- Web/H5 integration check
- GeniOS handoff evidence run
- production-like monitoring setup
- incident triage
- backup and rollback drill

## Required Evidence Files

Include or link:

- completed `docs/staging_validation_record.md` copy for staging or production-like runs
- completed `docs/genios_handoff_evidence_template.md` copy for GeniOS handoff runs
- completed `docs/backup_rollback_drill.md` copy when rollback risk exists
- incident notes based on `docs/incident_response_checklist.md` when an incident occurred
- monitoring setup notes based on `docs/monitoring_alert_examples.md` when alerting was configured
- source-review notes based on `docs/real_exhibit_seed_review.md` for verified exhibit data
- operator sequence notes from `docs/operator_runbook.md`

Use examples only as placeholders:

- `docs/examples/staging_validation_record.example.md`
- `docs/examples/genios_handoff_evidence.example.md`
- `docs/examples/deployment_environment_validation.example.md`
- `docs/examples/backend_readiness_validation.example.md`
- `docs/examples/operator_evidence_package.example.md`
- `docs/examples/operational_alerts_attention_required.example.json`

Do not label placeholder examples as real staging, production-like, or museum evidence. Use `docs/examples/operator_evidence_package.example.md` only as formatting guidance for an assembled package.

## Runtime Evidence

Preserve command output:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Record:

- runtime config validation result
- API key presence check result
- operator key separation check result
- CORS wildcard risk result
- database URL profile risk result
- log format result
- deployment self-check result
- backend readiness validation result
- returned `X-HistoryGuide-Request-Id` values
- `GET /health` result
- `GET /ready` result
- `GET /api/system/database` result
- `GET /api/system/access-policy` result
- `GET /api/system/security-status` result
- `GET /api/system/operational-alerts` result
- GeniOS source-safety result from read-only backend readiness validation

Do not preserve secret values from `HISTORYGUIDE_API_KEY`, `HISTORYGUIDE_OPERATOR_API_KEY`, `X-HistoryGuide-Api-Key`, or `X-HistoryGuide-Operator-Key`.

## Data And Migration Evidence

For real or production-like exhibit data, preserve:

```powershell
python scripts\export_exhibits.py <backup-file>
python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty
python scripts\rehearse_exhibit_restore.py <backup-file>
python scripts\import_exhibits.py --dry-run <verified-seed-file>
python scripts\rehearse_migrations.py
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Record:

- verified seed file path
- source package location
- source review owner
- backup file path
- backup verification result
- restore rehearsal result
- import dry-run result
- migration rehearsal result
- staging Alembic head
- core table status
- exhibit count
- unsourced exhibit count
- Visitor State count
- visit-event count
- audit-log count

Do not create, infer, rewrite, or generate historical facts to make evidence look complete.

## Visit Flow Evidence

Preserve request or response summaries for:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

Record:

- `session_id`
- `visitor_type`
- current exhibit
- visited history
- visit-event count
- remaining time
- recommendation count
- route plan item count
- integrity issue count
- returned `X-HistoryGuide-Request-Id` values

The package should prove that Visitor State follows one real visit session, not a generic chatbot conversation.

## GeniOS Handoff Evidence

Preserve request or response summaries for:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Record:

- `grounding_exhibit_ids`
- `grounding_sources_complete`
- `source_safety.ready_for_generation`
- `missing_exhibit_ids`
- `unsourced_exhibit_ids`
- preflight `ready_for_handoff`
- handoff request id
- whether GeniOS consumed the backend handoff package
- whether generated explanation display was allowed
- review-run id, review decision, finalize status, and final-answer request id (without copying drafts or source text)

`grounding_sources_complete=true` and `source_safety.ready_for_generation=true` are necessary preflight checks, not display authorization. Display only the matching review-run `finalize.answer` after successful finalization. Fixture, missing approval, skipped review, or tool failure must block display.

The package does not define GeniOS prompts, does not run RAG, and does not judge generated historical prose.

## Monitoring And Incident Evidence

For production-like runs, preserve:

- structured request log query for `X-HistoryGuide-Request-Id`
- `HISTORYGUIDE_LOG_FORMAT=json` validation result
- dashboard or alert notes from `docs/monitoring_alert_examples.md`
- `GET /api/system/operational-alerts` output
- request logs for `status_code = 401`
- request logs for `status_code >= 500`
- request logs for `/api/genios/` with `elapsed_ms > 1000`
- incident notes from `docs/incident_response_checklist.md`, if any

Record whether any alert reached:

- `warn`
- `fail`
- `rollback_candidate`

Stop or escalate when monitoring evidence shows source-safety failure, Visitor State drift, repeated auth failure from expected clients, readiness failure, or missing audit evidence after state-changing operations.

## Audit Evidence

Preserve:

```http
GET /api/audit-logs/stats
GET /api/audit-logs
```

Record:

- total audit logs
- latest audit timestamp
- `visitor_state_created` count or presence
- `visitor_state_updated` count or presence
- `visit_event_recorded` count or presence
- `exhibits_imported` count or presence
- returned `X-HistoryGuide-Request-Id` values

Audit logs are operator traceability. They are not visitor identity, not visitor profile data, not historical evidence, not source references, not RAG content, not GeniOS prompt input, and not generated explanation content.

## Redaction Checklist

Remove or avoid:

- `HISTORYGUIDE_API_KEY`
- `HISTORYGUIDE_OPERATOR_API_KEY`
- `X-HistoryGuide-Api-Key`
- `X-HistoryGuide-Operator-Key`
- full database URLs
- database credentials
- private GeniOS prompts
- raw source packages when they are not approved for sharing
- unreviewed generated historical text
- visitor personal information not required for backend debugging

## Final Package Decision

Use `docs/production_readiness_decision_checklist.md` when the package supports a production-like, public demo, museum-site rehearsal, or real visitor-facing backend decision.

Set one final decision:

- `proceed`: all required gates passed
- `proceed_with_warnings`: warnings were reviewed and accepted by the operator
- `blocked`: a required gate failed
- `rollback_required`: recovery must follow `docs/backup_rollback_drill.md`

Record:

- final decision:
- blocking issues:
- warnings accepted:
- rollback owner:
- follow-up owner:
- follow-up date:

## Boundary Reminder

This evidence package supports backend operation for a real museum visit Agent. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.
