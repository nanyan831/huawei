# Deployment Notes

This document describes lightweight deployment preparation for the NK HistoryGuide backend.

The backend remains responsible only for exhibit data, Visitor State, recommendations, and GeniOS context packages. It does not train models, replace GeniOS, generate explanation content, or implement digital humans, AR, or VR.

For production-like environments, also review `docs/production_hardening.md` and `docs/database_migrations.md`. They cover migration gates, backup and rollback expectations, API key checks, CORS checks, runtime monitoring, and the SQLite-to-PostgreSQL boundary.

## Environment Variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Supported variables:

```text
HISTORYGUIDE_APP_NAME
HISTORYGUIDE_APP_VERSION
HISTORYGUIDE_SERVICE_ID
HISTORYGUIDE_LOG_LEVEL
HISTORYGUIDE_LOG_FORMAT
HISTORYGUIDE_DATABASE_URL
HISTORYGUIDE_CORS_ORIGINS
HISTORYGUIDE_API_KEY
HISTORYGUIDE_API_KEY_NEXT
HISTORYGUIDE_OPERATOR_API_KEY
```

Default development database:

```text
sqlite:///./historyguide.db
```

Use `HISTORYGUIDE_LOG_FORMAT=json` when deployment logs are collected by a centralized logging platform. JSON request logs include `request_id`, `http_method`, `path`, `status_code`, and `elapsed_ms`. The default `text` format remains suitable for local development.

Before staging or production-like deployment, validate runtime environment variables:

```powershell
python scripts\validate_runtime_config.py --profile staging
python scripts\validate_runtime_config.py --profile production
```

The validator checks API key presence, operator key separation, CORS wildcard risk, database URL profile risk, log level, and log format without connecting to the database and without printing secret values.

For production-like deployment, prefer a managed database. Alembic scaffolding is available as the formal migration path, but the current runtime path is still verified with SQLite until migrations are validated in staging.

For Web/H5 integration, set allowed browser origins explicitly:

```text
HISTORYGUIDE_CORS_ORIGINS=http://localhost:5173,https://your-historyguide-web.example
```

Leave it empty when the backend is not called directly from a browser.

For deployment beyond local demos, set an API key:

```text
HISTORYGUIDE_API_KEY=<generate-a-secret>
```

When configured, business APIs require:

```text
X-HistoryGuide-Api-Key: <generate-a-secret>
```

For operator-only endpoints such as audit logs, operational alerts, and security status, set:

```text
HISTORYGUIDE_OPERATOR_API_KEY=<generate-a-separate-operator-secret>
```

When configured, operator APIs require:

```text
X-HistoryGuide-Operator-Key: <generate-a-separate-operator-secret>
```

Health, readiness, database status, and OpenAPI docs remain public for deployment probes. `GET /api/system/security-status` reports configured key controls without exposing key values and is protected like an operator endpoint when `HISTORYGUIDE_OPERATOR_API_KEY` is configured.

For an exposed business key, use the bounded dual-key cutover in `docs/business_key_rotation.md`. The source of truth for the deployed service's environment may differ from this repository; inspect the running unit/wrapper before changing it.

## Local Production-Style Run

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```text
GET /health
```

Readiness check:

```text
GET /ready
```

Database status check:

```text
GET /api/system/database
GET /api/system/security-status
GET /api/system/access-policy
```

Use the database endpoint to confirm whether the service is running on the verified SQLite MVP backend or another configured SQLAlchemy backend. It intentionally does not expose the full database URL. Use the security status endpoint to confirm business/operator key controls and protected path groups without exposing secret values. Use the access policy endpoint to confirm coarse public, business, operator, and local script boundaries without exposing key values; it is not full RBAC.

Run the read-only deployment self-check:

```powershell
python scripts\deployment_self_check.py --base-url http://127.0.0.1:8000
```

For protected deployments, provide keys as arguments or environment variables:

```powershell
python scripts\deployment_self_check.py --base-url http://127.0.0.1:8000 --api-key <business-key> --operator-key <operator-key>
```

