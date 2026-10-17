from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    API_KEY_HEADER,
    OPERATOR_API_KEY_HEADER,
    OPERATOR_PATH_PREFIXES,
    OPERATOR_PATHS,
    PUBLIC_PATHS,
)
from app.database.session import engine, get_db
from app.schemas.system import AccessPolicyEntry, AccessPolicyResponse, OperationalAlertsResponse, SecurityStatusResponse
from app.services.operational_alert_service import get_operational_alerts


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(HealthResponse):
    database: str


class DatabaseStatusResponse(BaseModel):
    service: str
    version: str
    backend: str
    driver: str
    persistence: str
    schema_management: str
    migration_target: str
    production_note: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_id,
        version=settings.app_version,
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(db: Session = Depends(get_db)) -> ReadinessResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database readiness check failed.",
        ) from exc

    return ReadinessResponse(
        status="ready",
        service=settings.service_id,
        version=settings.app_version,
        database="ok",
    )


@router.get("/api/system/database", response_model=DatabaseStatusResponse)
def database_status() -> DatabaseStatusResponse:
    backend = engine.url.get_backend_name()
    driver = engine.url.drivername
    return DatabaseStatusResponse(
        service=settings.service_id,
        version=settings.app_version,
        backend=backend,
        driver=driver,
        persistence=_database_persistence(backend),
        schema_management=(
            "alembic_migrated_verified"
            if settings.schema_mode == "migrated"
            else "sqlalchemy_create_all_mvp_with_alembic_scaffold"
        ),
        migration_target="alembic_staging_then_postgresql",
        production_note=(
            "SQLite is the verified MVP backend. Alembic migration scaffolding is available, but "
            "production PostgreSQL still requires staging migration validation and verified exhibit backups."
        ),
    )


@router.get("/api/system/operational-alerts", response_model=OperationalAlertsResponse)
def operational_alerts(db: Session = Depends(get_db)) -> OperationalAlertsResponse:
    return get_operational_alerts(db)


@router.get("/api/system/security-status", response_model=SecurityStatusResponse)
def security_status(request: Request) -> SecurityStatusResponse:
    runtime_settings = request.app.state.settings
    return SecurityStatusResponse(
        service=runtime_settings.service_id,
        version=runtime_settings.app_version,
        business_api_key_configured=bool(runtime_settings.api_key or runtime_settings.api_key_next),
        business_api_key_rotation_staged=bool(runtime_settings.api_key_next),
        operator_api_key_configured=bool(runtime_settings.operator_api_key),
        visitor_gateway_enabled=runtime_settings.visitor_gateway_enabled,
        business_apis_require_api_key=bool(runtime_settings.api_key or runtime_settings.api_key_next),
        operator_apis_require_operator_key=bool(runtime_settings.operator_api_key),
        business_api_key_header=API_KEY_HEADER,
        operator_api_key_header=OPERATOR_API_KEY_HEADER,
        public_probe_paths=sorted(PUBLIC_PATHS),
        operator_paths=sorted(OPERATOR_PATHS),
        operator_path_prefixes=sorted(OPERATOR_PATH_PREFIXES),
        production_note=(
            "This endpoint reports whether optional API key controls are configured. "
            "It never returns configured key values and is not a replacement for full RBAC."
        ),
    )


@router.get("/api/system/access-policy", response_model=AccessPolicyResponse)
def access_policy(request: Request) -> AccessPolicyResponse:
    runtime_settings = request.app.state.settings
    return AccessPolicyResponse(
        service=runtime_settings.service_id,
        version=runtime_settings.app_version,
        policies=[
            AccessPolicyEntry(
                name="public_probe",
                access_level="public",
                required_header=None,
                paths=sorted(PUBLIC_PATHS),
                notes="Deployment probes and API documentation remain public when API key protection is enabled.",
            ),
            AccessPolicyEntry(
                name="business_api",
                access_level="business_api_key",
                required_header=API_KEY_HEADER if runtime_settings.api_key or runtime_settings.api_key_next else None,
                paths=[],
                path_prefixes=["/api"],
                notes=(
                    "Ordinary backend APIs use the business API key when configured. "
                    "Operator paths use the operator key; enabled visitor paths use scoped bearer tokens."
                ),
            ),
            AccessPolicyEntry(
                name="visitor_gateway",
                access_level="visitor_token",
                required_header="Authorization" if runtime_settings.visitor_gateway_enabled else None,
                paths=(
                    ["/api/visitor/me", "/api/visitor/revoke", "/api/visitor/route", "/api/visitor/visit-events",
                     "/api/visitor/answers/history", "/api/visitor/answers/exhibit"]
                    if runtime_settings.visitor_gateway_enabled else []
                ),
                path_prefixes=["/api/visitor/exhibits/"] if runtime_settings.visitor_gateway_enabled else [],
                notes=(
                    "Disabled by default. A trusted business-key caller provisions a short-lived "
                    "session-bound token at /api/visitor/grants; trusted callers can revoke a session at "
                    "/api/visitor/grants/revoke; visitor paths never accept the business key."
                ),
            ),
            AccessPolicyEntry(
                name="operator_api",
                access_level="operator_api_key",
                required_header=OPERATOR_API_KEY_HEADER if runtime_settings.operator_api_key else None,
                paths=sorted(OPERATOR_PATHS),
                path_prefixes=sorted(OPERATOR_PATH_PREFIXES),
                notes=(
                    "Audit, operational, security, and access-policy endpoints are operator-facing. "
                    "They expose operational metadata and never return configured key values."
                ),
            ),
            AccessPolicyEntry(
                name="local_operator_workflow",
                access_level="local_operator_workflow",
                required_header=None,
                paths=[],
                path_prefixes=["scripts/"],
                notes=(
                    "Import, export, backup verification, restore rehearsal, deployment self-check, "
                    "and migration rehearsal scripts are local/operator workflows, not public HTTP APIs."
                ),
            ),
        ],
        production_note=(
            "This endpoint documents current coarse access boundaries for deployment and integration checks. "
            "It does not implement user accounts, per-person authorization, or full RBAC."
        ),
    )


def _database_persistence(backend: str) -> str:
    if backend == "sqlite":
        database = engine.url.database
        if database in (None, "", ":memory:"):
            return "in_memory"
        return "local_file"
    return "external_service"
