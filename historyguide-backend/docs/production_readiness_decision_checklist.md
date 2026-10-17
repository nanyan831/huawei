# Production Readiness Decision Checklist

Use this checklist before declaring that an NK HistoryGuide backend environment is ready for a production-like run, public demo, museum-site rehearsal, or real visitor-facing integration.

This checklist is a decision gate, not a deployment claim. A `proceed` decision means the backend evidence for the selected environment is acceptable for the selected run type. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## Decision Metadata

Record:

- decision date:
- decision owner:
- environment:
- run type:
- backend base URL:
- backend version or source revision:
- database backend:
- database URL label, not secret:
- Web/H5 origin:
- GeniOS environment:
- operator evidence package path:
- final decision: proceed, proceed_with_warnings, blocked, rollback_required

Allowed run types:

- staging validation
- verified exhibit data import
- Web/H5 integration check
- GeniOS handoff evidence run
- production-like monitoring setup
- museum-site rehearsal
- real visitor-facing backend run

## Required Evidence

Before a `proceed` decision, the operator must complete or attach:

- `docs/staging_validation_record.md`
- `docs/operator_evidence_package_checklist.md`
- `docs/backup_rollback_drill.md` when the run can affect verified exhibit data, migration state, deployment state, Web/H5 integration, or GeniOS handoff behavior
- `docs/genios_handoff_evidence_template.md` when generated explanation may be displayed
- `docs/web_h5_integration_checklist.md` when a browser client participates
- `docs/monitoring_alert_examples.md` when production-like dashboard or alert policies are expected
- `docs/incident_response_checklist.md` when a prior incident or open failure exists

Placeholder examples are not evidence:

- `docs/examples/staging_validation_record.example.md`
- `docs/examples/genios_handoff_evidence.example.md`
- `docs/examples/deployment_environment_validation.example.md`
- `docs/examples/backend_readiness_validation.example.md`
- `docs/examples/operator_evidence_package.example.md`
- `docs/examples/production_readiness_decision.example.md`
- `docs/examples/operational_alerts_attention_required.example.json`

## Gate 1: Runtime Configuration

Required command:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

Use `--profile production` only for production-like configuration review.

Proceed only when:

- `HISTORYGUIDE_API_KEY` is configured when shared, public, or production-like business APIs are exposed
- `HISTORYGUIDE_OPERATOR_API_KEY` is configured when audit, operational, security, or access-policy endpoints are exposed outside trusted local use
- `HISTORYGUIDE_OPERATOR_API_KEY` is separate from `HISTORYGUIDE_API_KEY`
- `HISTORYGUIDE_CORS_ORIGINS` lists explicit Web/H5 origins
- `HISTORYGUIDE_LOG_FORMAT=json` is configured when centralized logs are expected
- no secret values are printed or preserved

Block when:

- the production-like environment has no business API key
- operator endpoints are exposed without an operator key
- CORS uses an unsafe wildcard for a browser-facing environment
- the database URL label does not match the intended environment

## Gate 2: Read-Only Runtime Self-Check

Required command:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Required endpoints:

```http
GET /health
GET /ready
GET /api/system/database
GET /api/system/access-policy
GET /api/system/security-status
GET /api/system/operational-alerts
```

Stronger read-only validator:

