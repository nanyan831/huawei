# Backup And Rollback Drill

Use this checklist before any production-like change that could affect verified exhibit data, Visitor State expectations, GeniOS handoff readiness, or Web/H5 integration behavior.

This is an operational drill for the NK HistoryGuide backend. It does not prove historical accuracy, does not replace museum or expert review, does not train models, does not run RAG, and does not generate explanation content.

## When To Run

Run this drill before:

- importing verified real exhibit data
- resetting a database that may contain verified museum records
- applying Alembic migrations to staging or production-like databases
- changing `HISTORYGUIDE_DATABASE_URL`
- changing `HISTORYGUIDE_API_KEY` or `HISTORYGUIDE_OPERATOR_API_KEY`
- changing `HISTORYGUIDE_CORS_ORIGINS` for Web/H5 integration
- switching deployment target, volume, or database provider
- running a GeniOS handoff demo with real exhibit records

## Required Inputs

Record these before the change:

- operator:
- date:
- environment name:
- backend version or source revision:
- database URL label, not secret:
- current `HISTORYGUIDE_DATABASE_URL` label:
- current `HISTORYGUIDE_CORS_ORIGINS`:
- backup file path:
- verified seed file path:
- related source package path:
- expected GeniOS test session id:
- rollback owner:
- rollback deadline:

Never paste secret values for `HISTORYGUIDE_API_KEY`, `HISTORYGUIDE_OPERATOR_API_KEY`, or database credentials into this document.

## 1. Pre-Change Runtime Gate

Run:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Record:

- runtime config validation result:
- deployment self-check result:
- returned `X-HistoryGuide-Request-Id` values:
- staging database validation result:
- current Alembic revision:
- core tables present:
- exhibit count:
- unsourced exhibit count:
- audit-log count:

Stop if runtime config validation fails, readiness fails, core tables are missing, or the staging database is not at the expected Alembic head.

## 2. Backup Gate

Export and verify exhibit records:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.json
```

Record:

- export completed:
- exported exhibit count:
- backup verification completed:
- restore rehearsal completed:
- sourced exhibit count:
- unsourced exhibit count:
- backup storage location:
- backup owner:

Stop if backup verification fails, restore rehearsal fails, the backup is empty when it should not be, or any verified museum record lacks `source_reference`.

## 3. Change Gate

Run only the intended change. Examples:

```powershell
alembic upgrade head
python scripts\import_exhibits.py --dry-run <verified-seed-file>
python scripts\import_exhibits.py <verified-seed-file>
```

Record:

- change type:
- command:
- result:
- request ids, if a running backend was involved:
- operator notes:

Do not make unrelated code, data, environment, or GeniOS configuration changes during the same drill.

## 4. Post-Change Validation Gate

Run:

```powershell
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Then check:

```http
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/visitor-states/{session_id}/integrity
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Record:

- staging database validation result:
- deployment self-check result:
- source report unsourced count:
- quality issue count:
- Visitor State integrity result:
- `grounding_sources_complete`:
- `source_safety.ready_for_generation`:
- `missing_exhibit_ids`:
- `unsourced_exhibit_ids`:
- returned `X-HistoryGuide-Request-Id` values:

Stop and roll back if source safety fails, grounding is incomplete, exhibit ids are missing, the visit-event timeline is inconsistent, or request ids cannot be correlated.

## 5. Rollback Decision

Rollback is required when:

- `/ready` fails after the change
- the database is not at the expected Alembic head
- verified exhibit records are missing or duplicated unexpectedly
- real exhibit records have empty `source_reference`
- `grounding_sources_complete=false`
- `source_safety.ready_for_generation=false`
- Visitor State integrity fails for the expected test session
- Web/H5 or GeniOS clients receive repeated unexpected `401`
- request ids cannot be found in backend logs

Rollback is not complete until exhibit data, Visitor State expectations, Web/H5 settings, GeniOS integration settings, and runtime environment variables are all returned to a known working state.

## 6. Rollback Execution Record

Record the exact rollback plan before executing it:

- restore database or volume from:
- restore exhibit seed or backup file:
- restore backend image or source revision:
- restore `HISTORYGUIDE_DATABASE_URL` label:
- restore `HISTORYGUIDE_CORS_ORIGINS`:
- restore API key configuration from secret store:
- restore GeniOS environment or handoff configuration:
- restore Web/H5 backend base URL:
- expected post-rollback request ids:

After rollback, rerun:

```powershell
python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty
python scripts\rehearse_exhibit_restore.py <backup-file>
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Then recheck:

```http
GET /api/exhibits/source-report
GET /api/genios/handoff/{session_id}
```

Record:

- rollback execution result:
- exhibit count after rollback:
- unsourced exhibit count after rollback:
- audit-log count after rollback:
- `source_safety.ready_for_generation` after rollback:
- request ids after rollback:
- remaining issues:

## Boundary Reminder

This drill protects backend data and integration readiness. It does not prove historical accuracy, does not replace museum or expert review, does not train models, does not run RAG, does not generate explanation content, and does not define a GeniOS prompt.

It also does not:

- validate historical interpretation
- certify museum source quality
- implement digital humans
- implement AR/VR
