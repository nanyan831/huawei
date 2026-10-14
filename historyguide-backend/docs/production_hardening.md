# Production Hardening Notes

This document lists production hardening work for the NK HistoryGuide backend. It is not a claim that the current MVP is production-ready. The current verified database path is SQLite for local MVP and demo use.

The backend remains limited to FastAPI APIs, exhibit data, Visitor State, recommendations, route candidates, GeniOS collaboration packages, tests, and documentation. It does not train models, replace GeniOS, perform RAG retrieval, generate explanation text, or implement digital humans, AR, or VR.

## Current Verified State

Verified today:

- FastAPI service startup
- health and readiness endpoints
- SQLite-backed MVP database initialization
- optional API key protection for business APIs
- explicit CORS allowlist configuration
- exhibit import dry-run and export workflows
- source and quality reporting for exhibit data
- GeniOS context, grounding, preflight, and handoff packages
- Alembic migration scaffold for the current schema
- read-only staging database validation for schema and data gates

Not yet production-complete:

- staging validation of the Alembic migration path
- PostgreSQL staging verification
- read-only staging database validation on the target database
- database backup and restore automation
- managed secrets handling
- role-based administration
- centralized logs and monitoring
- GeniOS production RAG setup
- Web/H5 production experience

## Environment Gate

Before any shared or public deployment, configure:

```text
HISTORYGUIDE_API_KEY=<strong-secret>
HISTORYGUIDE_OPERATOR_API_KEY=<strong-operator-secret>
HISTORYGUIDE_CORS_ORIGINS=<explicit-web-h5-origins>
HISTORYGUIDE_DATABASE_URL=<verified-database-url>
```

Checks:

- `HISTORYGUIDE_API_KEY` must not be empty outside local demos or trusted private networks.
- `HISTORYGUIDE_OPERATOR_API_KEY` should be set separately when audit logs or operational alerts are exposed outside a trusted local environment.
- `HISTORYGUIDE_OPERATOR_API_KEY` should not reuse the ordinary business API key.
- `HISTORYGUIDE_CORS_ORIGINS` must list explicit browser origins, not an open wildcard.
- `HISTORYGUIDE_DATABASE_URL` must point to the intended database for that environment.
- Secrets should come from the deployment platform secret store, not from committed files.

Run the runtime config validator before staging or production-like deployment:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

The validator checks API key presence, operator key separation, CORS wildcard risk, database URL profile risk, log level, and log format without printing secret values. It does not connect to the database. It is a deployment gate only; it does not validate historical content, import records, call GeniOS, run RAG, or generate explanation content.

## Pre-Deployment Checks

Run:

```powershell
python -m pytest
```

Then start the service and check:

```http
GET /health
GET /ready
GET /api/system/database
GET /openapi.json
```

Expected:

- `/health` returns service status.
- `/ready` returns `database: ok`.
- `/api/system/database` reports the expected backend and persistence mode without exposing the full database URL.
- `/openapi.json` contains the expected route groups.

For protected staging or production-like environments, also verify:

```http
GET /api/system/security-status
```

Expected:

- the response reports whether `HISTORYGUIDE_API_KEY` and `HISTORYGUIDE_OPERATOR_API_KEY` are configured
- the response lists header names and protected path groups without exposing secret values

The same read-only checks can be run with:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

The script checks health, readiness, database status, OpenAPI availability, security status, and operational alerts. It does not write to the database, prints returned `X-HistoryGuide-Request-Id` values for log correlation, and does not print key values.

Run the stronger read-only backend readiness validator before production-like handoff or visitor-facing backend runs:

