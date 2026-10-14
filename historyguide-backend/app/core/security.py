from secrets import compare_digest


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
    "/operator",
    "/operator/app.js",
    "/operator/styles.css",
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

def access_key_matches(provided: str | None, configured: str) -> bool:
    """Compare UTF-8 bytes so malformed non-ASCII headers fail without a 500."""
    return provided is not None and compare_digest(provided.encode("utf-8"), configured.encode("utf-8"))
