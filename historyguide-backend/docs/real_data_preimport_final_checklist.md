# Real Data Pre-Import Final Checklist

Use this checklist immediately before importing verified museum exhibit records into NK HistoryGuide.

This is the final backend gate before `python scripts\import_exhibits.py <verified-seed-file>`. It does not create, infer, rewrite, or generate historical facts. It does not prove historical accuracy, does not replace museum or expert review, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, and does not implement AR/VR.

## Required Inputs

Have these ready:

- verified exhibit seed JSON file
- completed source review based on `docs/real_exhibit_seed_review.md`
- source package for every exhibit record
- reviewer or review-owner record outside the JSON file
- target environment name
- target database label, not secret
- current exhibit backup path
- restore rehearsal result
- staging validation record path
- rollback owner
- import operator
- GeniOS test `session_id`

Do not proceed when any exhibit lacks a source package or a non-empty `source_reference`.

## Gate 1: Source Package And Manual Review

Confirm every exhibit record has:

- stable `id` for QR, Web/H5, GeniOS, and future RAG metadata
- verified `name`
- source-backed `description`
- reviewed `period`
- reviewed `keywords`
- reviewed `people`
- reviewed `time_range`
- reviewed `themes`
- curator-approved `importance` rule
- non-empty `source_reference`
- no generated claims that are not backed by source material

Stop when source material is missing, unclear, or not approved for import.

## Gate 2: Seed Structure

Review the seed against `docs/exhibit_seed_format.md`.

Required fields:

- `id`
- `name`
- `description`
- `period`
- `keywords`
- `importance`
- `source_reference`

Recommended fields:

- `people`
- `time_range`
- `themes`

Stop when the JSON is not an array, required fields are missing, `importance` is outside 1 to 5, ids are temporary spreadsheet row numbers, metadata terms are inconsistent, or fixture records are mixed into verified museum records.

## Gate 3: Runtime And Migration

Run or confirm preserved output:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Stop when migration state is uncertain, the database target is unexpected, audit evidence is missing, or secrets are printed in evidence.

## Gate 4: Backup And Restore

Run before import:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-real-import.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-real-import.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-real-import.json
```

Confirm backup verification passed, restore rehearsal passed, backup path is recorded in `docs/staging_validation_record.md`, rollback owner is assigned, and rollback path is documented in `docs/backup_rollback_drill.md`.

Stop when backup verification fails, restore rehearsal fails, backup is empty when it should not be, or rollback ownership is unclear.

## Gate 5: Seed Dry-Run

Run:

```powershell
python scripts\import_exhibits.py --dry-run <verified-seed-file>
```

Dry-run must pass before import.

Confirm dry-run checked JSON shape, required fields, `importance`, non-empty `source_reference`, duplicate ids inside the seed file, and id conflicts with the current database.

Dry-run does not write records and does not prove historical accuracy.

## Gate 6: Pre-Import Runtime Evidence

Run or confirm preserved output:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
python scripts\validate_backend_readiness.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Confirm:

- `GET /ready` passes
- `GET /api/system/database` matches the intended target
- `GET /api/exhibits/source-report` has no unexpected unsourced real exhibits
- `GET /api/exhibits/quality-report` has acceptable metadata completeness for the import stage
- `GET /api/audit-logs/stats` is reachable
- `GET /api/system/operational-alerts` has no import-blocking `severity=fail`
- returned `X-HistoryGuide-Request-Id` values are preserved

Stop when readiness fails, source report is unexpected, quality report reveals unresolved required metadata gaps, audit stats cannot be checked, operational alerts show fail-level issues, or request ids cannot be preserved.

## Gate 7: Import Authorization

Import is allowed only when all prior gates pass.

Run:

```powershell
python scripts\import_exhibits.py <verified-seed-file>
```

If import fails because ids already exist, stop and compare the current database export, new verified seed file, QR code references, Web/H5 references, GeniOS metadata references, and previous Visitor State records.

Do not rename ids casually when QR codes, GeniOS metadata, or previous visit records may already refer to them.

## Gate 8: Immediate Post-Import Checks

After import, run:

```http
GET /ready
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/exhibits/facets
GET /api/audit-logs?action=exhibits_imported
GET /api/audit-logs/stats
GET /api/system/operational-alerts
```

Confirm source report has no unexpected `unsourced_exhibit_ids`, quality report is acceptable for the integration stage, facets show expected periods, keywords, people, and themes, import audit log exists, audit stats include `exhibits_imported`, operational alerts do not report source, audit, or rollback failures, and request ids are recorded.

## Gate 9: GeniOS Source-Safety Smoke

Create or reuse a test Visitor State that references imported exhibits.

Run:

```http
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Before drafting, require these necessary source-safety preflight checks:

- Visitor State integrity issue count is zero
- `grounding_sources_complete=true`
- `source_safety.ready_for_generation=true`
- `missing_exhibit_ids=[]`
- `unsourced_exhibit_ids=[]`
- preflight `ready_for_handoff=true`

These checks do not authorize display. A visitor-facing answer must use the matching exhibit/route or general-history review-run and display only `finalize.answer` after successful finalization. Stop display if preflight fails, review/finalize is skipped or fails, or the snapshot is stale.

## Evidence Update

Update:

- `docs/staging_validation_record.md`
- `docs/operator_evidence_package_checklist.md`
- `docs/production_readiness_decision_checklist.md` when the import supports a production-like or visitor-facing run
- `docs/operator_post_run_review.md` after the import run

Record seed file path, source package location, source review owner, dry-run output, import output, backup path, restore rehearsal result, request ids, source report result, quality report result, audit-log stats, GeniOS source-safety result, rollback owner, and follow-up owner.

Do not preserve secret values, full database URLs, private GeniOS prompts, raw source packages when they are not approved for sharing, unreviewed generated historical text, or visitor personal information not required for backend debugging.

## Stop Conditions

Stop or roll back when:

- source package is missing
- `source_reference` is empty
- dry-run fails
- backup verification fails
- restore rehearsal fails
- migration rehearsal or staging migration fails
- target database is unexpected
- import audit log is missing
- source report shows unexpected unsourced real exhibits
- GeniOS source safety is not ready
- request ids cannot be correlated
- operational alerts report `rollback_candidate`
- rollback owner is missing

## Boundary Reminder

The backend can validate structure, required fields, duplicate ids, database id conflicts, non-empty `source_reference`, source and quality reports, audit traces, and GeniOS handoff readiness. It cannot prove that historical interpretation is complete, current, or curator-approved.
