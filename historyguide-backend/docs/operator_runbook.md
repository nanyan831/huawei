# Operator Runbook

Use this runbook when operating the NK HistoryGuide backend for local demos, staging validation, verified data import, Web/H5 integration, or GeniOS handoff checks.

This runbook coordinates existing backend tools and documents. It does not train models, does not replace GeniOS, does not run RAG, does not generate explanation content, and does not implement digital human or AR/VR features.

## 1. Choose The Run Type

Before running commands, identify the run type:

- local fixture demo
- verified exhibit data dry-run
- verified exhibit data import
- staging migration validation
- Web/H5 integration check
- GeniOS handoff evidence run
- backup and rollback drill
- incident triage after failed readiness, source-safety, or auth checks

Record:

- operator:
- date:
- environment:
- backend base URL:
- database URL label, not secret:
- Web/H5 origin:
- GeniOS environment:
- expected session id:
- expected exhibit ids:

## 2. Environment Gate

Run the runtime config validator before shared, staging, or production-like work:

```powershell
python scripts\validate_runtime_config.py --profile staging
```

Use `--profile production` only when checking production-like configuration.

Expected:

- no failed API key checks for shared environments
- `HISTORYGUIDE_OPERATOR_API_KEY` is separate from `HISTORYGUIDE_API_KEY`
- `HISTORYGUIDE_CORS_ORIGINS` uses explicit origins
- `HISTORYGUIDE_LOG_FORMAT=json` for centralized logs in staging or production-like environments
- secret values are not printed

Stop when the validator reports failed checks for the target environment.

## 3. Read-Only Runtime Gate

Against a running backend, run:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Record:

- `GET /health` result
- `GET /ready` result
- `GET /api/system/database` result
- `GET /api/system/access-policy` result
- `GET /api/system/security-status` result
- `GET /api/system/operational-alerts` result
- returned `X-HistoryGuide-Request-Id` values

Stop when readiness fails, access policy is not aligned with the environment, or operator endpoints do not require the intended operator key.

## 4. Data Safety Gate

Before changing verified exhibit data, follow:

```text
docs/real_exhibit_seed_review.md
docs/real_data_import_runbook.md
docs/real_data_preimport_final_checklist.md
docs/backup_rollback_drill.md
```

