# NK HistoryGuide Backend

NK HistoryGuide is a backend service for a real museum visit scenario. It is not a general Nankai history chatbot. The backend focuses on exhibit data, visitor state, visit context, and structured collaboration with GeniOS.

## Project Positioning

NK HistoryGuide should understand:

- who the visitor is, such as freshman, alumnus, or tourist
- which exhibit the visitor is viewing
- what the visitor has already visited
- what topics the visitor is interested in
- how much time remains in the visit

GeniOS is responsible for dialogue, RAG, knowledge retrieval, and generated explanations. This backend is responsible for context, data, state, and API contracts.

## Codex Development Boundary

This backend owns:

- FastAPI service
- data model design
- exhibit management
- Visitor State management
- GeniOS collaboration interfaces
- tests
- deployment and development documentation

This backend does not own:

- large model training
- replacing the GeniOS Agent
- digital human development
- AR or VR systems
- unrelated feature expansion

## Current Stage

Current checkpoint: local curator workspace and atomic evidence/exhibit intake.
Production and Coze release gates remain NO-GO until real evidence is collected.

Implemented:

- FastAPI application factory
- health check endpoint
- database readiness endpoint
- database status endpoint for migration readiness
- operational alerts endpoint for deployment and demo checks
- Alembic migration scaffold for staging and future PostgreSQL work
- structured audit log table and read endpoint
- audit log stats endpoint for lightweight operational monitoring
- optional API key protection for business APIs
- optional operator API key protection for audit and operational endpoints
- security status endpoint for deployment and operator-key verification
- request id response header and lightweight request completion logs
- read-only deployment self-check script for health, readiness, database, security, OpenAPI, and operational alerts
- read-only backend readiness validator for runtime, data, Visitor State, GeniOS handoff, source-safety, and audit gates
- placeholder-only backend readiness validation evidence example for operator packages and go/no-go decisions
- offline exhibit backup verification script for migration and restore checks
- isolated in-memory exhibit restore rehearsal script for backup recovery checks
- read-only staging database validation script for table, migration, exhibit-source, and audit-log gates
- basic logging setup
- dependency files
- pytest smoke test
- SQLite database initialization
- Exhibit SQLAlchemy model
- exhibit API schemas
- exhibit service layer
- exhibit list and detail query endpoints
- exhibit list pagination
- exhibit metadata facets endpoint
- exhibit metadata quality report endpoint
- exhibit source reference report endpoint
- Visitor State SQLAlchemy model
- Visitor State API schemas
- Visitor State service layer
- visitor session list endpoint with filter and pagination
- visitor session stats endpoint
- visitor session integrity report endpoint
- per-session visitor session integrity endpoint
- visitor session create, read, and update endpoints
- audit logs for Visitor State create and update operations
- exhibit visit event endpoint for real visit flow updates
- audit logs for exhibit visit event recording
- visit event timeline endpoint with pagination for recorded exhibit-entry history
- exhibit reference validation for visitor state
- rule-based exhibit recommendation service
- recommendation endpoint with explainable reasons and priorities
- rule-based visit route plan service
- route plan endpoint with ordered route items and simple duration estimates
- GeniOS context package schema
- GeniOS context assembly service
- GeniOS context package includes visit-event timeline
- GeniOS context package includes grounding exhibit ids for exhibit-level RAG input
- GeniOS capability discovery endpoint
- structured context endpoint for GeniOS collaboration
- structured grounding endpoint for GeniOS exhibit-level RAG preparation
- structured grounding source completeness fields for GeniOS fact-safety checks
- structured preflight endpoint for GeniOS handoff readiness checks
- structured handoff endpoint for GeniOS collaboration, including source safety and preflight
- structured visit summary endpoint
- structured visit summary includes visit-event timeline
- verified exhibit JSON seed format documentation
- real exhibit seed review checklist
- exhibit import service
- exhibit import CLI
- exhibit import dry-run validation
- exhibit import summary audit logs
- exhibit export service
- exhibit export CLI
- non-historical development fixture data
- validation for required fields, importance range, duplicate seed ids, and existing database ids
- validation that imported exhibit records include non-empty source references
- frontend and GeniOS API contract documentation
- GeniOS handoff example response in the API contract
- local end-to-end demo workflow documentation
- Web/H5 and GeniOS integration sequence documentation
- GeniOS handoff evidence template
- Web/H5 integration acceptance checklist
- backup and rollback drill
- operator runbook
- incident response checklist
- production-like monitoring alert examples
- operator evidence package checklist
- placeholder-only operator evidence package example
- production readiness decision checklist
- placeholder-only production readiness decision example
- final operator pre-run checklist
- operator post-run review template
- operational readiness documentation
- production hardening notes
- database migration notes
- consistent error response examples
- development database reset notes
- OpenAPI core path and tag checks
- MVP readiness checklist
- final MVP verification and handoff documentation
- environment variable based settings
- explicit CORS origin settings for browser-based Web/H5 integration
- Dockerfile and Docker ignore rules
- deployment notes

