# MVP Handoff

This document summarizes the current NK HistoryGuide backend MVP state.

## Project Boundary

NK HistoryGuide is a context-aware museum visit backend. It is not a general Nankai history chatbot.

The backend provides:

- exhibit data storage and query
- Visitor State storage and update
- event-style exhibit visit recording
- rule-based recommendation candidates
- structured visit route plans
- GeniOS capability discovery
- GeniOS context packages
- GeniOS handoff packages
- structured visit summaries
- verified exhibit data import workflow
- integration and operational documentation

The backend does not provide:

- large model training
- GeniOS replacement
- generated explanation text
- digital humans
- AR or VR
- unrelated chat features

## Implemented Backend Capabilities

Application foundation:

- FastAPI app factory
- explicit CORS configuration for Web/H5 integration
- health check
- database readiness check
- database status endpoint for backend and migration-mode visibility
- operational alerts endpoint for deployment and demo checks
- Alembic migration scaffold for staging and future PostgreSQL work
- structured audit log table and API
- audit log stats endpoint for lightweight operational monitoring
- optional API key protection for business APIs
- optional operator API key protection for audit and operational APIs
- security status endpoint for deployment and operator-key verification
- request id response header and request completion logging
- read-only deployment self-check script
- read-only backend readiness validator
- offline exhibit backup verification script
- isolated exhibit restore rehearsal script
- read-only staging database validation script
- logging setup
- SQLite database initialization
- test suite

Exhibit management:

- `Exhibit` database model
- exhibit list and detail APIs
- exhibit list pagination
- exhibit metadata facets API
- exhibit quality report API
- exhibit source report API
- keyword, period, and importance filters
- JSON seed format
- import CLI
- import dry-run validation
- import summary audit log
- export CLI for seed-style backups
- offline backup verification CLI
- isolated restore rehearsal CLI
- duplicate id protection
- required source references for imported records

Visitor State:

- visit-session model
- visitor types: `freshman`, `alumnus`, `tourist`
- visitor session listing with type filter and pagination
- audit logs for Visitor State create and update operations
- visitor session aggregate stats
- visitor session integrity report
- per-session visitor session integrity report
- current exhibit tracking
- visited history
- visit event endpoint for scan or exhibit-entry updates
- audit logs for visit-event recording
- timestamped visit-event timeline with optional pagination
- interest tracking
- remaining time
- exhibit reference validation

Recommendation:

- rule-based recommendation service
- excludes current and visited exhibits
- uses visitor type, interests, remaining time, and exhibit metadata
- returns structured recommendation reasons

Visit route planning:

- rule-based route plan service
- ordered route items derived from unvisited recommendation candidates
- simple duration estimates based on exhibit importance
- total planned minutes fitted within remaining visit time
- explicit boundary against indoor map navigation and generated explanation text

GeniOS collaboration:

- structured capability discovery package
- structured context package with visit-event timeline
- structured grounding package with exhibit records, source references, and source completeness status
- structured preflight package for handoff readiness and grounding source checks
- structured handoff package combining source safety, preflight, context, route plan, and visit summary
- Visitor State
- current exhibit
- visited exhibits
- recommendation candidates
- missing exhibit references
- explicit backend/GeniOS role boundary

Visit summary:

- structured session summary
- visited exhibit list
- visit-event timeline
- interest and remaining-time summary
- missing visited exhibit references
- GeniOS next-step hint for grounded recap generation

Documentation:

- API contract
- complete non-historical GeniOS handoff response example
- local demo workflow
- Web/H5 and GeniOS integration sequence
- GeniOS handoff evidence template
- placeholder-only GeniOS handoff evidence example
- Web/H5 integration acceptance checklist
- backup and rollback drill
- operator runbook: `docs/operator_runbook.md`
- incident response checklist: `docs/incident_response_checklist.md`
- production-like monitoring alert examples: `docs/monitoring_alert_examples.md`
- operator evidence package checklist: `docs/operator_evidence_package_checklist.md`
- placeholder-only operator evidence package example: `docs/examples/operator_evidence_package.example.md`
- production readiness decision checklist: `docs/production_readiness_decision_checklist.md`
- placeholder-only production readiness decision example: `docs/examples/production_readiness_decision.example.md`
- final operator pre-run checklist: `docs/operator_final_prerun_checklist.md`
- operator post-run review template: `docs/operator_post_run_review.md`
- real data pre-import final checklist: `docs/real_data_preimport_final_checklist.md`
- placeholder-only deployment environment validation example
- placeholder-only backend readiness validation evidence example: `docs/examples/backend_readiness_validation.example.md`
- exhibit seed format
- real exhibit seed review checklist
- operational readiness checklist
- production hardening notes
- database migration notes

