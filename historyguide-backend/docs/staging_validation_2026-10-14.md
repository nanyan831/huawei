# Isolated Staging Validation, 2026-10-14

This is a partial technical validation record, not a production go decision.
The public HistoryGuide service and its SQLite database were not migrated,
restarted, or replaced during this run.

## Environment

- Host: existing HistoryGuide server; staging files under `/tmp/nk-historyguide-staging-20261014`.
- Image: `nk-historyguide:staging-20261014`, Python 3.12.15; built from the local source whitelist.
- Runtime: Docker container `nk-historyguide-staging-20261014`, `--network none`, no published ports.
- Database: fresh, empty `/tmp/nk-historyguide-staging-20261014/data/staging.db`, separate from the live database.
- Keys: independently generated staging business and operator keys, mounted read-only from files. Values were not recorded here.
- Image and package mirrors were used because direct Docker Hub/PyPI access was slow or unavailable. Upstream artifact provenance has not been independently verified. Dependencies are range-based, not locked.

## Checks Completed

1. `alembic upgrade head` on the fresh staging database succeeded; migration rehearsal reached `0005_history_review_runs` with 10 tables.
2. Container startup in `HISTORYGUIDE_SCHEMA_MODE=migrated` succeeded. `/health`, `/ready`, `/api/system/database`, and both run-tool OpenAPI documents returned HTTP 200. The database endpoint reported `alembic_migrated_verified`.
3. All 221 tests passed locally and again in a disposable Python 3.12 container using the image's resolved runtime dependencies. One third-party TestClient deprecation warning remains in the container run.
4. `validate_runtime_config.py --profile staging`: 0 failures, 1 warning for empty CORS origins. Empty CORS is acceptable for this network-isolated check, but not proof of Web/H5 integration.
5. Read-only self-check: public endpoints returned 200; operator endpoints returned 401 without a key and 200 with the separate staging operator key. `/api/exhibits` returned 401 without a key and 200 with the staging business key.
6. `rehearse_legacy_adoption.py` read the live database through a read-only single-file mount. Its temporary backup uniquely matched migration `0002_audit_logs`; the temporary clone reached `0005_history_review_runs` and preserved all 4 original tables and 5 rows by digest. The live database was never stamped or upgraded.
7. The live `nk-historyguide.service` remained active after the checks.

## Gates Still Failing or Unproven

- Read-only staging data validation correctly failed: 0 exhibits and no approved `S01` or `S02` sources. This fresh staging database cannot serve real historical answers.
- No recoverable production backup, cutover, rollback drill, or actual live migration was performed.
- No real museum-approved source corpus, exhibit provenance approval, curator evaluation, Coze forced-review workflow, or real Coze trace was validated.
- The existing live business key was previously exposed and has not been rotated here. The live service still lacks the new operator-key setup.
- This staging container is intentionally inaccessible from the public Internet and from Coze. No Coze Agent or workflow was published or modified.

Decision: technical compatibility rehearsal passed; production and content release gates remain **NO-GO**.