Minimum commands:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.json
python scripts\import_exhibits.py --dry-run <verified-seed-file>
```

Stop when:

- backup verification fails
- restore rehearsal fails
- import dry-run fails
- duplicate ids are unexpected
- any real exhibit record lacks `source_reference`

Do not create, infer, rewrite, or generate historical facts to make a seed file pass.

## 5. Migration Or Staging Database Gate

For staging database work, run:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Record:

- isolated migration rehearsal result
- staging migration result
- current Alembic head
- core table status
- exhibit count
- unsourced exhibit count
- audit-log count

Stop when the database is not at the expected Alembic head, core tables are missing, or verified real exhibit records are unsourced.

## 6. Local Fixture Demo Flow

For a local fixture demo only:

```powershell
python scripts\import_exhibits.py --dry-run data\example_exhibits.fixture.json
python scripts\import_exhibits.py data\example_exhibits.fixture.json
```

Then call the core flow:

```http
GET /ready
GET /api/exhibits
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/recommendations/{session_id}
GET /api/visit-routes/{session_id}/plan
GET /api/genios/handoff/{session_id}
GET /api/visits/{session_id}/summary
```

Remember that fixture data is non-historical and must not be presented as verified Nankai history.

## 7. Web/H5 Integration Gate

Before browser-based integration, follow:

```text
docs/web_h5_integration_checklist.md
```

Confirm:

- `HISTORYGUIDE_CORS_ORIGINS` includes the intended browser origin
- the trusted visitor gateway holds and sends `X-HistoryGuide-Api-Key` when enabled; the browser never holds it
- `X-HistoryGuide-Request-Id` is preserved by Web/H5 logs
- one physical visit uses one stable `session_id`
- QR scans or exhibit-entry events call `POST /api/visitor-states/{session_id}/visit-events`
- source-safety checks pass before drafting, and only the review-run `finalize.answer` is shown

## 8. GeniOS Handoff Gate

Before generated explanation, follow:

```text
docs/web_h5_genios_integration.md
docs/genios_handoff_evidence_template.md
```

Check:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Generation may proceed only when:

```text
grounding_sources_complete=true
source_safety.ready_for_generation=true
```

Stop when:

- `missing_exhibit_ids` is not empty
- `unsourced_exhibit_ids` is not empty
- `grounding_sources_complete=false`
- `source_safety.ready_for_generation=false`
- Visitor State integrity fails
- request ids cannot be correlated across Web/H5, GeniOS, backend logs, and operator notes

## 9. Incident Triage

For readiness failures:

- check `GET /ready`
- check `GET /api/system/database`
- inspect startup logs
- verify `HISTORYGUIDE_DATABASE_URL` label, not secret value

For repeated `401` responses:

- check `GET /api/system/access-policy`
- check `GET /api/system/security-status`
- verify client sends `X-HistoryGuide-Api-Key`
- verify operator tooling sends `X-HistoryGuide-Operator-Key`

For source-safety failures:

- check `GET /api/exhibits/source-report`
- check `GET /api/exhibits/quality-report`
- check `GET /api/genios/grounding/{session_id}`
- check `GET /api/genios/preflight/{session_id}`
- fix exhibit data or Visitor State references before generated explanation

For Visitor State drift:

- check `GET /api/visitor-states/{session_id}/integrity`
- check `GET /api/visitor-states/{session_id}/visit-events`
- record future physical movement through visit events rather than manually patching `visited_history`

## 10. Evidence To Preserve

For every operator run, preserve:

- command outputs
- returned `X-HistoryGuide-Request-Id` values
- deployment self-check output
- staging database validation output
- source report and quality report summaries
- GeniOS handoff evidence record
- backup file path and verification result
- rollback decision, if any

Do not preserve secret values, private prompts, unreviewed generated historical text, or database credentials in operator records.

Use `docs/operator_evidence_package_checklist.md` to assemble the final evidence package after demos, staging validation, verified data import, Web/H5 checks, GeniOS handoff runs, incidents, monitoring setup, or rollback-sensitive changes.

Use `docs/production_readiness_decision_checklist.md` before production-like, public demo, museum-site rehearsal, or real visitor-facing backend runs to turn the collected evidence into a `proceed`, `proceed_with_warnings`, `blocked`, or `rollback_required` decision.

Use `docs/operator_final_prerun_checklist.md` in the final minutes before starting the run to verify the evidence chain, request-id correlation, source-safety gates, monitoring readiness, incident owner, rollback owner, and final go/no-go decision.

Use `docs/operator_post_run_review.md` after the run to record actual backend outcome, request-id evidence, Visitor State and GeniOS handoff source-safety status, audit evidence, monitoring and incident results, rollback status, evidence package updates, and follow-up owners.

Stop verified exhibit import when `docs/real_data_preimport_final_checklist.md` has not passed.

For placeholder formatting guidance, see:

```text
docs/examples/deployment_environment_validation.example.md
docs/examples/backend_readiness_validation.example.md
docs/examples/operator_evidence_package.example.md
```

The examples are not evidence that any real staging, production-like, or museum deployment has been validated.

For detailed incident response, use:

```text
docs/incident_response_checklist.md
```

It covers the first five minutes of evidence capture, readiness/database failures, repeated auth failures, source-safety blocks, Visitor State drift, Web/H5 scan failures, GeniOS handoff failures, logging correlation gaps, and rollback triggers.

For production-like monitoring setup, use:

```text
docs/monitoring_alert_examples.md
docs/examples/operational_alerts_attention_required.example.json
```

The examples map `GET /api/system/operational-alerts`, structured request logs, source-safety fields, Visitor State integrity, Web/H5 scan events, and GeniOS handoff checks into alert rules without adding generated content or model behavior.

## Related Documents

- `docs/operational_readiness.md`
- `docs/real_data_import_runbook.md`
- `docs/real_data_preimport_final_checklist.md`
- `docs/backup_rollback_drill.md`
- `docs/incident_response_checklist.md`
- `docs/monitoring_alert_examples.md`
- `docs/operator_evidence_package_checklist.md`
- `docs/production_readiness_decision_checklist.md`
- `docs/operator_final_prerun_checklist.md`
- `docs/operator_post_run_review.md`
- `docs/examples/production_readiness_decision.example.md`
- `docs/examples/deployment_environment_validation.example.md`
- `docs/examples/backend_readiness_validation.example.md`
- `docs/examples/operator_evidence_package.example.md`
- `docs/web_h5_integration_checklist.md`
- `docs/web_h5_genios_integration.md`
- `docs/genios_handoff_evidence_template.md`
- `docs/staging_validation_record.md`
- `docs/centralized_logging.md`
- `docs/production_hardening.md`

## Boundary Reminder

This runbook operates the backend and its integration evidence. It does not train models, does not replace GeniOS, does not run RAG, does not generate explanation content, does not define GeniOS prompts, does not prove historical accuracy, and does not replace museum or expert review.

It also does not:

- implement digital humans
- implement AR/VR
