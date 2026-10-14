from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.exhibits import router as exhibits_router
from app.api.routes.genios_context import router as genios_context_router
from app.api.routes.genios_history_openapi import router as genios_history_openapi_router
from app.api.routes.genios_openapi import router as genios_openapi_router
from app.api.routes.genios_runs_openapi import router as genios_runs_openapi_router
from app.api.routes.health import router as health_router
from app.api.routes.operator_ui import router as operator_ui_router
from app.api.routes.history_review_runs import router as history_review_runs_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.review_runs import router as review_runs_router
from app.api.routes.route_plans import router as route_plans_router
from app.api.routes.visit_summaries import router as visit_summaries_router
from app.api.routes.visitor_states import router as visitor_states_router
from app.core.config import settings
from app.core.evidence_body_limit import EvidenceBodyLimitMiddleware
from app.core.logging import configure_logging
from app.core.request_context import attach_request_context
from app.core.security import (
    API_KEY_HEADER,
    OPERATOR_API_KEY_HEADER,
    PUBLIC_PATHS,
    access_key_matches,
    is_operator_path,
)
from app.database.init_db import init_db


def create_app() -> FastAPI:
    configure_logging()
    init_db(schema_mode=settings.schema_mode)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend service for NK HistoryGuide, focused on visitor state, "
            "exhibit data, and GeniOS collaboration context."
        ),
    )
    app.state.settings = settings
    app.add_middleware(EvidenceBodyLimitMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    if settings.api_key or settings.api_key_next or settings.operator_api_key:
        app.middleware("http")(require_access_keys)
    app.middleware("http")(attach_request_context)

    app.include_router(health_router)
    app.include_router(audit_logs_router)
    app.include_router(evidence_router)
    app.include_router(operator_ui_router)
    app.include_router(exhibits_router)
    app.include_router(visitor_states_router)
    app.include_router(recommendations_router)
    app.include_router(review_runs_router)
    app.include_router(history_review_runs_router)
    app.include_router(genios_context_router)
    app.include_router(genios_openapi_router)
    app.include_router(genios_runs_openapi_router)
    app.include_router(genios_history_openapi_router)
    app.include_router(visit_summaries_router)
    app.include_router(route_plans_router)
    return app


async def require_access_keys(request: Request, call_next: Callable[[Request], Response]) -> Response:
    settings = request.app.state.settings
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    evidence_path = request.url.path == "/api/evidence" or request.url.path.startswith("/api/evidence/")
    if evidence_path and not settings.operator_api_key:
        return JSONResponse(
            status_code=503,
            content={"detail": "Evidence operations require a configured operator API key."},
        )

    if settings.operator_api_key and is_operator_path(request.url.path):
        operator_key = request.headers.get(OPERATOR_API_KEY_HEADER)
        if not access_key_matches(operator_key, settings.operator_api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Valid HistoryGuide operator API key is required."},
            )
        return await call_next(request)

    accepted_business_keys = tuple(key for key in (settings.api_key, settings.api_key_next) if key)
    provided_key = request.headers.get(API_KEY_HEADER)
    if accepted_business_keys and (
        provided_key is None
        or not any(access_key_matches(provided_key, key) for key in accepted_business_keys)
    ):
        return JSONResponse(
            status_code=401,
            content={"detail": "Valid HistoryGuide API key is required."},
        )

    return await call_next(request)
app = create_app()