## Verification Result

Latest test result:

```text
159 passed, 2 warnings
```

Warnings:

- FastAPI/Starlette TestClient upstream deprecation warnings
- no current runtime impact

Local demo flow verified:

- reset local SQLite database
- imported 2 non-historical fixture exhibits
- started FastAPI app
- verified `GET /health`
- verified `GET /ready`
- verified `GET /api/system/database`
- verified `GET /api/system/operational-alerts`
- verified `GET /api/system/security-status`
- verified `GET /api/system/access-policy`
- verified `GET /api/audit-logs`
- verified `GET /api/audit-logs/stats`
- verified optional API key protection for business APIs
- verified optional operator API key protection for audit and operational APIs
- verified runtime configuration validation script behavior
- verified `X-HistoryGuide-Request-Id` response header for successful and unauthorized responses
- verified optional structured JSON request logging fields
- verified centralized logging example payload
- verified read-only deployment self-check behavior with returned request id correlation
- verified offline exhibit backup verification behavior
- verified isolated exhibit restore rehearsal behavior
- verified isolated Alembic migration rehearsal behavior
- verified read-only staging database validation behavior
- verified staging validation record template coverage
- verified real data import runbook coverage
- verified GeniOS handoff evidence template coverage
- verified placeholder-only GeniOS handoff evidence example coverage
- verified backup and rollback drill coverage
- verified operator runbook coverage
- verified incident response checklist coverage
- verified production-like monitoring alert examples coverage
- verified operator evidence package checklist coverage
- verified placeholder-only operator evidence package example coverage
- verified placeholder-only production readiness decision example coverage
- verified final operator pre-run checklist coverage
- verified operator post-run review coverage
- verified placeholder-only backend readiness validation evidence example coverage
- verified production readiness decision checklist coverage
- verified read-only backend readiness validator coverage
- verified placeholder-only deployment environment validation example coverage
- verified Web/H5 integration checklist coverage
- verified `GET /api/exhibits`
- verified `GET /api/exhibits?limit=1&offset=1`
- verified `GET /api/exhibits/facets`
- verified `GET /api/exhibits/quality-report`
- verified `GET /api/exhibits/source-report`
- created Visitor State
- verified `GET /api/visitor-states?visitor_type=tourist&limit=1&offset=1`
- verified `GET /api/visitor-states/stats`
- verified `GET /api/visitor-states/integrity-report`
- verified `GET /api/visitor-states/{session_id}/integrity`
- verified `POST /api/visitor-states/{session_id}/visit-events`
- verified `GET /api/visitor-states/{session_id}/visit-events`
- verified `GET /api/visitor-states/{session_id}/visit-events?limit=1&offset=1`
- verified `GET /api/recommendations/{session_id}`
- verified `GET /api/visit-routes/{session_id}/plan`
- verified `GET /api/genios/capabilities`
- verified `GET /api/genios/context/{session_id}`
- verified `GET /api/genios/grounding/{session_id}`
- verified `GET /api/genios/preflight/{session_id}`
- verified `GET /api/genios/handoff/{session_id}`
- verified `GET /api/visits/{session_id}/summary`
- verified OpenAPI core paths

## Demo Evidence

Fixture import:

```text
Imported 2 exhibit records.
```

Dry-run validation:

```text
Validated 1 exhibit records. No records were imported.
```

Exhibit export:

```text
Exported 2 exhibit records to <temp export path>.
```

Exhibit backup verification:

```text
Verified <n> exhibit records in backup file. No database changes were made.
```

