# Operator Evidence Package Example

This example shows how an operator can assemble a backend evidence package after a staging validation, Web/H5 integration check, GeniOS handoff evidence run, museum-site rehearsal, or rollback-sensitive production-like change.

This example uses placeholder values only. It is not evidence that any real staging, production-like, or museum deployment has been validated.

This package is backend operational evidence only. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## Package Metadata

- package name: `example-staging-handoff-package-20260927`
- run type: `GeniOS handoff evidence run`
- operator: `example-operator`
- date: `2026-09-27`
- environment: `staging-example`
- backend base URL: `https://staging-historyguide.example.test`
- backend version or source revision: `example-revision-001`
- database backend: `PostgreSQL example`
- database URL label, not secret: `staging-postgres-example`
- Web/H5 origin: `https://museum-h5.example.test`
- GeniOS environment: `genios-staging-example`
- affected `session_id`: `staging-session-001`
- affected exhibit ids: `fixture-exhibit-001`, `fixture-exhibit-002`
- final decision: `proceed_with_warnings`

## Attached Evidence Files

- completed staging record: `evidence/staging_validation_record.20260927.example.md`
- backend readiness validation record: `docs/examples/backend_readiness_validation.example.md`
- deployment environment validation record: `docs/examples/deployment_environment_validation.example.md`
- GeniOS handoff evidence record: `docs/examples/genios_handoff_evidence.example.md`
- monitoring alert sample: `docs/examples/operational_alerts_attention_required.example.json`
- source review notes: `evidence/real_exhibit_seed_review.20260927.example.md`
- backup and rollback drill notes: `evidence/backup_rollback_drill.20260927.example.md`

Do not label placeholder examples as real staging, production-like, or museum evidence.

## Runtime Evidence

Commands recorded:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\deployment_self_check.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key>
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --session-id staging-session-001 --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Recorded results:

- runtime config validation result: pass
- API key presence check result: pass
- operator key separation check result: pass
- CORS wildcard risk result: pass
- database URL profile risk result: pass
- log format result: `HISTORYGUIDE_LOG_FORMAT=json`
- deployment self-check result: pass
- backend readiness validation result: pass
- `GET /health`: pass
- `GET /ready`: pass
- `GET /api/system/database`: pass
- `GET /api/system/access-policy`: pass
- `GET /api/system/security-status`: pass
- `GET /api/system/operational-alerts`: pass
- returned `X-HistoryGuide-Request-Id` values: `example-health-001`, `example-ready-001`, `example-alerts-001`, `example-handoff-001`

No secret values from `HISTORYGUIDE_API_KEY`, `HISTORYGUIDE_OPERATOR_API_KEY`, `X-HistoryGuide-Api-Key`, or `X-HistoryGuide-Operator-Key` are preserved.

## Data And Migration Evidence

Commands recorded:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.example.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.example.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.example.json
python scripts\import_exhibits.py --dry-run data\verified-exhibits.example.json
python scripts\rehearse_migrations.py
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Recorded results:

- verified seed file path: `data\verified-exhibits.example.json`
- source package location: `source-package-label-example`
- source review owner: `example-reviewer`
- backup file path: `backups\exhibits.before-change.example.json`
- backup verification result: pass
- restore rehearsal result: pass
- import dry-run result: pass
- migration rehearsal result: pass
- staging Alembic head: `0002_audit_logs`
- core table status: pass
- exhibit count: `42`
- unsourced exhibit count: `0`
- Visitor State count: `3`
- visit-event count: `7`
- audit-log count: `18`

Historical facts were not created, inferred, rewritten, or generated to make the evidence look complete.

## Visit Flow Evidence

Requests recorded:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

Recorded results:

- `session_id`: `staging-session-001`
- `visitor_type`: `freshman`
- current exhibit: `fixture-exhibit-002`
- visited history: `fixture-exhibit-001`, `fixture-exhibit-002`
- visit-event count: `3`
- remaining time: `18`
- recommendation count: `2`
- route plan item count: `2`
- integrity issue count: `0`
- returned `X-HistoryGuide-Request-Id` values: `example-visit-001`, `example-events-001`, `example-integrity-001`

Visitor State follows one real visit session, not a generic chatbot conversation.

## GeniOS Handoff Evidence

Requests recorded:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Recorded results:

- `grounding_exhibit_ids`: `fixture-exhibit-001`, `fixture-exhibit-002`
- `grounding_sources_complete=true`
- `source_safety.ready_for_generation=true`
- `missing_exhibit_ids=[]`
- `unsourced_exhibit_ids=[]`
- preflight `ready_for_handoff=true`
- handoff request id: `example-handoff-001`
- GeniOS consumed backend handoff package: `yes, placeholder example`
- generated explanation display was allowed: `no; fixture-only placeholder, no review/finalize evidence`

These legacy Handoff fields are preflight signals, not permission to display. Fixture records and absent review/finalize evidence require blocking generated explanation display, regardless of the placeholder values above.

This package does not define GeniOS prompts, does not run RAG, and does not judge generated historical prose.

## Monitoring And Incident Evidence

Recorded results:

- structured request log query for `X-HistoryGuide-Request-Id`: pass
- `HISTORYGUIDE_LOG_FORMAT=json` validation result: pass
- `GET /api/system/operational-alerts` output: pass
- request logs for `status_code = 401`: no unexpected repeated failures
- request logs for `status_code >= 500`: none
- request logs for `/api/genios/` with `elapsed_ms > 1000`: none
- incident notes from `docs/incident_response_checklist.md`: not applicable
- alert level reached: none
- `rollback_candidate`: false

Stop or escalate if later monitoring evidence shows source-safety failure, Visitor State drift, repeated auth failure from expected clients, readiness failure, or missing audit evidence after state-changing operations.

## Audit Evidence

Requests recorded:

```http
GET /api/audit-logs/stats
GET /api/audit-logs
```

Recorded results:

- total audit logs: `18`
- latest audit timestamp: `2026-09-27T17:40:00Z`
- `visitor_state_created`: present
- `visitor_state_updated`: present
- `visit_event_recorded`: present
- `exhibits_imported`: present
- returned `X-HistoryGuide-Request-Id` values: `example-audit-stats-001`, `example-audit-list-001`

Audit logs are operator traceability. They are not visitor identity, not visitor profile data, not historical evidence, not source references, not RAG content, not GeniOS prompt input, and not generated explanation content.

## Redaction Checklist

Removed or avoided:

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

- final decision: `proceed_with_warnings`
- blocking issues: none
- warnings accepted: staging example uses placeholder evidence and must be replaced by real command output before any real run
- rollback owner: `example-rollback-owner`
- follow-up owner: `example-follow-up-owner`
- follow-up date: `2026-09-28`

Use `docs/production_readiness_decision_checklist.md` before treating a completed package as support for a production-like, public demo, museum-site rehearsal, or real visitor-facing backend decision.