The self-check calls these read-only endpoints:

- `GET /health`
- `GET /ready`
- `GET /api/system/database`
- `GET /openapi.json`
- `GET /api/system/access-policy`
- `GET /api/system/security-status`
- `GET /api/system/operational-alerts`

It does not write to the database, prints returned `X-HistoryGuide-Request-Id` values for log correlation, and does not print key values.

## Docker Build

```powershell
docker build -t nk-historyguide-backend .
```

## Docker Run

```powershell
docker run --rm -p 8000:8000 `
  -e HISTORYGUIDE_DATABASE_URL=sqlite:////app/historyguide.db `
  nk-historyguide-backend
```

For persistent SQLite data, mount a volume and set the database URL to the mounted path.

Example:

```powershell
docker run --rm -p 8000:8000 `
  -v ${PWD}\runtime-data:/data `
  -e HISTORYGUIDE_DATABASE_URL=sqlite:////data/historyguide.db `
  nk-historyguide-backend
```

## Deployment Checklist

- Use verified exhibit seed data, not development fixtures.
- Keep a copy of every imported source JSON file.
- Confirm `GET /health`.
- Confirm `GET /ready` returns `database: ok`.
- Confirm `GET /api/system/database` reports the expected backend and persistence mode.
- Confirm `GET /api/system/security-status` reports configured key controls without exposing secret values.
- Confirm `GET /api/system/access-policy` reports coarse access boundaries without exposing key values.
- Run `python scripts\deployment_self_check.py --base-url <backend-url>` after the service starts.
- Run `python scripts\rehearse_migrations.py` before migration-related staging work to verify `alembic upgrade head` on an isolated temporary SQLite database.
- Keep the self-check output request ids when reporting deployment failures.
- Confirm OpenAPI routes at `/openapi.json`.
- Set `HISTORYGUIDE_API_KEY` for shared or public deployments.
- Confirm protected APIs reject missing or invalid `X-HistoryGuide-Api-Key`.
- Set `HISTORYGUIDE_OPERATOR_API_KEY` for shared or production-like deployments that expose audit or operational endpoints.
- Confirm operator APIs reject missing or invalid `X-HistoryGuide-Operator-Key`.
- Confirm operator APIs do not accept the ordinary business API key when an operator key is configured.
- Confirm `GET /api/system/security-status` requires `X-HistoryGuide-Operator-Key` when an operator key is configured.
- Confirm GeniOS can reach `/api/genios/context/{session_id}`.
- Confirm Web/H5 origins are listed in `HISTORYGUIDE_CORS_ORIGINS` before browser-based integration.
- Confirm logs are visible in the hosting environment.
- Do not expose unprotected admin or import operations; the import script is a local/operator workflow.

## Database Migration Notes

The local MVP defaults to SQLAlchemy `create_all`. Staging and production-like services must use `HISTORYGUIDE_SCHEMA_MODE=migrated` after Alembic migration; startup then verifies the head/schema and will not create missing tables. For unversioned SQLite, rehearse adoption on a temporary copy first (see `docs/database_migrations.md`). Before production PostgreSQL use:

- export verified exhibit data with `scripts/export_exhibits.py`
- verify exported exhibit backups with `scripts/verify_exhibit_backup.py --require-non-empty`
- rehearse backup restore with `scripts/rehearse_exhibit_restore.py`
- rehearse Alembic migrations with `python scripts\rehearse_migrations.py` against an isolated temporary SQLite database
- keep original verified seed JSON files
- apply and validate Alembic migrations against a staging database
- test migrations against a staging database
- re-run exhibit quality and source reports after import or migration

Do not treat a PostgreSQL URL alone as production readiness. The migration rehearsal verifies the current Alembic revision and core tables, but it does not modify the configured application database, does not import records, and does not prove PostgreSQL production-ready status.

See `docs/database_migrations.md` and `docs/production_hardening.md` before moving beyond the verified SQLite MVP path.
