PUBLIC_PATHS = {
    "/health",
    "/ready",
    "/api/system/database",
    "/openapi.json",
    "/openapi-genios-handoff.json",
    "/openapi-genios-review.json",
    "/openapi-genios-runs.json",
    "/openapi-genios-history-runs.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}

API_KEY_HEADER = "X-HistoryGuide-Api-Key"
OPERATOR_API_KEY_HEADER = "X-HistoryGuide-Operator-Key"

OPERATOR_PATHS = {
    "/api/system/access-policy",
    "/api/system/operational-alerts",
    "/api/system/security-status",
}
OPERATOR_PATH_PREFIXES = (
    "/api/audit-logs",
    "/api/evidence",
)


def is_operator_path(path: str) -> bool:
    return path in OPERATOR_PATHS or any(path.startswith(prefix) for prefix in OPERATOR_PATH_PREFIXES)