## Project Structure

```text
historyguide-backend/
  app/
    api/
      routes/
        audit_logs.py
        exhibits.py
        genios_context.py
        health.py
        recommendations.py
        route_plans.py
        visit_summaries.py
        visitor_states.py
    core/
      config.py
      logging.py
      request_context.py
      security.py
    database/
      base.py
      init_db.py
      session.py
    main.py
    models/
      audit_log.py
      exhibit.py
      visitor_state.py
    schemas/
      audit_log.py
      exhibit.py
      genios_context.py
      recommendation.py
      route_plan.py
      system.py
      visit_summary.py
      visitor_state.py
    services/
      audit_log_service.py
      exhibit_service.py
      exhibit_export_service.py
      exhibit_import_service.py
      genios_context_service.py
      recommendation_service.py
      route_plan_service.py
      visit_summary_service.py
      visitor_state_service.py
  data/
    example_exhibits.fixture.json
  docs/
    examples/
      backend_readiness_validation.example.md
      deployment_environment_validation.example.md
      genios_handoff_evidence.example.md
      operator_evidence_package.example.md
      operational_alerts_attention_required.example.json
      production_readiness_decision.example.md
      staging_validation_record.example.md
      structured_request_log.json
    api_contract.md
    backup_rollback_drill.md
    centralized_logging.md
    database_migrations.md
    deployment.md
    exhibit_seed_format.md
    genios_handoff_evidence_template.md
    incident_response_checklist.md
    local_demo_workflow.md
    monitoring_alert_examples.md
    mvp_handoff.md
    operator_evidence_package_checklist.md
    operator_final_prerun_checklist.md
    operator_post_run_review.md
    operator_runbook.md
    operational_readiness.md
    production_readiness_decision_checklist.md
    production_hardening.md
    real_data_import_runbook.md
    real_data_preimport_final_checklist.md
    real_exhibit_seed_review.md
    staging_validation_record.md
    web_h5_integration_checklist.md
    web_h5_genios_integration.md
  migrations/
    env.py
    script.py.mako
    versions/
      0001_initial_schema.py
      0002_audit_logs.py
      0003_evidence_governance.py
      0004_review_runs.py
      0005_history_review_runs.py
      0006_visitor_access_grants.py
      0007_source_approval_fingerprint.py
  scripts/
    deployment_self_check.py
    export_exhibits.py
    import_exhibits.py
    rehearse_exhibit_restore.py
    rehearse_migrations.py
    validate_backend_readiness.py
    validate_staging_database.py
    validate_runtime_config.py
    verify_exhibit_backup.py
  tests/
    conftest.py
    test_cors.py
    test_deployment_self_check.py
    test_exhibits.py
    test_exhibit_export.py
    test_exhibit_import.py
    test_rehearse_exhibit_restore.py
    test_rehearse_migrations.py
    test_validate_staging_database.py
    test_validate_runtime_config.py
    test_verify_exhibit_backup.py
    test_genios_context.py
    test_health.py
    test_openapi_contract.py
    test_recommendations.py
    test_route_plans.py
    test_visit_summaries.py
    test_visitor_states.py
  pyproject.toml
  Dockerfile
  requirements.txt
  requirements-dev.txt
```

## Local Setup

```powershell
cd .\historyguide-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --require-hashes -r requirements-dev.lock
```

## Run

Runtime and development dependencies are pinned with SHA-256 hashes in
`requirements.lock` and `requirements-dev.lock`. The Dockerfile installs the runtime
lock with `--require-hashes`. Range files remain the inputs for intentional upgrades;
see `docs/dependency_locking.md` for installation, updates, and verification limits.