Use `python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty` before restore rehearsal, reset, migration, or environment move that involves verified exhibit records. The verifier checks structure, duplicate ids, field validation, and `source_reference` presence. It does not prove historical accuracy and does not import records.

Exhibit restore rehearsal:

```text
Restore rehearsal passed: imported=<n>, sourced=<n>, unsourced=0, quality_issue_count=<n>. No configured database changes were made.
```

Use `python scripts\rehearse_exhibit_restore.py <backup-file>` before restore, reset, migration, or environment move that involves verified exhibit records. The rehearsal imports the backup into an isolated in-memory SQLite database, checks restored source and quality reports, and then destroys the temporary database. It does not modify the configured application database and does not prove historical accuracy.

Exhibit facets response includes:

- `total`
- `periods`
- `keywords`
- `people`
- `themes`

Exhibit pagination smoke verified `GET /api/exhibits?limit=1&offset=1` returning the second fixture exhibit.

Exhibit quality report includes:

- `source_reference_coverage_percent`
- `importance_distribution`
- `missing_source_reference`
- `empty_keywords`
- `empty_themes`
- `empty_people`

Exhibit source report includes:

- `sourced_count`
- `unsourced_count`
- `unsourced_exhibit_ids`
- grouped `source_references`
- per-source `exhibit_ids`

GeniOS capabilities package includes:

- `service_id`
- `version`
- `collaboration_contract`
- `supported_visitor_types`
- `primary_workflow`
- `endpoints`
- `integration_notes`

Readiness response:

```json
{
  "status": "ready",
  "service": "nk-historyguide-backend",
  "version": "0.1.0",
  "database": "ok"
}
```

Database status response includes:

- `backend`
- `driver`
- `persistence`
- `schema_management`
- `migration_target`
- `production_note`

Operational alerts response includes:

- `status`
- `total_alerts`
- `fail_count`
- `warn_count`
- alert `name`
- alert `severity`
- alert `resource_type`
- alert `count`
- alert `detail`

Optional API key protection:

- disabled by default for local demos
- enabled with `HISTORYGUIDE_API_KEY`
- business APIs require `X-HistoryGuide-Api-Key`
- operator endpoint protection enabled with `HISTORYGUIDE_OPERATOR_API_KEY`
- audit and operational APIs require `X-HistoryGuide-Operator-Key` when configured
- security status reports configured controls without exposing key values
- access policy reports coarse public, business, operator, and local script boundaries without exposing key values
- access policy is not full RBAC or a user account system
- health, readiness, database status, and OpenAPI docs remain public

Runtime config validation:

- `python scripts\validate_runtime_config.py --profile staging`
- `python scripts\validate_runtime_config.py --profile production`
- checks API key presence, operator key separation, CORS wildcard risk, database URL profile risk, log level, and log format
- does not connect to the database
- runs without printing secret values
- does not validate historical content, call GeniOS, run RAG, or generate explanation content

Request id tracing:

- every response includes `X-HistoryGuide-Request-Id`
- Web/H5 and GeniOS may send `X-HistoryGuide-Request-Id` to correlate client and backend logs
- invalid incoming request ids are replaced by generated ids
- request id is troubleshooting metadata only, not authentication, visitor identity, or historical evidence

Structured request logging:

- optional `HISTORYGUIDE_LOG_FORMAT=json` for centralized logging platforms
- JSON request logs include `event`, `service_id`, `request_id`, `http_method`, `path`, `status_code`, and `elapsed_ms`
- field reference and example payload live in `docs/centralized_logging.md` and `docs/examples/structured_request_log.json`
- structured request logs are operational correlation metadata only
- structured request logs are not historical evidence, visitor profile data, or GeniOS prompt input

Isolated Alembic migration rehearsal:

- `python scripts\rehearse_migrations.py`
- runs `alembic upgrade head` against an isolated temporary SQLite database
- verifies the current Alembic revision and core tables
- removes the temporary database by default
- does not modify the configured application database
- does not import records, prove historical accuracy, or make PostgreSQL production-ready

Read-only staging database validation:

- `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`
- connects to the configured target database or a trusted `--database-url` override
- checks connectivity, core tables, current Alembic head, exhibit count, empty `source_reference` values, Visitor State count, visit-event count, and audit-log count
- does not run migrations, import records, write audit logs, validate historical accuracy, run RAG, or generate explanation content

