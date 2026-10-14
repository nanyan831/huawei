# Staging Validation Record

Use this template when validating NK HistoryGuide in a staging or production-like environment. Keep one completed copy per staging run.

This record is evidence of operator checks. It does not prove historical accuracy, does not replace museum or expert review, does not train models, does not run RAG, and does not generate explanation content.

## Run Metadata

- Date:
- Operator:
- Environment name:
- Backend version or source revision:
- Database backend:
- Database URL label, not secret:
- Web/H5 origin:
- GeniOS environment:
- Related request ids:
- Operator evidence package path:
- Production readiness decision checklist completed:

## Required Inputs

- Verified exhibit seed file:
- Source package location:
- Real data import runbook reviewed:
- Backup and rollback drill reviewed:
- Backup file path:
- Runtime config profile:
- Expected GeniOS test session id:
- Expected sourced exhibit ids:

## Runtime Config Gate

Command:

```powershell
python scripts\validate_runtime_config.py --profile staging
```

Record:

- Result:
- Fail count:
- Warning count:
- API key configured without printing secret values:
- Operator key configured separately without printing secret values:
- CORS origins explicit:
- Log format:
- Database URL profile:
- Notes:

## Migration Gate

Commands:

```powershell
python scripts\rehearse_migrations.py
alembic upgrade head
python scripts\validate_staging_database.py
```

Record:

- Isolated migration rehearsal result:
- Staging `alembic upgrade head` result:
- Read-only staging database validation result:
- Current Alembic revision:
- Core tables present:
- Rollback plan confirmed:
- Notes:

## Data Safety Gate

Commands:

```powershell
python scripts\export_exhibits.py <backup-file>
python scripts\verify_exhibit_backup.py <backup-file> --require-non-empty
python scripts\rehearse_exhibit_restore.py <backup-file>
python scripts\import_exhibits.py --dry-run <verified-seed-file>
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Record:

- Export completed:
- Backup verification completed:
- Restore rehearsal completed:
- Rollback drill reviewed:
- Import dry-run completed:
- Post-import read-only staging database validation completed:
- Post-visit-event audit-log validation completed:
- Duplicate ids rejected if tested:
- Missing `source_reference` rejected if tested:
- Notes:

## Runtime Endpoint Gate

Command:

```powershell
python scripts\deployment_self_check.py --base-url <backend-url> --api-key <business-key> --operator-key <operator-key>
```

Record:

- Self-check result:
- Returned request ids preserved:
- `GET /api/system/access-policy` checked:
- `GET /api/system/security-status` checked:
- `GET /api/system/operational-alerts` checked:
- Notes:

## Historical Content Safety Gate

HTTP checks:

```http
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Record:

- Unsourced real exhibits count:
- Quality issue count:
- `grounding_sources_complete`:
- `source_safety.ready_for_generation`:
- Missing exhibit ids:
- Museum or expert review reference:
- Notes:

## GeniOS Handoff Gate

Reference:

```text
docs/genios_handoff_evidence_template.md
docs/examples/genios_handoff_evidence.example.md
```

Record:

- GeniOS context request id:
- GeniOS grounding request id:
- GeniOS preflight request id:
- GeniOS handoff request id:
- Handoff contains Visitor State:
- Handoff contains visit-event timeline:
- Handoff contains grounding exhibit ids:
- `grounding_sources_complete`:
- `source_safety.ready_for_generation`:
- GeniOS handoff evidence template completed:
- Backend did not generate explanation content:
- Notes:

## Centralized Logging Gate

Reference:

```text
docs/centralized_logging.md
docs/examples/structured_request_log.json
```

Record:

- `HISTORYGUIDE_LOG_FORMAT=json`:
- `request_id` searchable:
- `status_code` searchable:
- `elapsed_ms` searchable:
- Deployment self-check request ids found in backend logs:
- No API key values observed in logs:
- Notes:

## Final Decision

- Proceed:
- Proceed with warnings:
- Blocked:
- Blocking issues:
- Rollback required:
- Rollback owner:
- Follow-up owner:
- Follow-up date:
- Evidence package completed:
- Production readiness decision:

## Boundary Reminder

Do not use this record as:

- proof of historical accuracy
- source evidence for generated explanations
- visitor identity
- visitor profile data
- GeniOS prompt input
- RAG content
- a replacement for role-based access control
