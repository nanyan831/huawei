# Operational Readiness

This checklist keeps the NK HistoryGuide backend ready for local MVP demos and handoff to Web/H5 and GeniOS integration.

## Error Response Examples

Missing exhibit:

```http
GET /api/exhibits/missing-exhibit
```

```json
{
  "detail": "Exhibit 'missing-exhibit' was not found."
}
```

Duplicate Visitor State session:

```json
{
  "detail": "Visitor session 'demo-session-001' already exists."
}
```

Missing Visitor State session:

```json
{
  "detail": "Visitor session 'missing-session' was not found."
}
```

Visitor State references a missing exhibit:

```json
{
  "detail": "Referenced exhibit 'missing-exhibit' was not found."
}
```

Invalid query or request validation follows FastAPI's default `422` response shape. Keep this default unless the frontend or GeniOS integration needs a stricter error envelope.

Invalid or missing API key when `HISTORYGUIDE_API_KEY` is configured:

```json
{
  "detail": "Valid HistoryGuide API key is required."
}
```

Invalid or missing operator API key when `HISTORYGUIDE_OPERATOR_API_KEY` is configured:

```json
{
  "detail": "Valid HistoryGuide operator API key is required."
}
```

## Development Database Reset

The local SQLite database is:

```text
historyguide.db
```

It is ignored by Git. To reset local development data on PowerShell:

```powershell
Remove-Item .\historyguide.db -ErrorAction SilentlyContinue
python scripts\import_exhibits.py --dry-run data\example_exhibits.fixture.json
python scripts\import_exhibits.py data\example_exhibits.fixture.json
```

The database tables are recreated automatically when the FastAPI app starts or the import script runs.

Do not reset a database that contains verified museum records unless those records are safely backed up in a seed JSON file.

Back up current exhibit records before reset or migration:

```powershell
python scripts\export_exhibits.py backups\exhibits.backup.json
python scripts\verify_exhibit_backup.py backups\exhibits.backup.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.backup.json
```

## OpenAPI Review

Local OpenAPI document:

```text
http://127.0.0.1:8000/openapi.json
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

Required route groups:

- `health`
- `audit-logs`
- `exhibits`
- `visitor-states`
- `recommendations`
- `visit-routes`
- `genios`

Required paths:

- `GET /health`
- `GET /ready`
- `GET /api/system/database`
- `GET /api/system/operational-alerts`
- `GET /api/system/security-status`
- `GET /api/audit-logs`
- `GET /api/audit-logs/stats`
- `GET /api/exhibits`
- `GET /api/exhibits/facets`
- `GET /api/exhibits/quality-report`
- `GET /api/exhibits/source-report`
- `GET /api/exhibits/{exhibit_id}`
- `POST /api/visitor-states`
- `GET /api/visitor-states`
- `GET /api/visitor-states/stats`
- `GET /api/visitor-states/integrity-report`
- `GET /api/visitor-states/{session_id}`
- `GET /api/visitor-states/{session_id}/integrity`
- `PATCH /api/visitor-states/{session_id}`
- `GET /api/visitor-states/{session_id}/visit-events`
- `GET /api/visitor-states/{session_id}/visit-events?limit=20&offset=0`
- `POST /api/visitor-states/{session_id}/visit-events`
- `GET /api/recommendations/{session_id}`
- `GET /api/visit-routes/{session_id}/plan`
- `GET /api/genios/capabilities`
- `GET /api/genios/context/{session_id}`
- `GET /api/genios/grounding/{session_id}`
- `GET /api/genios/preflight/{session_id}`
- `GET /api/genios/handoff/{session_id}`
- `GET /api/visits/{session_id}/summary`

These paths are covered by `tests/test_openapi_contract.py`.

## Integration Documentation

Use `docs/web_h5_genios_integration.md` as the recommended Web/H5 and GeniOS call sequence for real visit integration. It covers session creation, QR scan or exhibit-entry events, GeniOS context, grounding, preflight, handoff, `source_safety.ready_for_generation`, and visit summary.

Use `docs/genios_handoff_evidence_template.md` to record each GeniOS handoff integration run. It captures request ids, Visitor State evidence, visit-event evidence, grounding completeness, preflight readiness, `source_safety.ready_for_generation`, GeniOS consumption notes, logging evidence, pass criteria, and stop conditions. Use `docs/examples/genios_handoff_evidence.example.md` only as placeholder formatting guidance, not as proof that staging or the museum environment has been validated.

Use `docs/web_h5_integration_checklist.md` as the Web/H5 acceptance checklist before browser integration or museum demo runs. It covers CORS, server-side API key handling, request id evidence, Visitor State session creation, exhibit scan events, source reports, GeniOS handoff gates, mandatory finalization, and stop conditions.

Use `docs/real_exhibit_seed_review.md` before importing real museum exhibit records. It covers source packages, manual review, dry-run, backup, import, post-import source and quality reports, and GeniOS grounding checks.

Use `docs/real_data_import_runbook.md` as the end-to-end real exhibit data import sequence. It ties together source review, runtime config validation, migration checks, backup and restore, dry-run, import, post-import backend checks, GeniOS source-safety checks, and request-id evidence.

Use `docs/real_data_preimport_final_checklist.md` immediately before importing verified museum exhibit records. It is the final backend gate for source packages, seed structure, runtime config, migrations, backup, restore rehearsal, dry-run, runtime evidence, import authorization, post-import checks, and GeniOS source-safety smoke.

Use `docs/backup_rollback_drill.md` before production-like data, migration, deployment, Web/H5, or GeniOS handoff changes. It covers pre-change runtime checks, exhibit export, backup verification, restore rehearsal, post-change validation, rollback decision criteria, and post-rollback source-safety checks.

Use `docs/operator_runbook.md` as the top-level operator sequence for local demos, verified data import, staging validation, Web/H5 checks, GeniOS handoff checks, incident triage, and evidence preservation. Use `docs/incident_response_checklist.md` for detailed readiness, auth, source-safety, Visitor State, Web/H5, GeniOS handoff, logging, and rollback triage. Use `docs/examples/deployment_environment_validation.example.md` only as placeholder formatting guidance, not as evidence that any real deployment has been validated.

Use `docs/database_migrations.md` before staging database work. It covers the Alembic scaffold, initial migration, migration commands, and PostgreSQL boundary.

Use `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs` after staging migrations and reviewed data import. It performs read-only checks for core tables, current Alembic head, exhibit source coverage, Visitor State count, visit-event count, and audit-log count without running migrations or writing data.

Use `python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts` before production-like handoff or visitor-facing backend runs. Add `--session-id <session-id> --require-visit-events` when validating a specific visit session and GeniOS handoff path. The script checks only read-only endpoints and does not write to the database, does not print key values, does not validate historical accuracy, does not run RAG, and does not generate explanation content. Use `docs/examples/backend_readiness_validation.example.md` only as placeholder formatting guidance for recording command output, request ids, source-safety fields, and stop conditions; it is not evidence that any real staging, production-like, or museum deployment has been validated.

Use `docs/staging_validation_record.md` to capture staging evidence for runtime config, migration, backup and restore, deployment self-check, source safety, GeniOS handoff, and centralized logging gates.

Use `docs/production_hardening.md` before shared, public, or production-like deployment. It covers migration gates, backups, rollback, API key checks, CORS checks, runtime monitoring, and the SQLite-to-PostgreSQL boundary.

Use `docs/monitoring_alert_examples.md` when wiring a production-like dashboard or alert policy. It maps `GET /api/system/operational-alerts`, structured request logs, source-safety fields, Visitor State integrity checks, Web/H5 scan events, and GeniOS handoff readiness into concrete monitoring rules. Use `docs/examples/operational_alerts_attention_required.example.json` only as placeholder formatting guidance.

Use `docs/operator_evidence_package_checklist.md` after demos, staging validation, verified data import, Web/H5 checks, GeniOS handoff runs, incidents, monitoring setup, or rollback-sensitive changes to package command outputs, request ids, source-safety fields, Visitor State integrity evidence, audit evidence, and final proceed/blocked/rollback decisions. Use `docs/examples/operator_evidence_package.example.md` only as placeholder formatting guidance for assembled evidence packages, not as evidence that any real staging, production-like, or museum deployment has been validated.

Use `docs/production_readiness_decision_checklist.md` before a production-like run, public demo, museum-site rehearsal, or real visitor-facing backend run. It turns runtime config, deployment self-check, database validation, data safety, visit flow, GeniOS handoff, monitoring, incident readiness, and evidence package results into a proceed, proceed_with_warnings, blocked, or rollback_required decision. Use `docs/examples/production_readiness_decision.example.md` only as placeholder formatting guidance for go/no-go decisions, not as evidence that any real staging, production-like, museum-site, or production deployment has been validated.

Use `docs/operator_final_prerun_checklist.md` in the final minutes before a production-like run, public demo, museum-site rehearsal, or real visitor-facing backend run. It ties together the staging validation record, backend readiness validation, operator evidence package, production readiness decision, monitoring checks, incident owner, rollback owner, and stop conditions.

Use `docs/operator_post_run_review.md` after a demo, staging validation, Web/H5 integration check, GeniOS handoff evidence run, production-like run, museum-site rehearsal, or real visitor-facing backend run. It records the actual backend outcome, request-id evidence, Visitor State integrity, GeniOS handoff source-safety, audit evidence, monitoring and incident results, rollback status, evidence package updates, and follow-up owners.

## MVP Readiness Checklist

Engineering:

- FastAPI app starts locally.
- SQLite database initializes automatically.
- Readiness check confirms database access.
- Database status reports backend and migration mode without exposing the full database URL.
- Operational alerts summarize demo, staging, and handoff readiness warnings and failures.
- Alembic migration scaffold exists for staging and future PostgreSQL work.
- Read-only staging database validation script exists for target database checks after migration and import.
- Read-only backend readiness validator exists for runtime, data, Visitor State, GeniOS handoff, source-safety, and audit gates.
- Audit logs are created for Visitor State changes, visit-event recording, and exhibit imports.
- Audit log endpoint supports operator review with filters and pagination.
- Audit log stats endpoint summarizes action, resource type, actor, and latest timestamp for monitoring checks.
- Optional API key protection works when `HISTORYGUIDE_API_KEY` is configured.
- Optional operator API key protection works when `HISTORYGUIDE_OPERATOR_API_KEY` is configured.
- Security status endpoint reports configured API-key controls without exposing secret values.
- Deployment self-check script can verify read-only runtime endpoints without writing to the database.
- Tests pass with `pytest`.
- Exhibit list pagination works.
- Visitor State listing works.
- Visitor State stats work.
- Visitor State integrity report works.
- Per-session Visitor State integrity report works.
- Exhibit quality report works.
- Exhibit source report works.
- GeniOS capability discovery works.
- GeniOS grounding works.
- GeniOS grounding reports source completeness.
- GeniOS preflight works.
- GeniOS handoff reports source safety.
- Web/H5 and GeniOS integration sequence documentation exists.
- GeniOS handoff evidence template exists.
- Web/H5 integration acceptance checklist exists.
- Backup and rollback drill exists.
- Operator runbook exists.
- Incident response checklist exists.
- Production-like monitoring alert examples exist.
- Operator evidence package checklist exists.
- Production readiness decision checklist exists.
- Final operator pre-run checklist exists.
- Operator post-run review exists.
- Real exhibit seed review checklist exists.
- Production hardening notes exist.
- Database migration notes exist.
- Exhibit seed dry-run validation works.
- Exhibit export backup works.
- Offline exhibit backup verification works.
- Isolated exhibit restore rehearsal works.
- Exhibit metadata facets work.
- Local fixture import works.
- Duplicate exhibit imports are rejected.
- Core OpenAPI paths are present.

Product boundary:

- Backend stores exhibit data and Visitor State.
- Backend reports database backend status for deployment and migration planning.
- Backend exposes operational alerts for empty data, unsourced exhibits, metadata gaps, Visitor State drift, and missing audit evidence.
- Backend can protect business APIs with `X-HistoryGuide-Api-Key`.
- Backend can protect audit and operational APIs with `X-HistoryGuide-Operator-Key`.
- Backend returns `X-HistoryGuide-Request-Id` on every response for Web/H5, GeniOS, and operator log correlation.
- Backend supports `HISTORYGUIDE_LOG_FORMAT=json` for centralized request logging with `request_id`, `http_method`, `path`, `status_code`, and `elapsed_ms`.
- Backend exposes security status for deployment and operator-key verification without returning key values.
- Backend exposes access policy for coarse public, business, operator, and local script boundaries without exposing key values.
- Backend exposes structured audit logs for operator traceability.
- Backend exposes audit log stats for lightweight operational monitoring.
- Backend supports paginated exhibit browsing.
- Backend exposes structured exhibit metadata facets.
- Backend exposes structured exhibit quality reports.
- Backend exposes structured exhibit source reports.
- Backend supports structured Visitor State listing.
- Backend exposes aggregate Visitor State stats.
- Backend exposes Visitor State and visit-event timeline integrity checks.
- Backend exposes per-session Visitor State and visit-event timeline integrity checks.
- Backend records exhibit visit events for real visit sessions.
- Backend stores and returns timestamped visit-event timelines with optional pagination.
- Backend records audit logs for Visitor State creation, Visitor State updates, and visit-event recording.
- Backend returns recommendation candidates and context packages.
- Backend includes visit-event timelines in GeniOS context packages.
- Backend includes grounding exhibit ids in GeniOS context and handoff packages.
- Backend exposes a structured GeniOS grounding package for exhibit-level RAG preparation.
- Backend reports sourced and unsourced grounding exhibit ids before generated explanation.
- Backend exposes a structured GeniOS capability discovery package.
- Backend exposes a structured GeniOS preflight package for session readiness and grounding source checks.
- Backend returns a structured GeniOS handoff package with source safety and preflight readiness.
- Backend returns structured route plans for real visit sessions.
- Backend returns structured visit summaries.
- Backend includes visit-event timelines in structured visit summaries.
- Backend can explicitly allow Web/H5 browser origins through CORS settings.
- Backend does not train models.
- Backend does not replace GeniOS.
- Backend does not implement digital humans, AR, VR, or unrelated chat features.

Historical content safety:

- No invented Nankai history is shipped in seed data.
- Development fixture data is clearly marked as non-historical.
- Real exhibit seed records must include non-empty `source_reference` values.
- Real exhibit seed files should be reviewed with `docs/real_exhibit_seed_review.md` before import.
- Real exhibit seed files should pass `docs/real_data_preimport_final_checklist.md` before import.
- Real exhibit data should be checked with the quality report after import.
- Real exhibit source grouping should be checked with the source report after import.
- GeniOS grounding packages should show `grounding_sources_complete=true` before generated explanation.
- GeniOS handoff packages should show `source_safety.ready_for_generation=true` before generated explanation.
- Real exhibit seed files should pass `python scripts\import_exhibits.py --dry-run <seed-file>` before import.
- Successful real exhibit imports should leave an `exhibits_imported` audit log.
- Databases containing verified museum records should be exported before reset or migration.
- Exported exhibit backups should pass `python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty` before restore rehearsal or migration.
- Backup verification checks structure and `source_reference` presence only; it does not prove historical accuracy and does not import records.
- Exported exhibit backups should pass `python scripts\rehearse_exhibit_restore.py <backup-file>` before restore, reset, or migration work.
- Restore rehearsal imports into an isolated in-memory SQLite database only; it does not modify the configured application database and does not prove historical accuracy.
- Production PostgreSQL use requires staging-validated Alembic migrations; a database URL change alone is not enough.
- Staging database validation should pass with `python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs` after staging migration, import, and test visit events.
- Production-like deployment should follow `docs/production_hardening.md`.
- GeniOS remains responsible for knowledge retrieval and generated explanation content.

Security:

- Leave `HISTORYGUIDE_API_KEY` empty only for local demos or trusted private networks.
- Set `HISTORYGUIDE_API_KEY` for shared, public, or production-like deployments.
- Pass `X-HistoryGuide-Api-Key` from GeniOS and the trusted visitor gateway when API key protection is enabled; never put the shared key in visitor code.
- Set `HISTORYGUIDE_OPERATOR_API_KEY` for shared or production-like deployments that expose audit logs or operational alerts.
- Pass `X-HistoryGuide-Operator-Key` only from trusted operator tooling.
- Keep `HISTORYGUIDE_OPERATOR_API_KEY` separate from `HISTORYGUIDE_API_KEY`.
- Run `python scripts\validate_runtime_config.py --profile staging` or `python scripts\validate_runtime_config.py --profile production` before shared deployment; it checks API key presence, operator key separation, CORS wildcard risk, database URL profile risk, log level, and log format without printing secret values.
- Use `GET /api/system/access-policy` to verify coarse access boundaries without exposing key values; do not treat it as user accounts or full RBAC.
- Pass `X-HistoryGuide-Request-Id` from Web/H5 or GeniOS when available to correlate logs; do not treat it as authentication or visitor identity.
- Use structured JSON request logs for operational correlation only; do not treat log fields as historical evidence, visitor profile data, or GeniOS prompt input.
- Use `GET /api/system/security-status` to verify key controls after deployment; do not treat it as full RBAC.
- Use `python scripts\deployment_self_check.py --base-url <backend-url>` for read-only deployment checks; preserve returned `X-HistoryGuide-Request-Id` values for log correlation, and pass API keys only through trusted operator tooling.
- Use `python scripts\validate_backend_readiness.py --base-url <backend-url>` for stronger read-only readiness validation before production-like handoff or visitor-facing backend runs.
- Keep health, readiness, database status, and OpenAPI docs reachable for deployment probes.

Demo flow:

- Import fixture exhibits.
- Start backend.
- Request database status.
- Request operational alerts before GeniOS handoff or demo runs.
- Request audit logs after state-changing demo steps.
- Request audit log stats after state-changing demo steps.
- Request exhibit source report.
- Create Visitor State.
- List Visitor States.
- Request Visitor State stats.
- Request Visitor State integrity report.
- Record a visit event.
- Request visit event timeline.
- Request paginated visit event timeline.
- Request per-session Visitor State integrity report.
- Request recommendations.
- Request a structured route plan.
- Request GeniOS capabilities.
- Request GeniOS context package.
- Request GeniOS grounding package.
- Request GeniOS preflight package.
- Request GeniOS handoff package.
- Request structured visit summary.
- Review `docs/web_h5_genios_integration.md` before connecting Web/H5 or GeniOS clients.
- Complete `docs/genios_handoff_evidence_template.md` for each GeniOS handoff integration run.
- Review `docs/web_h5_integration_checklist.md` before browser-based Web/H5 integration or museum demo runs.
- Review `docs/real_data_import_runbook.md` before importing verified museum records.
- Complete `docs/real_data_preimport_final_checklist.md` before importing verified museum records.
- Review `docs/backup_rollback_drill.md` before production-like changes or rollback-sensitive demos.
- Review `docs/operator_runbook.md` before running operator workflows or incident triage.
- Review `docs/incident_response_checklist.md` during failed readiness, auth, source-safety, Visitor State, Web/H5, GeniOS handoff, logging, or rollback-triggering incidents.
- Review `docs/monitoring_alert_examples.md` before connecting production-like dashboard or alert policies.
- Complete `docs/operator_evidence_package_checklist.md` after operator runs that need handoff, replay, auditability, or incident follow-up.
- Complete `docs/production_readiness_decision_checklist.md` before production-like, museum-site rehearsal, or real visitor-facing backend runs.
- Review `docs/database_migrations.md` before staging migration work.
- Run `python scripts\validate_staging_database.py` against staging after migrations and reviewed data import.
- Run `python scripts\validate_backend_readiness.py` against the running backend before production-like handoff or visitor-facing backend runs.
- Complete `docs/staging_validation_record.md` before production-like deployment.
- Review `docs/centralized_logging.md` before connecting a centralized logging platform.
- Review `docs/production_hardening.md` before shared, public, or production-like deployment.

Web/H5 integration:

- Configure `HISTORYGUIDE_CORS_ORIGINS` with explicit frontend origins.
- Keep CORS empty when no browser client needs direct backend access.
- Send `X-HistoryGuide-Api-Key` from the trusted visitor gateway when API key protection is enabled; do not expose it to Web/H5 JavaScript.
- Preserve returned `X-HistoryGuide-Request-Id` values in Web/H5 logs for backend correlation.
- Use `POST /api/visitor-states/{session_id}/visit-events` for QR scans or exhibit-entry events.
- Check `source_safety.ready_for_generation=true` and `grounding_sources_complete=true` before drafting; display only the applicable review-run `finalize.answer` after successful finalization.
- Stop integration when exhibit ids are missing, source references are empty, or GeniOS handoff source-safety checks fail.
