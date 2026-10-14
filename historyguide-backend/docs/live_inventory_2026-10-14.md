# Read-only live inventory: 2026-10-14

This is an observation record, not a deployment or approval record. The live service and database were not modified, copied, stamped, migrated, restarted, or backed up during this inventory. No key value or source body was read.

## Observed runtime

- SSH host identity matched the previously documented Ubuntu host. `nk-historyguide.service` was active, running Uvicorn from `/opt/nk-historyguide/.venv` with working directory `/opt/nk-historyguide` and an environment file at `/opt/nk-historyguide/historyguide.env`.
- Public `GET /api/system/database` reported SQLite and `sqlalchemy_create_all_mvp_with_alembic_scaffold`.
- The running virtualenv reported Python 3.10.12. `python3.11` and `python3.12` were not found on the host PATH. The current local project declares Python >=3.11; do not deploy it into the existing 3.10 virtualenv without a separately tested runtime plan.
- The environment file names, without values, were `HISTORYGUIDE_API_KEY`, `HISTORYGUIDE_DATABASE_URL`, and `HISTORYGUIDE_LOG_FORMAT`. The configured database path was confirmed as `/opt/nk-historyguide/historyguide.db` by exact-match check. No operator-key variable was found in that file or the systemd unit text.

## Observed database

- Read-only SQLite inspection found `exhibits`, `visitor_states`, `visitor_visit_events`, and `audit_logs`, plus the indexes expected of the early schema. There was **no** `alembic_version` table and no evidence-governance/review-run tables.
- Column and foreign-key listings were consistent with the `0002_audit_logs` migration stage, but without an Alembic version record this is a structural inference, not a verified migration revision. The adoption rehearsal must be performed on a consistent staging copy of the actual live database before any stamp/upgrade.
- Counts at inspection: 2 exhibits, 1 visitor state, 0 visit events, 2 audit logs. Both exhibit IDs had the `fixture-exhibit-*` prefix. `PRAGMA foreign_key_check` reported zero violations.

## Deployment implications

1. The local `0003`-`0005` source-governance and review-run features are not live. The Coze Agent still uses the legacy tools and has no enforced final-answer gateway.
2. Stage a current-code deployment separately from the live service, with a Python >=3.11 runtime, a distinct operator key, a rotated business key, and a restorable database backup. Do not use the fixture exhibits as historical evidence.
3. Rehearse migration adoption on a consistent copy of the actual live SQLite database. The local workspace database's successful rehearsal does not prove the server database will match exactly.
4. Obtain curator-approved source excerpts and reconcile Coze citation IDs with backend approved IDs before visitor-facing history answers. Test the forced pass/revise/block workflow and authentic Coze traces before publication.

The previously exposed business key remains a release risk. This inventory did not verify or rotate its value.
