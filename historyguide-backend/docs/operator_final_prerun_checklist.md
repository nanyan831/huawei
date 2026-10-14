# Operator Final Pre-Run Checklist

Use this checklist in the final minutes before a production-like run, public demo, museum-site rehearsal, or real visitor-facing backend run.

This checklist ties together the staging validation record, backend readiness validation, operator evidence package, and production readiness decision. It is backend operational guidance only. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## Required Inputs

Have these real records ready before starting:

- completed `docs/staging_validation_record.md`
- completed `docs/operator_evidence_package_checklist.md`
- completed `docs/production_readiness_decision_checklist.md`
- completed `docs/genios_handoff_evidence_template.md` when generated explanation may be displayed
- completed `docs/web_h5_integration_checklist.md` when a browser client participates
- completed `docs/backup_rollback_drill.md` when data, migration, deployment, Web/H5, or GeniOS handoff changes are rollback-sensitive
- monitoring notes based on `docs/monitoring_alert_examples.md`
- incident owner and path based on `docs/incident_response_checklist.md`

Placeholder examples are formatting aids only:

- `docs/examples/staging_validation_record.example.md`
- `docs/examples/deployment_environment_validation.example.md`
- `docs/examples/backend_readiness_validation.example.md`
- `docs/examples/operator_evidence_package.example.md`
- `docs/examples/production_readiness_decision.example.md`
- `docs/examples/genios_handoff_evidence.example.md`
- `docs/examples/operational_alerts_attention_required.example.json`

Do not treat placeholder examples as real staging, production-like, museum-site, or production evidence.

## Gate 1: Environment And Access

Confirm:

- `HISTORYGUIDE_API_KEY` is configured for shared, public, or production-like business APIs
- `HISTORYGUIDE_OPERATOR_API_KEY` is configured for operator endpoints outside trusted local use
- business key and operator key are different
- `HISTORYGUIDE_CORS_ORIGINS` contains explicit Web/H5 origins
- `HISTORYGUIDE_LOG_FORMAT=json` is configured when centralized logs are expected
- no command output or package preserves key values

Run or confirm preserved output:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

Stop when API keys are missing for the intended exposure, CORS is unsafe, log format is not ready for expected centralized logging, or secret values appear in evidence.

## Gate 2: Read-Only Backend State

Run or confirm preserved output:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Confirm:

- `GET /health` passes
- `GET /ready` passes
- `GET /api/system/database` reports the intended database boundary
- `GET /api/system/access-policy` matches expected caller groups
- `GET /api/system/security-status` confirms key controls without exposing key values
- `GET /api/system/operational-alerts` has no `severity=fail`
- `X-HistoryGuide-Request-Id` values are preserved

Stop when readiness fails, the database backend is unexpected, operator endpoints accept the wrong key type, operational alerts report fail-level issues, or request ids cannot be preserved.

## Gate 3: Data, Migration, And Rollback

Run or confirm preserved output:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
python scripts\export_exhibits.py <backup-file>
python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty
python scripts\rehearse_exhibit_restore.py <backup-file>
python scripts\import_exhibits.py --dry-run <verified-seed-file>
```

Confirm:

- migration rehearsal passed
- target database is at the expected Alembic head
- exhibit count matches the run plan
- unsourced exhibit count is zero for verified exhibit data
- audit-log count is non-zero after state-changing checks
- backup verification passed
- restore rehearsal passed
- rollback owner and rollback path are recorded

Stop when backups cannot be verified, restore rehearsal fails, source references are missing, audit logs are missing after state-changing checks, or rollback ownership is unclear.

## Gate 4: Real Visit Session

Confirm these calls were run for one stable `session_id`:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

Confirm:

- `visitor_type` is `freshman`, `alumnus`, or `tourist`
- current exhibit exists
- visited history references existing exhibits
- visit-event count matches the run plan
- Visitor State integrity issue count is zero
- recommendations and route plan are structured and explainable
- visit summary is structured and does not generate natural-language recap text

Stop when Visitor State references missing exhibits, visit-event timeline drifts from Visitor State, visit events are missing when required, or Web/H5 cannot preserve request ids.

## Gate 5: GeniOS Handoff Source Safety

Confirm these calls were run for the same `session_id`:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Generated explanation display is allowed by the backend gate only when:

- `grounding_sources_complete=true`
- `source_safety.ready_for_generation=true`
- `missing_exhibit_ids=[]`
- `unsourced_exhibit_ids=[]`
- preflight `ready_for_handoff=true`
- `X-HistoryGuide-Request-Id` values are preserved across backend, Web/H5, GeniOS, and operator notes

Stop generated explanation display when `grounding_sources_complete=false`, `source_safety.ready_for_generation=false`, any grounding exhibit is unsourced, any referenced exhibit id is missing, or request ids cannot be correlated.

## Gate 6: Monitoring And Incident Readiness

Confirm monitoring or log queries can detect:

- `GET /ready` failures
- repeated `status_code = 401`
- repeated `status_code >= 500`
- `/api/genios/` requests with `elapsed_ms > 1000`
- `unsourced_exhibits`
- `visitor_state_integrity_issues`
- `audit_logs_empty`
- `rollback_candidate`

Confirm:

- incident owner is assigned
- rollback owner is assigned
- `docs/incident_response_checklist.md` is available to the operator
- `docs/backup_rollback_drill.md` is available if rollback may be required

Stop when request ids are not searchable, operational alerts cannot be checked, incident ownership is unclear, or rollback path is unknown for rollback-sensitive changes.

## Gate 7: Final Decision

Open the completed `docs/production_readiness_decision_checklist.md`.

Proceed only when the final decision is one of:

- `proceed`
- `proceed_with_warnings`

Stop when the final decision is one of:

- `blocked`
- `rollback_required`

`proceed_with_warnings` is acceptable only when the warnings are documented, accepted by the decision owner, and do not affect source safety, Visitor State integrity, readiness, auth, or rollback path.

Passing tests alone are not production readiness evidence. Never use passing tests alone as proof of production readiness.

## Final Operator Statement

Before the run starts, record:

- final decision:
- decision owner:
- operator evidence package path:
- production readiness decision path:
- backend base URL:
- `session_id`:
- rollback owner:
- incident owner:
- accepted warnings:
- blocking issues:

Do not preserve secret values, private GeniOS prompts, unreviewed generated historical text, database credentials, or visitor personal information not required for backend debugging.

After the run, complete `docs/operator_post_run_review.md` to record the actual backend outcome, request-id evidence, source-safety status, Visitor State integrity, audit evidence, monitoring or incident results, rollback status, evidence package updates, and follow-up owners.

## Boundary Reminder

This final pre-run checklist supports backend operation for a real museum visit Agent. It does not certify historical interpretation, does not approve museum source packages, does not replace GeniOS, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not certify Web/H5 or GeniOS production readiness outside the backend integration contract, does not implement digital humans, and does not implement AR/VR.