The Windows Python 3.12 locked environment has been checked locally. Linux container
builds still require a working Docker daemon and separate validation.
The repository also contains `.github/workflows/ci.yml` for hash-locked installation,
backend and isolated operator-browser tests, Docker build, and a container readiness
smoke test. This workflow has not run remotely until these changes are pushed; a
passing local suite does not prove its Linux image build.

```powershell
uvicorn app.main:app --reload
```

Read-only deployment self-check against a running backend:

```powershell
python scripts\deployment_self_check.py --base-url http://127.0.0.1:8000
```

For a protected deployment, pass keys through parameters or environment variables:

```powershell
python scripts\deployment_self_check.py --base-url http://127.0.0.1:8000 --api-key <business-key> --operator-key <operator-key>
```

The self-check calls only read-only endpoints, prints returned `X-HistoryGuide-Request-Id` values for log correlation, and never prints configured key values.

Stronger read-only backend readiness validation against a running backend:

```powershell
python scripts\validate_backend_readiness.py --base-url http://127.0.0.1:8000 --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

For a visit-session handoff check, also pass:

```powershell
python scripts\validate_backend_readiness.py --base-url http://127.0.0.1:8000 --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

The readiness validator checks only read-only backend endpoints. It can validate readiness, database status, operational alerts, exhibit source and quality reports, audit log stats, Visitor State integrity, visit events, recommendations, route plan, visit summary, GeniOS grounding, GeniOS preflight, and GeniOS handoff source safety. It prints returned request ids for evidence correlation, does not write to the database, does not validate historical accuracy, does not run RAG, does not generate explanation content, does not print key values, and never prints configured key values.

Offline exhibit backup verification:

```powershell
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.json --require-non-empty
```

The backup verifier checks JSON structure, duplicate ids, field validation, and `source_reference` presence without connecting to the database. It does not prove historical accuracy and does not import records.

Isolated exhibit restore rehearsal:

```powershell
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.json
```

The restore rehearsal imports the backup into an isolated in-memory SQLite database, runs source and quality checks, and then destroys the temporary database. It does not modify the configured application database, and it does not prove historical accuracy.

Isolated Alembic migration rehearsal:

```powershell
python scripts\rehearse_migrations.py
```

The migration rehearsal runs `alembic upgrade head` against an isolated temporary SQLite database, verifies the current Alembic revision and core tables, then removes the temporary database by default. It does not modify the configured application database, does not import exhibit records, does not prove PostgreSQL production-ready status, and does not prove historical accuracy.

Read-only staging database validation after applying migrations:

```powershell
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

The staging database validator connects to the configured target database or a `--database-url` override and checks connectivity, core tables, the current Alembic head, exhibit count, empty `source_reference` values, Visitor State count, visit-event count, and audit-log count. It does not run migrations, import records, write audit logs, validate historical accuracy, run RAG, or generate explanation content.

After migrating an isolated PostgreSQL staging database, verify that claim approval revocation is serialized after a release transaction. This is an intentional write test and refuses to run without the acknowledgement flag; it creates uniquely named synthetic records and removes them by default:

```powershell
python scripts\verify_postgres_claim_release_lock.py --acknowledge-staging-write-test
```

Do not run this probe against production. A pass verifies this PostgreSQL row-lock boundary only; it does not replace curator review or Coze end-to-end validation.

Request tracing:

```text
X-HistoryGuide-Request-Id: <client-request-id>
```

Every response includes `X-HistoryGuide-Request-Id`. Web/H5 or GeniOS callers may send this header to correlate backend responses with client-side logs. If the caller omits it or sends an invalid value, the backend generates one. The request id is for troubleshooting only; it is not authentication, visitor identity, historical evidence, or a source of visitor profile data.

Health check:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "nk-historyguide-backend",
  "version": "0.1.0"
}
```

Readiness check:

```text
GET /ready
```

Expected response:

```json
{
  "status": "ready",
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "database": "ok"
}
```

Database status:

```text
GET /api/system/database
```

Expected response fields:

```text
service
version
backend
driver
persistence
schema_management
migration_target
production_note
```

The database status endpoint reports the configured SQLAlchemy backend without exposing the full database URL. It helps confirm whether the service is running on local SQLite or an external database before deployment and migration planning.

Operational alerts:

```text
GET /api/system/operational-alerts
```

The operational alerts endpoint summarizes backend readiness signals that matter before demos, staging checks, or GeniOS handoff: empty exhibit data, unsourced exhibits, exhibit metadata gaps, Visitor State timeline drift, and missing audit evidence. It returns structured `warn` and `fail` alerts only. It does not inspect historical accuracy, run RAG, infer visitor profiles, or generate explanation content.

