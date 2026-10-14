from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings


Profile = Literal["local", "staging", "production"]
Severity = Literal["pass", "warn", "fail"]

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_LOG_FORMATS = {"text", "json"}
LOCAL_DATABASE_URL = "sqlite:///./historyguide.db"


@dataclass(frozen=True)
class ConfigCheck:
    name: str
    severity: Severity
    detail: str


def validate_runtime_config(settings: Settings, *, profile: Profile) -> list[ConfigCheck]:
    checks = [
        _check_business_key(settings, profile),
        _check_operator_key(settings, profile),
        _check_operator_key_is_separate(settings),
        _check_business_key_rotation(settings),
        _check_cors(settings, profile),
        _check_database_url(settings, profile),
        _check_schema_mode(settings, profile),
        _check_log_level(settings),
        _check_log_format(settings, profile),
    ]
    return checks


def _check_business_key(settings: Settings, profile: Profile) -> ConfigCheck:
    if settings.api_key or settings.api_key_next:
        return ConfigCheck("business_api_key", "pass", "configured without exposing key value")
    if profile == "local":
        return ConfigCheck("business_api_key", "warn", "empty; acceptable only for local demos or trusted private runs")
    return ConfigCheck("business_api_key", "fail", "required for shared, staging, or production-like deployments")


def _check_operator_key(settings: Settings, profile: Profile) -> ConfigCheck:
    if settings.operator_api_key:
        return ConfigCheck("operator_api_key", "pass", "configured without exposing key value")
    if profile == "local":
        return ConfigCheck("operator_api_key", "warn", "empty; operator endpoints are unseparated in local demos")
    return ConfigCheck("operator_api_key", "fail", "required for operator endpoints in staging or production-like deployments")


def _check_operator_key_is_separate(settings: Settings) -> ConfigCheck:
    business_keys = tuple(key for key in (settings.api_key, settings.api_key_next) if key)
    if not business_keys or not settings.operator_api_key:
        return ConfigCheck("operator_key_separation", "warn", "cannot verify separation until both keys are configured")
    if settings.operator_api_key in business_keys:
        return ConfigCheck("operator_key_separation", "fail", "operator key must not reuse the business API key")
    return ConfigCheck("operator_key_separation", "pass", "business and operator keys are configured separately")


def _check_business_key_rotation(settings: Settings) -> ConfigCheck:
    if not settings.api_key_next:
        return ConfigCheck("business_key_rotation", "pass", "no secondary business key active")
    if settings.api_key_next == settings.api_key:
        return ConfigCheck("business_key_rotation", "fail", "staged business key must differ from current key")
    return ConfigCheck(
        "business_key_rotation", "warn",
        "secondary business key is active; complete plugin cutover and remove the exposed old key promptly",
    )


def _check_cors(settings: Settings, profile: Profile) -> ConfigCheck:
    if "*" in settings.cors_origins:
        return ConfigCheck("cors_origins", "fail", "wildcard origins are not allowed for Web/H5 integration")
    if settings.cors_origins:
        return ConfigCheck("cors_origins", "pass", "explicit origins configured")
    if profile == "local":
        return ConfigCheck("cors_origins", "pass", "empty; browser CORS is disabled")
    return ConfigCheck("cors_origins", "warn", "empty; Web/H5 browser clients cannot call the backend directly")


def _check_database_url(settings: Settings, profile: Profile) -> ConfigCheck:
    if not settings.database_url.strip():
        return ConfigCheck("database_url", "fail", "database URL is empty")
    if profile == "production" and _is_sqlite(settings.database_url):
        return ConfigCheck(
            "database_url",
            "fail",
            "SQLite is not enough by itself for production; use staging-validated migrations before PostgreSQL",
        )
    if profile == "staging" and settings.database_url == LOCAL_DATABASE_URL:
        return ConfigCheck("database_url", "warn", "using the default local SQLite path in staging")
    return ConfigCheck("database_url", "pass", "configured")


def _check_schema_mode(settings: Settings, profile: Profile) -> ConfigCheck:
    if settings.schema_mode not in {"auto_create", "migrated"}:
        return ConfigCheck("schema_mode", "fail", "unsupported schema mode")
    if profile in {"staging", "production"} and settings.schema_mode != "migrated":
        return ConfigCheck("schema_mode", "fail", "shared deployments require migrated schema mode")
    return ConfigCheck("schema_mode", "pass", f"configured as {settings.schema_mode}")


def _check_log_level(settings: Settings) -> ConfigCheck:
    if settings.log_level.upper() in VALID_LOG_LEVELS:
        return ConfigCheck("log_level", "pass", f"configured as {settings.log_level.upper()}")
    return ConfigCheck("log_level", "fail", f"unsupported log level: {settings.log_level}")


def _check_log_format(settings: Settings, profile: Profile) -> ConfigCheck:
    log_format = settings.log_format.lower()
    if log_format not in VALID_LOG_FORMATS:
        return ConfigCheck("log_format", "fail", f"unsupported log format: {settings.log_format}")
    if profile in {"staging", "production"} and log_format != "json":
        return ConfigCheck("log_format", "warn", "json is recommended for centralized staging or production logs")
    return ConfigCheck("log_format", "pass", f"configured as {log_format}")


def _is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite:")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate NK HistoryGuide runtime environment variables without connecting to the database "
            "or printing secret values."
        )
    )
    parser.add_argument("--profile", choices=("local", "staging", "production"), default="local")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    checks = validate_runtime_config(Settings.from_env(), profile=args.profile)

    print(f"Runtime config validation profile={args.profile}")
    for check in checks:
        marker = check.severity.upper()
        print(f"[{marker}] {check.name}: {check.detail}")

    fail_count = sum(1 for check in checks if check.severity == "fail")
    warn_count = sum(1 for check in checks if check.severity == "warn")
    print(f"Summary: fails={fail_count}, warnings={warn_count}. Secret values were not printed.")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
