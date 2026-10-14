# Deployment Environment Validation Example

This example uses placeholder values only. It is not evidence that any real staging, production-like, or museum deployment has been validated.

Do not paste secret values, database credentials, private prompts, or unreviewed generated historical text into a real deployment validation record.

## Run Metadata

- Date: 2026-09-26
- Operator: example-operator
- Environment name: staging-example
- Backend base URL: https://historyguide-backend.example
- Backend version or source revision: example-revision
- Database backend: sqlite-example
- Database URL label, not secret: staging-db-label
- Web/H5 origin: https://historyguide.example
- GeniOS environment: genios-staging-example
- Test session id: staging-session-example
- Expected sourced exhibit ids: fixture-exhibit-001, fixture-exhibit-002
- Related request ids: example-request-301, example-request-302, example-request-303

## Runtime Config Evidence

Command:

```powershell
python scripts\validate_runtime_config.py --profile staging
```

Record:

- Result: PASS
- Fail count: 0
- Warning count: 0
- `HISTORYGUIDE_API_KEY` configured without printing secret values: yes
- `HISTORYGUIDE_OPERATOR_API_KEY` configured separately without printing secret values: yes
- `HISTORYGUIDE_CORS_ORIGINS` explicit: yes
- `HISTORYGUIDE_LOG_FORMAT`: json
- Notes: Example only.

## Read-Only Deployment Self-Check Evidence

Command:

```powershell
python scripts\deployment_self_check.py --base-url https://historyguide-backend.example --api-key <business-key> --operator-key <operator-key>
```

Record:

- Result: PASS
- `GET /health`: PASS, request id example-request-301
- `GET /ready`: PASS, request id example-request-302
- `GET /api/system/database`: PASS, request id example-request-303
- `GET /api/system/access-policy`: PASS, request id example-request-304
- `GET /api/system/security-status`: PASS, request id example-request-305
- `GET /api/system/operational-alerts`: PASS, request id example-request-306
- Secret values printed: no
- Database writes performed: no
- Notes: Example only.

## Database Validation Evidence

Command:

```powershell
python scripts\validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs
```

Record:

- Result: PASS
- Current Alembic head: 0002_audit_logs
- Core tables present: yes
- Exhibit count: 2
- Unsourced exhibit count: 0
- Visitor State count: 1
- Visit-event count: 1
- Audit-log count: 3
- Notes: Example only. These are placeholder counts.

## Data Safety Evidence

Commands:

```powershell
python scripts\export_exhibits.py backups\exhibits.before-change.example.json
python scripts\verify_exhibit_backup.py backups\exhibits.before-change.example.json --require-non-empty
python scripts\rehearse_exhibit_restore.py backups\exhibits.before-change.example.json
```

Record:

- Export completed: yes
- Backup verification completed: yes
- Restore rehearsal completed: yes
- Backup file path: backups/exhibits.before-change.example.json
- Source package reference preserved: yes
- Notes: Example only.

## Web/H5 Evidence

Record:

- Intended origin included in `HISTORYGUIDE_CORS_ORIGINS`: yes
- Browser preflight checked: yes
- `X-HistoryGuide-Api-Key` sent when required: yes
- `X-HistoryGuide-Request-Id` preserved by Web/H5 logs: yes
- `POST /api/visitor-states/{session_id}/visit-events` used for scan events: yes
- Notes: Example only.

## GeniOS Handoff Evidence

Reference:

```text
docs/genios_handoff_evidence_template.md
docs/examples/genios_handoff_evidence.example.md
```

Record:

- `GET /api/genios/context/{session_id}` request id: example-request-401
- `GET /api/genios/grounding/{session_id}` request id: example-request-402
- `GET /api/genios/preflight/{session_id}` request id: example-request-403
- `GET /api/genios/handoff/{session_id}` request id: example-request-404
- `grounding_sources_complete`: true
- `source_safety.ready_for_generation`: true
- `missing_exhibit_ids`: none
- `unsourced_exhibit_ids`: none
- Backend generated explanation content: no
- Notes: Example only. GeniOS RAG and generated explanation are outside this backend record.

## Centralized Logging Evidence

Record:

- `HISTORYGUIDE_LOG_FORMAT=json`: yes
- `request_id` searchable: yes
- `status_code` searchable: yes
- `elapsed_ms` searchable: yes
- Deployment self-check request ids found: yes
- GeniOS handoff request ids found: yes
- No `HISTORYGUIDE_API_KEY` values observed in logs: yes
- No `HISTORYGUIDE_OPERATOR_API_KEY` values observed in logs: yes
- Notes: Example only.

## Final Decision

- Proceed: yes
- Proceed with warnings: no
- Blocked: no
- Rollback required: no
- Blocking issues: none
- Follow-up owner: example-owner
- Follow-up date: 2026-09-27

## Boundary Reminder

This example is placeholder-only and not deployment evidence. It does not prove historical accuracy, does not replace museum or expert review, does not train models, does not run RAG, does not generate explanation content, does not define GeniOS prompts, and does not implement digital human or AR/VR features.
