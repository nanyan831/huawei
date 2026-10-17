# Isolated Server Validation - 2026-10-18

## Scope

The current workspace was copied to a new server directory and built as image
`nk-historyguide:staging-20261018`. Production files, the production SQLite
database, the existing staging container, and the existing PostgreSQL service
were not used as test targets.

## Results

- The locked Docker image built successfully on the server.
- A new SQLite database migrated from an empty database through Alembic head
  `0008_claim_support_reviews`.
- The isolated SQLite container runs with `network=none` and no published
  ports. `/health`, `/ready`, `/operator`, `/openapi-genios-answers.json`, and
  `/openapi-genios-handoff.json` returned HTTP 200 from inside the container.
- A disposable PostgreSQL 16 container ran on an internal-only Docker network
  with a temporary in-memory data directory and no host port. All migrations
  through `0008_claim_support_reviews` succeeded.
- `validate_runtime_config.py --profile staging` passed with 0 failures and 0
  warnings using separate disposable business/operator keys, migrated schema
  mode, strict claim-support mode, JSON logging, explicit Coze CORS origin, and
  PostgreSQL.
- `verify_postgres_claim_release_lock.py --acknowledge-staging-write-test`
  passed. Concurrent revocation remained blocked until the release transaction
  committed, a fresh transaction observed the revocation, and synthetic probe
  records were cleaned.
- A disposable SQLite black-box run created a source and uploaded one exhibit
  through `POST /api/evidence/exhibits`. Both calls returned HTTP 201; the
  exhibit remained draft, its existing source was linked, and the detail read
  returned the link. The disposable database was removed afterward.

## Cleanup And Isolation

The temporary PostgreSQL container, internal network, upload-test container,
database URL environment file, and disposable upload database were removed.
The retained staging container has no published port. Production systemd status
and the public `/health` endpoint remained healthy after the checks. Secret
values were not copied into this record or printed by the validation commands.

## Decision

These results establish server-side build, migration, runtime, PostgreSQL lock,
and administrator-upload behavior for the current image. They do not establish
production deployment, public staging availability, Coze tool wiring, real
museum data approval, curator identity, backup/restore acceptance, or real
visitor traces. Release status remains **NO-GO**.
