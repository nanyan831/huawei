# Production Readiness Decision Example

This example shows how an operator can fill `docs/production_readiness_decision_checklist.md` after collecting backend evidence for a production-like run, public demo, museum-site rehearsal, or real visitor-facing backend run.

This example uses placeholder values only. It is not evidence that any real staging, production-like, museum-site, or production deployment has been validated.

This example is a backend decision record only. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## Decision Metadata

- decision date: `2026-09-27`
- decision owner: `example-decision-owner`
- environment: `staging-example`
- run type: `museum-site rehearsal`
- backend base URL: `https://staging-historyguide.example.test`
- backend version or source revision: `example-revision-001`
- database backend: `PostgreSQL example`
- database URL label, not secret: `staging-postgres-example`
- Web/H5 origin: `https://museum-h5.example.test`
- GeniOS environment: `genios-staging-example`
- operator evidence package path: `docs/examples/operator_evidence_package.example.md`
- final decision: `proceed_with_warnings`

## Required Evidence Attached

- `docs/staging_validation_record.md`: completed placeholder record path recorded
- `docs/operator_evidence_package_checklist.md`: completed placeholder package path recorded
- `docs/examples/operator_evidence_package.example.md`: formatting example only
- `docs/backup_rollback_drill.md`: rollback-sensitive path reviewed
- `docs/genios_handoff_evidence_template.md`: required because generated explanation may be displayed
- `docs/web_h5_integration_checklist.md`: required because browser client participates
- `docs/monitoring_alert_examples.md`: monitoring signals reviewed
- `docs/incident_response_checklist.md`: incident owner and response path reviewed

Placeholder examples are not evidence:

- `docs/examples/staging_validation_record.example.md`
- `docs/examples/deployment_environment_validation.example.md`
- `docs/examples/backend_readiness_validation.example.md`
- `docs/examples/operator_evidence_package.example.md`
- `docs/examples/genios_handoff_evidence.example.md`
- `docs/examples/operational_alerts_attention_required.example.json`

## Gate 1: Runtime Configuration

Commands recorded:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

Decision:

- `HISTORYGUIDE_API_KEY`: configured, value not preserved
- `HISTORYGUIDE_OPERATOR_API_KEY`: configured, value not preserved
- operator key separation: pass
- `HISTORYGUIDE_CORS_ORIGINS`: explicit Web/H5 origin
- `HISTORYGUIDE_LOG_FORMAT=json`: pass
- secret values printed or preserved: no
- gate result: pass

## Gate 2: Read-Only Runtime Self-Check

Commands recorded:

```powershell
python scripts\deployment_self_check.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key>
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --session-id staging-session-001 --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Checks recorded:

- `GET /health`: pass
- `GET /ready`: pass
- `GET /api/system/database`: pass
- `GET /api/system/access-policy`: pass
- `GET /api/system/security-status`: pass
- `GET /api/system/operational-alerts`: pass
- operational alerts have no `severity=fail`: yes
- `X-HistoryGuide-Request-Id`: `example-ready-001`, `example-alerts-001`, `example-handoff-001`
- gate result: pass

## Gate 3: Database And Migration

Commands recorded:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Decision:

- isolated migration rehearsal: pass
- expected Alembic head: `0002_audit_logs`
- core tables present: yes
- exhibit count: `42`
- empty `source_reference` count: `0`
- Visitor State count: `3`
- visit-event count: `7`
- audit-log count: `18`
- gate result: pass

This gate does not run migrations through `validate_staging_database.py`, does not import records, does not write audit logs, does not validate historical accuracy, does not run RAG, and does not generate explanation content.

## Gate 4: Data Safety And Backup

Commands recorded:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.example.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.example.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.example.json
python scripts\import_exhibits.py --dry-run data\verified-exhibits.example.json
```

Decision:

- verified seed file passed manual source review: placeholder yes
- every real exhibit record has non-empty `source_reference`: yes
- backup export completed before the change: yes
- backup verification passed: yes
- restore rehearsal passed: yes
- import dry-run passed: yes
- rollback owner recorded: yes
- gate result: pass

## Gate 5: Visit Flow

Checks recorded:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

Decision:

- one real visit uses one stable `session_id`: `staging-session-001`
- `visitor_type`: `freshman`
- QR scan or exhibit-entry events recorded through visit events: yes
- Visitor State integrity issue count: `0`
- recommendations and route plan are structured and explainable: yes
- visit summary is structured and does not generate natural-language recap text: yes
- gate result: pass

## Gate 6: GeniOS Handoff And Source Safety

Checks recorded:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Decision:

- `grounding_sources_complete=true`
- `source_safety.ready_for_generation=true`
- `missing_exhibit_ids=[]`
- `unsourced_exhibit_ids=[]`
- preflight `ready_for_handoff=true`
- generated explanation display: allowed by backend source-safety gate
- gate result: pass

This gate checks backend handoff data only. It does not define GeniOS prompts, does not run RAG, and does not judge generated historical prose.

## Gate 7: Monitoring And Incident Preparedness

Decision:

- `HISTORYGUIDE_LOG_FORMAT=json`: pass
- centralized request log search by `X-HistoryGuide-Request-Id`: pass
- dashboard or alert notes from `docs/monitoring_alert_examples.md`: reviewed
- incident path from `docs/incident_response_checklist.md`: reviewed
- rollback path from `docs/backup_rollback_drill.md`: reviewed
- repeated `status_code = 401`: none from expected clients
- repeated `status_code >= 500`: none
- `/api/genios/` requests with `elapsed_ms > 1000`: none
- `unsourced_exhibits`: `0`
- `visitor_state_integrity_issues`: `0`
- `audit_logs_empty`: false
- `rollback_candidate`: false
- gate result: pass

## Gate 8: Evidence Package

Decision:

- operator evidence package: `docs/examples/operator_evidence_package.example.md`
- package contains runtime config output: placeholder yes
- package contains deployment self-check output: placeholder yes
- package contains staging database validation output: placeholder yes
- package contains backup and restore rehearsal evidence: placeholder yes
- package contains source and quality report summaries: placeholder yes
- package contains Visitor State integrity evidence: placeholder yes
- package contains GeniOS handoff evidence: placeholder yes
- package contains audit log evidence: placeholder yes
- package contains monitoring or incident evidence: placeholder yes
- package contains final decision and owner: yes
- package includes secret values: no
- package relies on placeholder examples as real evidence: no
- gate result: pass

## Final Decision

Decision: `proceed_with_warnings`

Allowed final decisions:

- `proceed`
- `proceed_with_warnings`
- `blocked`
- `rollback_required`

Warnings accepted:

- This example is placeholder formatting only and must be replaced with real command output before any real production-like, museum-site, or visitor-facing run.
- The decision applies only to backend operational evidence and does not certify Web/H5 or GeniOS production readiness outside the backend integration contract.

Blocking issues:

- none in this placeholder example

Rollback owner:

- `example-rollback-owner`

Follow-up owner:

- `example-follow-up-owner`

Follow-up date:

- `2026-09-28`

Passing tests alone are not production readiness evidence. Never use passing tests alone as proof of production readiness.

## Boundary Reminder

This example decides whether backend operational evidence is sufficient for a selected run. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not certify Web/H5 or GeniOS production readiness outside the backend integration contract.
