# Staging Validation Record Example

This example uses placeholder values only. It is not evidence that staging has been validated.

## Run Metadata

- Date: 2026-09-26
- Operator: example-operator
- Environment name: staging-example
- Backend version or source revision: example-revision
- Database backend: sqlite-example
- Database URL label, not secret: staging-db-label
- Web/H5 origin: https://historyguide.example
- GeniOS environment: genios-staging-example
- Related request ids: example-request-001

## Required Inputs

- Verified exhibit seed file: data/verified-seed.example.json
- Source package location: museum-source-package.example
- Backup file path: backups/exhibits.staging.example.json
- Runtime config profile: staging
- Expected GeniOS test session id: staging-session-example
- Expected sourced exhibit ids: exhibit-example-001

## Runtime Config Gate

- Result: PASS
- Fail count: 0
- Warning count: 0
- API key configured without printing secret values: yes
- Operator key configured separately without printing secret values: yes
- CORS origins explicit: yes
- Log format: json
- Database URL profile: staging label checked
- Notes: Example only.

## Migration Gate

- Isolated migration rehearsal result: PASS
- Staging `alembic upgrade head` result: PASS
- Current Alembic revision: 0002_audit_logs
- Core tables present: yes
- Rollback plan confirmed: yes
- Notes: Example only.

## Data Safety Gate

- Export completed: yes
- Backup verification completed: yes
- Restore rehearsal completed: yes
- Import dry-run completed: yes
- Duplicate ids rejected if tested: yes
- Missing `source_reference` rejected if tested: yes
- Notes: Example only.

## Runtime Endpoint Gate

- Self-check result: PASS
- Returned request ids preserved: yes
- `GET /api/system/access-policy` checked: yes
- `GET /api/system/security-status` checked: yes
- `GET /api/system/operational-alerts` checked: yes
- Notes: Example only.

## Historical Content Safety Gate

- Unsourced real exhibits count: 0
- Quality issue count: 0
- `grounding_sources_complete`: true
- `source_safety.ready_for_generation`: true
- Missing exhibit ids: none
- Museum or expert review reference: review-record.example
- Notes: Example only.

## GeniOS Handoff Gate

- GeniOS context request id: example-request-101
- GeniOS grounding request id: example-request-102
- GeniOS preflight request id: example-request-103
- GeniOS handoff request id: example-request-104
- Handoff contains Visitor State: yes
- Handoff contains visit-event timeline: yes
- Handoff contains grounding exhibit ids: yes
- Backend did not generate explanation content: yes
- Notes: Example only.

## Centralized Logging Gate

- `HISTORYGUIDE_LOG_FORMAT=json`: yes
- `request_id` searchable: yes
- `status_code` searchable: yes
- `elapsed_ms` searchable: yes
- Deployment self-check request ids found in backend logs: yes
- No API key values observed in logs: yes
- Notes: Example only.

## Final Decision

- Proceed: yes
- Proceed with warnings: no
- Blocked: no
- Blocking issues: none
- Follow-up owner: example-owner
- Follow-up date: 2026-09-27