```powershell
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Proceed only when:

- `GET /ready` confirms database access
- `GET /api/system/database` reports the intended backend and migration boundary
- `GET /api/system/access-policy` matches public, business, operator, and local workflow expectations
- `GET /api/system/security-status` reports expected key controls without exposing secret values
- returned `X-HistoryGuide-Request-Id` values are preserved
- operational alerts have no `severity=fail`
- `python scripts\validate_backend_readiness.py` passes for required runtime, data, Visitor State, GeniOS handoff, source-safety, and audit gates

Block when:

- readiness fails
- database backend is unexpected
- operator endpoints accept the wrong key type
- `GET /api/system/operational-alerts` reports fail-level source, Visitor State, or audit evidence problems

## Gate 3: Database And Migration

Required commands:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Proceed only when:

- isolated migration rehearsal passes
- staging or production-like database is at the expected Alembic head
- core tables are present
- exhibit count is expected for the run
- empty `source_reference` count is zero for verified exhibit data
- Visitor State count and visit-event count match the test plan
- audit-log count is non-zero after state-changing checks

Block when:

- migrations were not applied to the intended target
- core tables are missing
- verified exhibit records are unsourced
- audit logs are missing after import or visit-event operations

This gate does not run migrations through `validate_staging_database.py`, does not import records, does not write audit logs, does not validate historical accuracy, does not run RAG, and does not generate explanation content.

## Gate 4: Data Safety And Backup

Required commands:

```powershell
python scripts\export_exhibits.py <backup-file>
python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty
python scripts\rehearse_exhibit_restore.py <backup-file>
python scripts\import_exhibits.py --dry-run <verified-seed-file>
```

Proceed only when:

- verified seed file passed manual source review
- every real exhibit record has non-empty `source_reference`
- backup export completed before the change
- backup verification passed
- restore rehearsal passed
- import dry-run passed
- rollback owner and rollback path are recorded

Block when:

- backup cannot be verified
- restore rehearsal fails
- dry-run finds duplicate ids or missing source references
- source package references are unavailable
- historical content was created, inferred, rewritten, or generated to make data pass

## Gate 5: Visit Flow

Required checks:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

Proceed only when:

- one real visit uses one stable `session_id`
- `visitor_type` is one of `freshman`, `alumnus`, or `tourist`
- QR scan or exhibit-entry events are recorded through visit events
- Visitor State integrity issue count is zero
- recommendations and route plan are structured and explainable
- visit summary is structured and does not generate natural-language recap text

Block when:

- current exhibit or visited history references missing exhibit ids
- visit-event timeline and Visitor State snapshot drift
- Web/H5 cannot preserve request ids

## Gate 6: GeniOS Handoff And Source Safety

Required checks:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

The following are necessary preflight checks, not permission to display a draft:

- `grounding_sources_complete=true`
- `source_safety.ready_for_generation=true`
- `missing_exhibit_ids` is empty
- `unsourced_exhibit_ids` is empty
- preflight `ready_for_handoff=true`
- `docs/genios_handoff_evidence_template.md` is completed for the run

For an exhibit/route answer, additionally require a successful `/api/genios/runs` prepare -> review -> finalize sequence. For general history, require the corresponding `/api/genios/history-runs` sequence. The visitor must see only the matching `finalize.answer`, enforced by a workflow or trusted gateway. Current live Handoff alone does not satisfy this gate.

Block generated explanation display when:

- `grounding_sources_complete=false`
- `source_safety.ready_for_generation=false`
- any grounding exhibit is unsourced
- any referenced exhibit id is missing
- request ids cannot be correlated across Web/H5, GeniOS, backend logs, and operator notes
- review/finalize was skipped, failed, timed out, rejected a stale snapshot, or returned a different draft

This gate checks backend preflight and final-answer control. It does not itself judge whether every historical claim is supported by its source; curator review and claim-level evaluation remain required.

## Gate 7: Monitoring And Incident Preparedness

Required evidence:

- `HISTORYGUIDE_LOG_FORMAT=json`
- centralized request log search by `X-HistoryGuide-Request-Id`
- dashboard or alert notes from `docs/monitoring_alert_examples.md`
- incident path from `docs/incident_response_checklist.md`
- rollback path from `docs/backup_rollback_drill.md`

Proceed only when monitoring can detect:

- `GET /ready` failures
- repeated `status_code = 401`
- repeated `status_code >= 500`
- `/api/genios/` requests with `elapsed_ms > 1000`
- `unsourced_exhibits`
- `visitor_state_integrity_issues`
- `audit_logs_empty`
- `rollback_candidate`

Block production-like promotion when:

- request ids are not searchable
- operational alerts cannot be checked
- no incident owner is assigned
- rollback path is unknown for rollback-sensitive changes

## Gate 8: Evidence Package

Required checklist:

```text
docs/operator_evidence_package_checklist.md
```

Proceed only when the package contains:

- runtime config output
- deployment self-check output
- staging database validation output
- backup and restore rehearsal evidence
- source and quality report summaries
- Visitor State integrity evidence
- GeniOS handoff evidence
- audit log evidence
- monitoring or incident evidence when applicable
- final decision and owner

Block when:

- the package includes secret values
- the package relies on placeholder examples as real evidence
- the package lacks request ids for critical backend calls
- the package lacks a final proceed, proceed_with_warnings, blocked, or rollback_required decision

## Final Decision Rules

Use:

- `proceed` only when every required gate passes
- `proceed_with_warnings` only when warnings are documented, accepted by the decision owner, and do not affect source safety, Visitor State integrity, readiness, auth, or rollback path
- `blocked` when any required gate fails
- `rollback_required` when restoring previous data or deployment state is required

Passing tests alone are not production readiness evidence. Never use passing tests alone as proof of production readiness. The decision must be based on current environment evidence, not only local test results.

After recording the final decision, use `docs/operator_final_prerun_checklist.md` in the final minutes before the run starts. The pre-run checklist should confirm the evidence chain, request ids, source-safety gates, monitoring readiness, incident owner, rollback owner, and final proceed/blocked/rollback decision.

## Boundary Reminder

This checklist decides whether backend operational evidence is sufficient for a selected run. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not certify Web/H5 or GeniOS production readiness outside the backend integration contract.