Read-only deployment self-check:

- `python scripts\deployment_self_check.py --base-url <backend-url>`
- checks `GET /health`, `GET /ready`, `GET /api/system/database`, `GET /openapi.json`, `GET /api/system/access-policy`, `GET /api/system/security-status`, and `GET /api/system/operational-alerts`
- accepts business and operator keys by arguments or environment variables
- does not write to the database
- prints returned `X-HistoryGuide-Request-Id` values for log correlation
- does not print key values

Read-only backend readiness validation:

- `python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts`
- `python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --session-id <session-id> --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts`
- supports `--session-id <session-id>` for Visitor State and GeniOS handoff checks
- checks runtime, data, Visitor State, GeniOS handoff, source-safety, and audit gates
- covers readiness, database status, operational alerts, exhibit source and quality reports, audit log stats, Visitor State integrity, visit events, recommendations, route plan, visit summary, GeniOS grounding, GeniOS preflight, GeniOS handoff, source-safety, and `X-HistoryGuide-Request-Id` evidence
- prints returned `X-HistoryGuide-Request-Id` values for evidence correlation
- can be recorded with `docs/examples/backend_readiness_validation.example.md` as placeholder formatting guidance only
- does not write to the database
- does not print key values
- does not validate historical accuracy
- does not run RAG
- does not generate explanation content

Audit log response includes:

- `action`
- `resource_type`
- `resource_id`
- `actor`
- `details`
- `created_at`

Audit log stats include:

- `total_logs`
- `actions`
- `resource_types`
- `actors`
- `latest_created_at`

Current audited operations:

- `visitor_state_created`
- `visitor_state_updated`
- `visit_event_recorded`
- `exhibits_imported`

Recommendation response shape:

```json
[
  {
    "exhibit_id": "fixture-exhibit-002",
    "name": "Fixture Exhibit Two",
    "reason": "importance level 4; matches interests: recommendation; continues the current exhibit context; not yet visited",
    "priority": 1
  }
]
```

GeniOS context package includes:

- `session_id`
- `visitor_state`
- `current_exhibit`
- `visited_exhibits`
- `visit_events`
- `recommendations`
- `grounding_exhibit_ids`
- `missing_exhibit_ids`
- `collaboration_contract`

GeniOS grounding package includes:

- `grounding_exhibit_ids`
- `exhibits`
- `source_references`
- `source_reference_count`
- `sourced_exhibit_ids`
- `unsourced_exhibit_ids`
- `grounding_sources_complete`
- `missing_exhibit_ids`
- `collaboration_contract`

GeniOS preflight package includes:

- `ready_for_handoff`
- `checks`
- `missing_exhibit_ids`
- `integrity_report`
- `visit_event_count`
- `recommendation_count`
- `collaboration_contract`

Preflight checks include grounding source-reference completeness, so sessions with grounding exhibit records that lack `source_reference` are not marked ready for handoff.

GeniOS handoff package includes:

- `source_safety`
- `preflight`
- `context`
- `route_plan`
- `visit_summary`
- `handoff_note`

`source_safety` includes:

- `ready_for_generation`
- `grounding_sources_complete`
- `source_reference_count`
- `sourced_exhibit_ids`
- `unsourced_exhibit_ids`
- `missing_exhibit_ids`
- `blocking_check_names`
- `safety_note`

Runtime smoke verified handoff responses with matching context session, source-safety summary, route item, visited exhibit summary, and a populated handoff note.

Route plan includes:

- `remaining_time`
- `planned_minutes`
- ordered `items`
- per-item `estimated_minutes`
- per-item structured `reason`

Visit event response shape:

```json
{
  "visitor_type": "tourist",
  "current_exhibit": "fixture-exhibit-002",
  "visited_history": ["fixture-exhibit-001", "fixture-exhibit-002"],
  "interest": ["recommendation"],
  "remaining_time": 18,
  "session_id": "event-smoke-20260922142600"
}
```

Visit event timeline includes:

- `id`
- `session_id`
- `exhibit_id`
- `remaining_time`
- `event_time`

