# Real Exhibit Seed Review Checklist

Use this checklist before importing real Nankai history museum exhibit records into NK HistoryGuide. It is a data review guide for verified museum material. It does not create, infer, rewrite, or generate historical facts.

## Review Boundary

Codex and the backend may validate:

- JSON shape
- required fields
- duplicate ids
- database id conflicts
- `importance` range
- non-empty `source_reference`
- structured metadata completeness
- source grouping after import

Codex and the backend must not:

- invent exhibit descriptions
- fill missing historical facts
- judge historical truth beyond source presence
- replace museum or domain-expert review
- generate explanation text
- train or tune a model

## Required Source Package

Before preparing a seed file, collect a source package for every exhibit record:

- exhibit label, catalog card, curatorial text, archive record, or approved knowledge-base entry
- stable source reference, archive id, document title, page number, URL, or GeniOS knowledge-base reference
- reviewer name or review owner outside the JSON when project governance requires it
- date of source review outside the JSON when project governance requires it

If a record has no source package, do not import it.

## Seed File Requirements

Every real exhibit record must follow `docs/exhibit_seed_format.md`.

Required fields:

- `id`
- `name`
- `description`
- `period`
- `keywords`
- `importance`
- `source_reference`

Recommended metadata:

- `people`
- `time_range`
- `themes`

Use stable exhibit ids that can be reused by QR codes, Web/H5, GeniOS, and future RAG metadata. Avoid temporary spreadsheet row numbers as ids.

## Manual Review Checklist

Before dry-run, review each record:

- `id` is stable, unique, ASCII-safe, and meaningful for system integration.
- `name` matches the verified exhibit title.
- `description` is copied from or summarized from approved source material.
- `period` is controlled enough for filtering and route context.
- `keywords` include search and RAG metadata terms from the source package.
- `importance` is an integer from 1 to 5 and uses a consistent curatorial rule.
- `people` includes only source-supported people.
- `time_range` is present when the exhibit is tied to a clear time span.
- `themes` are consistent across the dataset.
- `source_reference` is non-empty and points to the source package.
- No field contains generated claims that are not backed by the source package.

## Dry-Run Gate

Run dry-run before every import:

```powershell
python scripts\import_exhibits.py --dry-run path\to\verified_exhibits.json
```

Dry-run must pass before import. It checks structure, required fields, `importance`, non-empty `source_reference`, duplicate ids inside the seed file, and id conflicts with the current database.

Dry-run is not a historical accuracy review. Passing dry-run means the file is structurally acceptable, not that all historical claims are correct.

## Backup Before Import

If the target database may already contain verified exhibit records, export before importing:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-import.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-import.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-import.json
```

Do not reset or overwrite a database containing verified museum records unless an export has been created and reviewed.

Backup verification checks structure, duplicate ids, required fields, and `source_reference` presence without connecting to the database. It does not prove historical accuracy and does not import records.

Restore rehearsal imports the backup into an isolated in-memory SQLite database and then discards it. It proves the backup can be restored by the current backend model, but it does not prove historical accuracy and does not modify the configured application database.

## Import Gate

Import only after source review, dry-run, and `docs/real_data_preimport_final_checklist.md` pass:

```powershell
python scripts\import_exhibits.py path\to\verified_exhibits.json
```

If import fails because ids already exist, stop and compare the existing database export with the new seed file. Do not rename ids casually if QR codes, GeniOS metadata, or previous visit records may already refer to them.

## Post-Import Checks

After import, start the backend and check:

```http
GET /ready
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/exhibits/facets
GET /api/genios/capabilities
```

Expected results:

- `/ready` reports database readiness.
- source report shows no unexpected `unsourced_exhibit_ids`.
- quality report shows acceptable metadata completeness for the integration stage.
- facets show expected periods, keywords, people, and themes.
- capabilities still describe the backend/GeniOS boundary.

## GeniOS Grounding Checks

Create or reuse a test Visitor State that references the imported exhibits, then verify:

```http
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Before generated explanation:

- `grounding_sources_complete` should be `true`.
- `unsourced_exhibit_ids` should be empty.
- `missing_exhibit_ids` should be empty.
- `source_safety.ready_for_generation` should be `true`.

If any condition fails, fix exhibit data or Visitor State references before GeniOS generated explanation.

## Rejection Conditions

Reject or hold the seed file when:

- any record lacks `source_reference`
- source material is missing or unclear
- ids collide unexpectedly
- descriptions include unsupported historical claims
- metadata uses inconsistent period, people, or theme names
- dry-run fails
- source report shows unsourced records after import
- grounding or handoff source-safety checks fail

## Handoff Notes For Reviewers

The backend can prove structural readiness and source-reference presence. It cannot prove that the museum interpretation is historically complete, current, or curator-approved. Keep expert review outside the backend workflow, then use the backend reports to confirm that the reviewed data entered the system intact.
