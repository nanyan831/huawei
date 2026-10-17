import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "NK HistoryGuide Backend"
    app_version: str = "0.1.0"
    service_id: str = "nk-historyguide-backend"
    log_level: str = "INFO"
    log_format: str = "text"
    database_url: str = "sqlite:///./historyguide.db"
    schema_mode: str = "auto_create"
    cors_origins: tuple[str, ...] = ()
    api_key: str | None = None
    api_key_next: str | None = None
    operator_api_key: str | None = None
    visitor_gateway_enabled: bool = False
    visitor_signing_key: str | None = None
    visitor_token_ttl_minutes: int = 120
    claim_support_required: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("HISTORYGUIDE_APP_NAME", cls.app_name),
            app_version=os.getenv("HISTORYGUIDE_APP_VERSION", cls.app_version),
            service_id=os.getenv("HISTORYGUIDE_SERVICE_ID", cls.service_id),
            log_level=os.getenv("HISTORYGUIDE_LOG_LEVEL", cls.log_level),
            log_format=os.getenv("HISTORYGUIDE_LOG_FORMAT", cls.log_format),
            database_url=os.getenv("HISTORYGUIDE_DATABASE_URL", cls.database_url),
            schema_mode=os.getenv("HISTORYGUIDE_SCHEMA_MODE", cls.schema_mode),
            cors_origins=parse_csv_env("HISTORYGUIDE_CORS_ORIGINS"),
            api_key=read_optional_secret("HISTORYGUIDE_API_KEY"),
            api_key_next=read_optional_secret("HISTORYGUIDE_API_KEY_NEXT"),
            operator_api_key=read_optional_secret("HISTORYGUIDE_OPERATOR_API_KEY"),
            visitor_gateway_enabled=read_bool_env("HISTORYGUIDE_VISITOR_GATEWAY_ENABLED"),
            visitor_signing_key=read_optional_secret("HISTORYGUIDE_VISITOR_SIGNING_KEY"),
            visitor_token_ttl_minutes=int(os.getenv("HISTORYGUIDE_VISITOR_TOKEN_TTL_MINUTES", "120")),
            claim_support_required=read_bool_env("HISTORYGUIDE_CLAIM_SUPPORT_REQUIRED"),
        )


def parse_csv_env(name: str) -> tuple[str, ...]:
    raw_value = os.getenv(name, "")
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def read_bool_env(name: str) -> bool:
    value = os.getenv(name, "false").strip().lower()
    if value not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true or false.")
    return value in {"true", "1"}


def read_optional_secret(name: str) -> str | None:
    direct = (os.getenv(name) or "").strip()
    file_path = (os.getenv(f"{name}_FILE") or "").strip()
    if direct and file_path:
        raise ValueError(f"Set either {name} or {name}_FILE, not both.")
    if not file_path:
        return direct or None
    path = Path(file_path)
    if not path.is_absolute():
        raise ValueError(f"{name}_FILE must be an absolute path.")
    try:
        if path.stat().st_size > 4096:
            raise ValueError(f"{name}_FILE is too large for a single secret.")
        secret = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{name}_FILE could not be read.") from exc
    if not secret or "\n" in secret or "\r" in secret:
        raise ValueError(f"{name}_FILE must contain exactly one nonempty secret.")
    return secret


settings = Settings.from_env()