Security status:

```text
GET /api/system/security-status
GET /api/system/access-policy
```

The security status endpoint reports whether optional business and operator API key controls are configured, which request headers are expected, and which paths remain public deployment probes. It never returns configured key values. When `HISTORYGUIDE_OPERATOR_API_KEY` is configured, this endpoint itself requires `X-HistoryGuide-Operator-Key`; when only `HISTORYGUIDE_API_KEY` is configured, it requires `X-HistoryGuide-Api-Key`.

The access policy endpoint reports coarse access groups for public probes, business APIs, operator APIs, and local operator scripts without exposing key values. It does not grant access and is not a user account or full RBAC system. When `HISTORYGUIDE_OPERATOR_API_KEY` is configured, this endpoint requires `X-HistoryGuide-Operator-Key`.

Exhibit APIs:

```text
GET /api/exhibits
GET /api/exhibits/facets
GET /api/exhibits/quality-report
GET /api/exhibits/source-report
GET /api/exhibits/{exhibit_id}
```

Optional filters:

```text
GET /api/exhibits?keyword=校训
GET /api/exhibits?period=近代
GET /api/exhibits?importance_min=3
GET /api/exhibits?limit=20&offset=0
```

The list endpoint supports optional `limit` and `offset` parameters for larger exhibit datasets.

The facets endpoint returns structured metadata counts for `periods`, `keywords`, `people`, and `themes`. It supports frontend filters, data review, and GeniOS setup. It does not generate historical content.

The quality report endpoint flags structured metadata gaps such as missing source references, empty keywords, empty themes, and empty people fields. It does not verify historical accuracy or generate missing content.

The source report endpoint groups exhibits by exact `source_reference` values and lists unsourced exhibit ids. It helps review verified data batches before GeniOS integration, without judging historical accuracy.

The current database is created automatically at `historyguide.db`. The service does not auto-seed historical exhibit facts, because museum history content must come from verified sources.

Environment configuration:

```text
HISTORYGUIDE_APP_NAME
HISTORYGUIDE_APP_VERSION
HISTORYGUIDE_SERVICE_ID
HISTORYGUIDE_LOG_LEVEL
HISTORYGUIDE_LOG_FORMAT
HISTORYGUIDE_DATABASE_URL
HISTORYGUIDE_SCHEMA_MODE
HISTORYGUIDE_CORS_ORIGINS
HISTORYGUIDE_API_KEY
HISTORYGUIDE_API_KEY_FILE
HISTORYGUIDE_API_KEY_NEXT
HISTORYGUIDE_API_KEY_NEXT_FILE
HISTORYGUIDE_OPERATOR_API_KEY
HISTORYGUIDE_OPERATOR_API_KEY_FILE
```

Set `HISTORYGUIDE_CORS_ORIGINS` to comma-separated Web/H5 origins when a browser client calls this backend directly. Leave it empty when CORS is not needed.

`HISTORYGUIDE_SCHEMA_MODE=auto_create` is the local-demo default. Set `HISTORYGUIDE_SCHEMA_MODE=migrated` in staging/production-like environments **after** applying and verifying Alembic migrations; startup then checks the current revision and model schema without creating missing tables. The runtime config validator fails shared profiles that still use `auto_create`. An unversioned legacy database requires the isolated adoption rehearsal in `docs/database_migrations.md` before any controlled cutover.

Set `HISTORYGUIDE_LOG_FORMAT=json` in production-like environments when logs are collected by a centralized logging platform. JSON request logs include `event`, `service_id`, `request_id`, `http_method`, `path`, `status_code`, and `elapsed_ms`. These fields are for troubleshooting and correlation only; they are not authentication, visitor identity, historical evidence, or prompt input for GeniOS.

Set `HISTORYGUIDE_API_KEY` in deployment to require `X-HistoryGuide-Api-Key` on business APIs. Leave it empty for local demos. Health, readiness, database status, and OpenAPI docs remain public for deployment probes.

Each key can instead be read from an absolute-path, single-line UTF-8 secret file by setting its `_FILE` variant. Do not set the direct and `_FILE` forms of the same key together. Missing, unreadable, multiline, or oversized secret files fail startup; file contents are not logged.