Visit event timeline supports:

- `limit`
- `offset`

Visitor State listing supports:

- `visitor_type`
- `limit`
- `offset`

Visitor State stats include:

- `total_sessions`
- `visitor_types`
- `current_exhibits`
- `interests`
- `no_current_exhibit_count`
- `remaining_time`

Visitor State integrity report includes:

- `total_sessions`
- `total_visit_events`
- `sessions_with_visit_events`
- `issue_count`
- `issues`

The same integrity response shape is available for one active visit session through `GET /api/visitor-states/{session_id}/integrity`.

Visit summary includes:

- `visited_count`
- `visited_exhibits`
- `visit_events`
- `interests`
- `remaining_time`
- `missing_exhibit_ids`
- `genios_next_step`

## Remaining Non-Backend Work

GeniOS:

- create the dialogue Agent
- configure prompt and role
- connect the校史 knowledge base
- perform RAG retrieval
- generate grounded personalized explanations
- consume `/api/genios/context/{session_id}` as structured context
- follow `docs/web_h5_genios_integration.md` for context, grounding, preflight, handoff, and source-safety checks
- complete `docs/genios_handoff_evidence_template.md` for each handoff integration run

Real museum data:

- replace development fixtures with verified exhibit records
- include `source_reference` for each exhibit
- follow `docs/real_data_import_runbook.md` for the import sequence
- review real seed files with `docs/real_exhibit_seed_review.md` before import
- complete `docs/real_data_preimport_final_checklist.md` before import
- curate metadata for people, time range, themes, and keywords
- validate historical content and run import dry-run before import
- export verified exhibit records before database reset or migration
- verify exported exhibit backups before restore rehearsal or migration
- rehearse exported exhibit restore before reset, restore, or migration
- follow `docs/backup_rollback_drill.md` before production-like changes or rollback-sensitive demos
- use `docs/incident_response_checklist.md` for failed readiness, auth, source-safety, Visitor State, Web/H5, GeniOS handoff, logging, or rollback-triggering incidents
- review audit logs after real seed import and live visit state-changing operations
- validate Alembic migrations in staging before production PostgreSQL use
- run read-only staging database validation after staging migration, reviewed import, and test visit-event operations
- complete `docs/staging_validation_record.md` before production-like deployment
- preserve GeniOS handoff evidence with `docs/genios_handoff_evidence_template.md`
- configure `HISTORYGUIDE_API_KEY` for shared or public deployments
- configure `HISTORYGUIDE_OPERATOR_API_KEY` for audit and operational endpoints in shared or production-like deployments
- review `docs/centralized_logging.md` before connecting centralized logs
- review `docs/monitoring_alert_examples.md` before connecting production-like dashboard or alert policies
- complete `docs/operator_evidence_package_checklist.md` after runs that need handoff, replay, auditability, or incident follow-up
- complete `docs/production_readiness_decision_checklist.md` before production-like, museum-site rehearsal, or real visitor-facing backend runs
- run `python scripts\validate_backend_readiness.py` before production-like handoff or visitor-facing backend runs
- review `docs/production_hardening.md` before production-like deployment

Frontend or Web/H5:

- scan or choose exhibit
- create and update Visitor State
- record exhibit-entry events through the visit event API
- use `source_safety.ready_for_generation` before displaying GeniOS generated explanation
- follow `docs/web_h5_integration_checklist.md` for CORS, API key headers, request id evidence, visit-event recording, GeniOS handoff gates, and stop conditions
- display exhibit metadata
- display recommendations
- pass GeniOS generated explanation to the user

Future backend enhancements:

- route planning with verified venue topology, if available
- richer source tracking
- staging-validated PostgreSQL migration using the Alembic scaffold
- production-like database validation evidence from a real staging environment
- stronger role-based authentication if needed for deployment
- managed backup, restore, monitoring, and rollback operations for production-like deployment

## Handoff Status

The backend MVP is ready for:

- local demos
- GeniOS context integration
- frontend API integration
- verified exhibit data import

It is not yet a full production system because real museum data, GeniOS RAG setup, deployment hardening, and any frontend experience are outside this backend MVP.
