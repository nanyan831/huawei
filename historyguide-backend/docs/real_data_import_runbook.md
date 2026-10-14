# Real Data Import Runbook

Use this runbook when importing verified museum exhibit records into NK HistoryGuide.

This runbook is an operator checklist. It does not create, infer, rewrite, or generate historical facts. It does not replace museum or expert review, does not train models, does not run RAG, and does not generate explanation content.

## Required Documents

Review these documents before import:

- `docs/exhibit_seed_format.md`
- `docs/real_exhibit_seed_review.md`
- `docs/real_data_preimport_final_checklist.md`
- `docs/staging_validation_record.md`
- `docs/centralized_logging.md`
- `docs/production_hardening.md`

## Pre-Import Inputs

Prepare:

- verified exhibit seed JSON file
- source package for every exhibit
- reviewer or review-owner record outside the JSON file
- target environment name
- current database backup path
- staging validation record path
- Web/H5 origin if browser clients call the backend
- GeniOS test session id

Do not import a seed file if any exhibit lacks a source package or a non-empty `source_reference`.

## Step 1: Manual Source Review

For each exhibit:

- confirm `id` is stable for QR, Web/H5, GeniOS, and future RAG metadata
- confirm `name` matches the verified museum title
- confirm `description` is source-backed
- confirm `period`, `keywords`, `people`, `time_range`, and `themes` use reviewed metadata
- confirm `importance` uses a consistent curator-approved rule
- confirm `source_reference` points to the source package
- reject generated claims that are not backed by source material

Record the review outcome in `docs/staging_validation_record.md` or a copied run record.

## Step 2: Runtime Config Gate

Run:

```powershell
python scripts\validate_runtime_config.py --profile staging
```

For production-like import rehearsal, also run:

```powershell
python scripts\validate_runtime_config.py --profile production
```

Do not proceed if required secrets, CORS, database URL profile, or log format checks fail. The validator does not connect to the database and does not print secret values.

## Step 3: Migration Gate

Run:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
```

Confirm:

- isolated migration rehearsal passes
- staging migration reaches the current Alembic head
- rollback plan is recorded

The migration rehearsal does not modify the configured application database and does not make PostgreSQL production-ready by itself.

## Step 4: Backup Gate

Before changing a database that may contain verified records, run:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-real-import.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-real-import.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-real-import.json
```

Do not proceed if backup verification or restore rehearsal fails.

Backup verification and restore rehearsal do not prove historical accuracy.

## Step 5: Seed Dry-Run Gate

Run:

```powershell
python scripts\import_exhibits.py --dry-run path\to\verified_exhibits.json
```

Dry-run must pass before import. It checks JSON shape, required fields, `importance`, non-empty `source_reference`, duplicate ids inside the seed file, and id conflicts with the current database.

Dry-run does not write records and does not prove historical accuracy.

## Step 6: Import Gate

Run import only after source review, runtime config validation, migration checks, backup checks, restore rehearsal, dry-run, and `docs/real_data_preimport_final_checklist.md` pass:

```powershell
python scripts\import_exhibits.py path\to\verified_exhibits.json
```

If import fails because ids already exist, stop and compare the existing export with the new seed file. Do not rename ids casually if QR codes, GeniOS metadata, or previous visit records may already refer to them.

## Step 7: Post-Import Backend Checks

Start the backend and check:

```http
GET /ready
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/exhibits/facets
GET /api/audit-logs?action=exhibits_imported
GET /api/system/operational-alerts
```

Expected:

- readiness succeeds
- source report has no unexpected unsourced real exhibits
- quality report has acceptable metadata completeness for the integration stage
- facets show expected periods, keywords, people, and themes
- import audit log exists
- operational alerts do not report unexpected source or audit failures

## Step 8: GeniOS Handoff Checks

Create or reuse a test Visitor State that references imported exhibits, then check:

```http
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Before GeniOS generated explanation:

- `grounding_sources_complete` should be `true`
- `unsourced_exhibit_ids` should be empty
- `missing_exhibit_ids` should be empty
- `source_safety.ready_for_generation` should be `true`

If any condition fails, fix exhibit data or Visitor State references before GeniOS generated explanation.

## Step 9: Logging And Evidence

Use:

```text
X-HistoryGuide-Request-Id
docs/centralized_logging.md
docs/staging_validation_record.md
```

Record:

- request ids for deployment self-check
- request ids for source report and quality report
- request ids for GeniOS grounding, preflight, and handoff
- import audit log id or timestamp
- source review reference
- staging validation decision

Do not log API key values, source packages, unreviewed historical content, or generated explanation text.

## Stop Conditions

Stop the import when:

- source package is missing
- `source_reference` is empty
- dry-run fails
- backup verification fails
- restore rehearsal fails
- migration rehearsal or staging migration fails
- source report shows unexpected unsourced real exhibits
- GeniOS source safety is not ready
- request logs or audit logs cannot be correlated during staging

## Boundary Reminder

The backend can validate structure, source-reference presence, duplicate ids, database conflicts, reports, and handoff readiness. It cannot prove that historical interpretation is complete, current, or curator-approved.