`HISTORYGUIDE_API_KEY_NEXT` is a temporary second accepted business key for a coordinated plugin rotation. Never leave the exposed old key active after the cutover; see `docs/business_key_rotation.md`.

Set `HISTORYGUIDE_OPERATOR_API_KEY` in shared or production-like environments to require `X-HistoryGuide-Operator-Key` on audit log, operational alert, and security status APIs. When both keys are configured, operator endpoints require the operator key and ordinary business APIs require `X-HistoryGuide-Api-Key`.

Validate runtime environment variables before staging or production-like deployment:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

The runtime config validator checks API key presence, operator key separation, CORS wildcard risk, database URL profile risk, schema-mode profile risk, log level, and log format without connecting to the database and without printing secret values. It is a deployment gate, not a historical-content validator and not a GeniOS prompt or RAG tool.

Validate the staging database after `alembic upgrade head` and after importing reviewed real exhibit data:

```powershell
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Use `--database-url <url>` only from trusted operator tooling when an explicit override is safer than environment variables. The script performs read-only database checks and avoids printing the full database URL or secret values.

Visitor State APIs:

```text
POST /api/visitor-states
GET /api/visitor-states
GET /api/visitor-states?visitor_type=tourist&limit=20&offset=0
GET /api/visitor-states/stats
GET /api/visitor-states/integrity-report
GET /api/visitor-states/{session_id}
GET /api/visitor-states/{session_id}/integrity
PATCH /api/visitor-states/{session_id}
GET /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/visit-events?limit=20&offset=0
POST /api/visitor-states/{session_id}/visit-events
```

Visitor types:

```text
freshman
alumnus
tourist
```

Visitor State tracks one real visit session with `session_id`, `visitor_type`, `current_exhibit`, `visited_history`, `interest`, and `remaining_time`. When `current_exhibit` or `visited_history` references an exhibit id, the backend validates that the exhibit exists. The list endpoint supports `visitor_type`, `limit`, and `offset` for session review and Web/H5 recovery flows. The stats endpoint aggregates stored session counts for demos, integration checks, and lightweight operations without inferring visitor profiles. The global integrity report checks whether Visitor State snapshots and visit-event timelines are aligned across stored sessions, while the per-session integrity endpoint checks one active visit session before a GeniOS handoff or frontend recovery step. The visit event endpoint records QR scan or exhibit-entry events by setting the current exhibit, appending to visited history without duplicates, optionally updating remaining time, and storing a timestamped event row. The timeline endpoint returns recorded visit events for the session as structured data and supports optional `limit` and `offset` pagination for longer real visits.

Audit log API:

```text
GET /api/audit-logs
GET /api/audit-logs/stats
GET /api/audit-logs?action=visit_event_recorded&limit=20&offset=0
GET /api/audit-logs?resource_type=visitor_state&resource_id=demo-session-001
```

The audit log endpoint returns structured operation records for Visitor State creation, Visitor State updates, visit-event recording, and exhibit seed imports. It supports exact-match filters for `action`, `resource_type`, `resource_id`, and `actor`, plus `limit` and `offset`. The stats endpoint summarizes total logs, actions, resource types, actors, and the latest audit timestamp for lightweight operational monitoring. Audit logs are for operator traceability and integration checks. They do not infer visitor profiles, perform RAG retrieval, or generate explanation content.

Recommendation API:

```text
GET /api/recommendations/{session_id}
GET /api/recommendations/{session_id}?limit=3
```

The MVP recommendation service is rule-based and explainable. It uses the visitor type, remaining time, interests, current exhibit context, and visited history to rank unvisited exhibits. The backend does not generate explanation content; it returns structured recommendation reasons for GeniOS or the frontend to use.

Visit route plan API:

```text
GET /api/visit-routes/{session_id}/plan
GET /api/visit-routes/{session_id}/plan?max_items=5
```

The route plan service is rule-based and uses unvisited recommendation candidates, remaining visit time, and simple exhibit duration estimates. It returns ordered structured route items. It does not perform indoor map navigation and does not generate explanation content.

GeniOS context API:

```text
GET /api/genios/capabilities
GET /api/genios/context/{session_id}
GET /api/genios/context/{session_id}?recommendation_limit=3
GET /api/genios/grounding/{session_id}
GET /api/genios/grounding/{session_id}?recommendation_limit=3
GET /api/genios/preflight/{session_id}
GET /api/genios/preflight/{session_id}?recommendation_limit=3
GET /api/genios/handoff/{session_id}
GET /api/genios/handoff/{session_id}?recommendation_limit=3&route_max_items=5
```

The capabilities endpoint returns the backend/GeniOS collaboration boundary, supported visitor types, integration workflow, and related structured endpoints. It is intended as a machine-readable starting point for GeniOS or Web/H5 integration.

The context package includes Visitor State, current exhibit, visited exhibits, visit-event timeline, recommendation candidates, grounding exhibit ids, missing exhibit references, and a collaboration contract. It is designed for GeniOS to use as structured input. The backend does not perform dialogue, RAG retrieval, or generated explanation content.

The grounding package resolves grounding exhibit ids to exhibit records and source references for GeniOS exhibit-level RAG preparation. It also reports sourced and unsourced grounding exhibit ids plus `grounding_sources_complete`, so GeniOS can avoid generated explanation when source references are incomplete. It does not retrieve knowledge-base passages or generate explanation content.

The preflight package checks one visit session before GeniOS handoff. It reports exhibit-reference readiness, grounding source-reference completeness, Visitor State integrity, visit-event availability, recommendation availability, missing exhibit ids, and whether the session is structurally ready for handoff. It does not generate explanation content.

The handoff package combines source safety, the preflight package, context package, route plan, and visit summary into one structured response for GeniOS integration. The `source_safety` summary exposes whether the session is ready for generated explanation without requiring GeniOS to parse every preflight check. It does not generate explanation content.

See `docs/api_contract.md` for a complete non-historical fixture handoff response example covering `source_safety`, `preflight`, `context`, `route_plan`, and `visit_summary`.

Visit summary API:

```text
GET /api/visits/{session_id}/summary
```

The summary is structured data for the frontend or GeniOS. It includes visited exhibits and visit-event timeline data, but does not generate a natural-language recap.

## Exhibit Data Import

### Curator workspace

Open `/operator` on the backend for a Chinese staff workspace with source/exhibit JSON
preview and draft import, source approval/revocation, exhibit-source linking,
exhibit approval/revocation, and audit records. All data APIs require a separate
operator key; the public page contains no museum records or keys.

On Windows, after creating `.venv` and installing `requirements-dev.lock` with
`--require-hashes`:

```powershell
.\scripts\start_local_workspace.ps1
```

The launcher prompts for a fresh local operator key, listens only on `127.0.0.1`,
and uses a separate `.local/workspace.db`. See `docs/operator_workspace.md` for the
workflow, upload limits, authentication boundary, and remaining release gates.

Seed format:

```text
docs/exhibit_seed_format.md
```

Real exhibit seed review checklist:

```text
docs/real_exhibit_seed_review.md
```

Real data pre-import final checklist:

```text
docs/real_data_preimport_final_checklist.md
```

Development fixture:

```text
data/example_exhibits.fixture.json
```

Import command:

```powershell
python scripts\import_exhibits.py data\example_exhibits.fixture.json
```

Dry-run validation before import:

```powershell
python scripts\import_exhibits.py --dry-run data\example_exhibits.fixture.json
```

Export current database records to a seed-style backup:

```powershell
python scripts\export_exhibits.py backups\exhibits.backup.json
python scripts\verify_exhibit_backup.py backups\exhibits.backup.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.backup.json
```

The fixture data is explicitly non-historical. Replace it with verified museum records before using the system for real Nankai history content. Review real seed files with `docs/real_exhibit_seed_review.md` and complete `docs/real_data_preimport_final_checklist.md` before import. Duplicate ids are rejected both within the seed file and against the current database. Imported records must include a non-empty `source_reference`. Use `--dry-run` to validate verified seed files before writing records. Use export, offline backup verification, and isolated restore rehearsal before resetting or migrating any database that contains verified museum records. Successful imports write a summary audit log for operator traceability.

## Integration Docs

API contract:

```text
docs/api_contract.md
```

Local demo workflow:

```text
docs/local_demo_workflow.md
```

Web/H5 and GeniOS integration sequence:

```text
docs/web_h5_genios_integration.md
```

GeniOS handoff evidence template:

```text
docs/genios_handoff_evidence_template.md
docs/examples/genios_handoff_evidence.example.md
```

Web/H5 integration acceptance checklist:

```text
docs/web_h5_integration_checklist.md
```

Real data import runbook:

```text
docs/real_data_import_runbook.md
docs/real_data_preimport_final_checklist.md
```

Backup and rollback drill:

```text
docs/backup_rollback_drill.md
```

Operator runbook:

```text
docs/operator_runbook.md
docs/examples/deployment_environment_validation.example.md
docs/examples/backend_readiness_validation.example.md
```

Incident response checklist:

```text
docs/incident_response_checklist.md
```

Production-like monitoring alert examples:

```text
docs/monitoring_alert_examples.md
docs/examples/operational_alerts_attention_required.example.json
```

Operator evidence package checklist:

```text
docs/operator_evidence_package_checklist.md
docs/examples/operator_evidence_package.example.md
docs/examples/backend_readiness_validation.example.md
```

Production readiness decision checklist:

```text
docs/production_readiness_decision_checklist.md
docs/examples/production_readiness_decision.example.md
docs/examples/backend_readiness_validation.example.md
```

Final operator pre-run checklist:

```text
docs/operator_final_prerun_checklist.md
```

Operator post-run review:

```text
docs/operator_post_run_review.md
```

## Test

```powershell
pytest
```

Operational readiness:

```text
docs/operational_readiness.md
```

MVP handoff:

```text
docs/mvp_handoff.md
```

Deployment notes:

```text
docs/deployment.md
```

Production hardening notes:

```text
docs/production_hardening.md
```

Centralized logging notes:

```text
docs/centralized_logging.md
```

Database migration notes:

```text
docs/database_migrations.md
```

Staging validation record template:

```text
docs/staging_validation_record.md
```

## Next Stage

Agent architecture and the local snapshot-bound review workflow are documented in
`docs/agent_architecture_2026.md`. These endpoints are not yet deployed or wired as
the NK-GeniOS final answer gate.
General historical Q&A has a separate local approved-source run API and plugin schema
at `/openapi-genios-history-runs.json`. Its review currently allows only literal
`claim_text` excerpts from approved `evidence_quote` values, each followed by the
matching source marker. This is not a semantic fact verifier or museum approval.
Exhibit/route review also requires literal claim excerpts; multi-exhibit answers may
include only the route-name prefix derived from the cited, backend-ordered exhibits.
The optional `/openapi-genios-answers.json` plugin provides server-side single-call
prepare/review/finalize orchestration for history and exhibit/route drafts. Its protected
API returns only a reviewed answer or safe block, but it is not a visitor browser gateway
and cannot force Coze to call it; a mandatory final-output workflow is still required.
An opt-in, session-token visitor gateway is documented in `docs/visitor_gateway.md`.
It keeps the business key off visitor JavaScript and scopes state, approved routes,
exhibit reads and reviewed answers to a short-lived token. It is not yet a Coze
model adapter or a production-ready public deployment.
Operator-only draft evidence batch intake, listing, and detail inspection are described in
`docs/evidence_intake.md`. The local staff UI is documented in `docs/operator_workspace.md`;
it has not been deployed or accepted by museum staff. The cleaned public-source package must not be auto-approved.

Next backend work should be chosen from integration needs:

- connect verified museum exhibit data
- integrate with GeniOS
- integrate with Web/H5
- validate Alembic migrations in staging before production PostgreSQL use
- run read-only staging database validation after staging migration and import
- harden production hosting details
- run incident response checklist during failed readiness, auth, source-safety, Visitor State, Web/H5, or GeniOS handoff events
- connect production-like monitoring alerts using operational alerts and structured request logs
- package operator evidence after demo, staging, Web/H5, GeniOS handoff, incident, or rollback-sensitive runs
- use `docs/examples/operator_evidence_package.example.md` only as placeholder formatting guidance for assembled evidence packages
- use production readiness decision checklist before production-like, museum-site rehearsal, or real visitor-facing backend runs
- use `docs/examples/production_readiness_decision.example.md` only as placeholder formatting guidance for go/no-go decisions
- complete `docs/operator_final_prerun_checklist.md` in the final minutes before production-like, museum-site rehearsal, or visitor-facing backend runs
- complete `docs/operator_post_run_review.md` after demo, staging, Web/H5, GeniOS handoff, production-like, museum-site rehearsal, or visitor-facing backend runs
- complete `docs/real_data_preimport_final_checklist.md` before importing verified museum exhibit records
- run read-only backend readiness validation before production-like handoff or visitor-facing backend runs
- use `docs/examples/backend_readiness_validation.example.md` only as placeholder formatting guidance for readiness evidence records
- improve route planning if verified venue topology becomes available