```powershell
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

The validator checks readiness, database status, operational alerts, exhibit source and quality reports, audit log stats, Visitor State integrity, visit events, recommendations, route plan, visit summary, GeniOS grounding, GeniOS preflight, and GeniOS handoff source safety. It is read-only, does not write to the database, does not print key values, does not validate historical accuracy, does not run RAG, and does not generate explanation content.

Use `docs/examples/backend_readiness_validation.example.md` only as placeholder formatting guidance for recording validator output in operator evidence packages and production readiness decisions. The example is not evidence that any real staging, production-like, or museum deployment has been validated.

## Data Backup Gate

Before reset, migration, or environment move, export exhibit records:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.json
python scripts\rehearse_migrations.py
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Also keep:

- original verified seed JSON files
- source packages referenced by `source_reference`
- import logs or operator notes
- dry-run output for the imported seed file

Do not reset a database containing verified museum records without a reviewed export.

The backup verifier checks JSON structure, duplicate ids, required fields, and `source_reference` presence without connecting to the database. It does not prove historical accuracy and does not import records.

The restore rehearsal imports the backup into an isolated in-memory SQLite database, checks restored source and quality reports, then destroys the temporary database. It does not modify the configured application database and does not prove historical accuracy.

The migration rehearsal runs `alembic upgrade head` against an isolated temporary SQLite database, verifies the current Alembic revision and core tables, then removes the temporary database by default. It does not modify the configured application database, does not import records, does not validate real museum data, does not prove historical accuracy, and does not make PostgreSQL production-ready.

The staging database validator connects to the configured target database with read-only checks after migrations and import. It checks core tables, current Alembic head, exhibit count, empty `source_reference` values, Visitor State count, visit-event count, and audit-log count. It does not run migrations, import records, write audit logs, validate historical accuracy, run RAG, or generate explanation content.

## SQLite Boundary

SQLite is acceptable for:

- local development
- local demos
- small private proof-of-concept runs
- fixture-based testing

SQLite is not enough by itself for:

- concurrent public traffic
- multi-instance deployment
- managed backup and restore
- formal schema migration history
- operational monitoring

If a deployment needs those production properties, move through the PostgreSQL migration gate below.

## PostgreSQL Migration Gate

Do not switch to PostgreSQL only by changing `HISTORYGUIDE_DATABASE_URL`.

Before PostgreSQL production use:

1. Review the Alembic scaffold in `alembic.ini` and `migrations/`.
2. Apply the initial migration from `migrations/versions/0001_initial_schema.py`.
3. Apply migrations to a staging PostgreSQL database.
4. Run `python scripts\validate_staging_database.py` against the staging database.
5. Import a reviewed real exhibit seed file into staging.
6. Run `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits`.
7. Run source and quality reports in staging.
8. Create a test Visitor State and visit-event timeline in staging.
9. Run `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`.
10. Verify GeniOS grounding, preflight, and handoff in staging.
11. Confirm export works from staging.
12. Document rollback steps.
13. Only then promote the database URL to a production environment.

Required staging checks:

```http
GET /ready
GET /api/system/database
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Before generated explanation, confirm:

```text
source_safety.ready_for_generation=true
```

## API Key Check

When `HISTORYGUIDE_API_KEY` is configured:

- protected business APIs must reject requests without `X-HistoryGuide-Api-Key`
- protected business APIs must reject incorrect keys
- protected business APIs must accept the configured key
- `/health`, `/ready`, `/api/system/database`, `/openapi.json`, and docs remain reachable for deployment probes

The API key is a deployment hardening control. It is not a full user account or role-permission system.

When `HISTORYGUIDE_OPERATOR_API_KEY` is configured:

- audit and operational APIs must reject requests without `X-HistoryGuide-Operator-Key`
- audit and operational APIs must reject incorrect operator keys
- audit and operational APIs must reject the ordinary `X-HistoryGuide-Api-Key` when a separate operator key is configured
- audit and operational APIs must accept the configured operator key
- `GET /api/system/security-status` must require `X-HistoryGuide-Operator-Key` and must not return secret values
- `GET /api/system/access-policy` must require `X-HistoryGuide-Operator-Key` and report coarse access boundaries without exposing key values when the operator key is configured
- access policy output must be treated as coarse deployment documentation, not full RBAC

The operator key separates operational review endpoints from ordinary business API clients. It is still not a full role-based account system.

## CORS Check

For browser-based Web/H5 integration:

- set only explicit origins in `HISTORYGUIDE_CORS_ORIGINS`
- include local development origins only in local or staging environments
- remove unused origins before public deployment
- keep CORS empty when browsers do not call the backend directly

## Runtime Monitoring Checklist

At minimum, collect:

- application startup logs
- backend request completion logs with `X-HistoryGuide-Request-Id`
- deployment self-check output with returned `X-HistoryGuide-Request-Id` values
- request logs from the hosting platform
- readiness failures
- database connection failures
- import/export operator logs
- GeniOS handoff failures caused by missing exhibit references
- source-safety failures caused by unsourced grounding exhibits

Operational alerts should prioritize:

- `/ready` failures
- repeated `401` responses from expected GeniOS or Web/H5 clients
- repeated missing exhibit references
- source report showing unexpected unsourced real exhibits
- Visitor State integrity issue count increasing during demos or live visits

Use `X-HistoryGuide-Request-Id` to correlate Web/H5, GeniOS, operator tooling, backend request logs, and hosting platform logs. Treat it as a troubleshooting correlation id only; it is not authentication, visitor identity, or historical evidence.

Set `HISTORYGUIDE_LOG_FORMAT=json` when logs are ingested by a centralized logging platform. Structured request logs include these stable fields:

- `event`
- `service_id`
- `request_id`
- `http_method`
- `path`
- `status_code`
- `elapsed_ms`

Do not use structured log fields as visitor profile data, historical source references, historical evidence, or GeniOS prompt input. They are operational correlation metadata only.

Use `docs/centralized_logging.md` for the JSON request log field reference, example payload at `docs/examples/structured_request_log.json`, suggested filters, and redaction boundaries. The logging guide is operational documentation only; it does not validate historical content, run RAG, or generate explanation content.

Use `docs/monitoring_alert_examples.md` for production-like alert rule examples that combine `GET /api/system/operational-alerts`, structured request logs, `X-HistoryGuide-Request-Id`, source-safety fields, Visitor State integrity checks, Web/H5 scan events, and GeniOS handoff readiness. Use `docs/examples/operational_alerts_attention_required.example.json` only as a placeholder alert payload example, not as evidence from a real deployment.

Use `docs/operator_evidence_package_checklist.md` to package production-like operator evidence after staging validation, verified data import, Web/H5 checks, GeniOS handoff, monitoring setup, incident response, or rollback-sensitive changes. The package should preserve command outputs, request ids, source-safety fields, Visitor State integrity evidence, audit evidence, monitoring signals, and the final proceed/blocked/rollback decision without preserving secret values. Use `docs/examples/operator_evidence_package.example.md` only as placeholder formatting guidance for a completed package; it is not evidence that any real staging, production-like, or museum deployment has been validated.

Use `docs/production_readiness_decision_checklist.md` before production-like runs, public demos, museum-site rehearsals, or real visitor-facing backend runs. It converts runtime config, deployment self-check, database validation, data safety, visit flow, GeniOS handoff, monitoring, incident readiness, and evidence package gates into a `proceed`, `proceed_with_warnings`, `blocked`, or `rollback_required` decision. Use `docs/examples/production_readiness_decision.example.md` only as placeholder formatting guidance for the final go/no-go record. Passing tests alone are not production readiness evidence.

Use `docs/operator_final_prerun_checklist.md` immediately before production-like runs, public demos, museum-site rehearsals, or real visitor-facing backend runs. It is the final backend operator gate for environment access, read-only backend state, data and rollback safety, real visit session integrity, GeniOS handoff source safety, monitoring readiness, incident ownership, rollback ownership, and final proceed/blocked/rollback decision review.

Use `docs/operator_post_run_review.md` after production-like runs, public demos, museum-site rehearsals, or real visitor-facing backend runs. It closes the backend operational loop by recording actual outcome, request ids, source-safety status, Visitor State integrity, audit evidence, monitoring signals, incident handling, rollback handling, evidence package updates, and follow-up owners.

Use `docs/staging_validation_record.md` to record staging evidence before production-like deployment. The record should include runtime config validation, migration checks, backup and restore checks, deployment self-check request ids, source-safety results, GeniOS handoff readiness, and centralized logging checks. It is an operator record, not proof of historical accuracy.

Use `docs/backup_rollback_drill.md` before production-like data, migration, deployment, Web/H5, or GeniOS handoff changes. The drill captures pre-change runtime checks, `python scripts\export_exhibits.py`, `python scripts\verify_exhibit_backup.py --require-non-empty`, `python scripts\rehearse_exhibit_restore.py`, `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`, deployment self-check request ids, rollback decision criteria, and post-rollback source-safety checks.

Use `docs/operator_runbook.md` as the operator-facing sequence across runtime config validation, deployment self-check, data safety, migration, local fixture demos, Web/H5 integration, GeniOS handoff, incident triage, and evidence preservation. Use `docs/incident_response_checklist.md` for detailed backend incident handling across readiness/database failures, repeated auth failures, source-safety blocks, Visitor State drift, Web/H5 scan failures, GeniOS handoff failures, logging correlation gaps, and rollback triggers. Use `docs/examples/deployment_environment_validation.example.md` and `docs/examples/backend_readiness_validation.example.md` only as placeholder formatting guidance for deployment and readiness validation records. They coordinate existing backend tools and do not replace GeniOS or generate explanation content.

## Rollback Checklist

Before a production-like change:

- export exhibit data
- verify exported exhibit backups
- rehearse exhibit restore
- save the exact seed file used for import
- record the old environment variable values
- record the new environment variable values
- confirm how to restore the previous database or volume
- confirm how to redeploy the previous backend image or source revision
- confirm how to restore Web/H5 and GeniOS integration settings
- rerun `GET /api/genios/handoff/{session_id}` after rollback

Rollback is incomplete unless exhibit data, Visitor State expectations, and GeniOS integration settings are all returned to the known working state.

## Production Readiness Statement

The MVP backend can support local demos, structured GeniOS integration, Web/H5 API integration, and verified exhibit seed import. A full production system still requires real museum data, GeniOS RAG setup, staging-validated migrations, managed deployment, monitoring, backup and restore operations, and stronger authentication if administrative APIs are added later.
