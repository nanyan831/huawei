import pytest

from app.core.config import Settings


def test_settings_from_env_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("HISTORYGUIDE_APP_NAME", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_DATABASE_URL", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_SCHEMA_MODE", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_API_KEY", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_API_KEY_NEXT", raising=False)
    monkeypatch.delenv("HISTORYGUIDE_OPERATOR_API_KEY", raising=False)
    for name in (
        "HISTORYGUIDE_API_KEY_FILE",
        "HISTORYGUIDE_API_KEY_NEXT_FILE",
        "HISTORYGUIDE_OPERATOR_API_KEY_FILE",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.app_name == "NK HistoryGuide Backend"
    assert settings.database_url == "sqlite:///./historyguide.db"
    assert settings.schema_mode == "auto_create"
    assert settings.log_format == "text"
    assert settings.cors_origins == ()
    assert settings.api_key is None
    assert settings.api_key_next is None
    assert settings.operator_api_key is None


def test_settings_from_env_reads_overrides(monkeypatch) -> None:
    monkeypatch.setenv("HISTORYGUIDE_APP_NAME", "Custom HistoryGuide")
    monkeypatch.setenv("HISTORYGUIDE_DATABASE_URL", "sqlite:///./custom.db")
    monkeypatch.setenv("HISTORYGUIDE_SCHEMA_MODE", "migrated")
    monkeypatch.setenv("HISTORYGUIDE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("HISTORYGUIDE_LOG_FORMAT", "json")
    monkeypatch.setenv("HISTORYGUIDE_API_KEY", "secret-key")
    monkeypatch.setenv("HISTORYGUIDE_API_KEY_NEXT", "next-secret-key")
    monkeypatch.setenv("HISTORYGUIDE_OPERATOR_API_KEY", "operator-secret")
    monkeypatch.setenv(
        "HISTORYGUIDE_CORS_ORIGINS",
        "http://localhost:5173, https://historyguide.example",
    )

    settings = Settings.from_env()

    assert settings.app_name == "Custom HistoryGuide"
    assert settings.database_url == "sqlite:///./custom.db"
    assert settings.schema_mode == "migrated"
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.cors_origins == ("http://localhost:5173", "https://historyguide.example")
    assert settings.api_key == "secret-key"
    assert settings.api_key_next == "next-secret-key"
    assert settings.operator_api_key == "operator-secret"


def test_settings_from_env_reads_secret_files(monkeypatch, tmp_path) -> None:
    for name in (
        "HISTORYGUIDE_API_KEY",
        "HISTORYGUIDE_API_KEY_NEXT",
        "HISTORYGUIDE_OPERATOR_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
        path = tmp_path / name.lower()
        path.write_text(f"{name.lower()}-secret\n", encoding="utf-8")
        monkeypatch.setenv(f"{name}_FILE", str(path))

    settings = Settings.from_env()
    assert settings.api_key == "historyguide_api_key-secret"
    assert settings.api_key_next == "historyguide_api_key_next-secret"
    assert settings.operator_api_key == "historyguide_operator_api_key-secret"


def test_settings_rejects_ambiguous_or_bad_secret_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HISTORYGUIDE_API_KEY", "direct-secret")
    monkeypatch.setenv("HISTORYGUIDE_API_KEY_FILE", str(tmp_path / "key"))
    with pytest.raises(ValueError, match="not both"):
        Settings.from_env()

    monkeypatch.delenv("HISTORYGUIDE_API_KEY")
    monkeypatch.setenv("HISTORYGUIDE_API_KEY_FILE", "relative-key")
    with pytest.raises(ValueError, match="absolute path"):
        Settings.from_env()

    key_file = tmp_path / "key"
    key_file.write_text("first\nsecond\n", encoding="utf-8")
    monkeypatch.setenv("HISTORYGUIDE_API_KEY_FILE", str(key_file))
    with pytest.raises(ValueError, match="exactly one"):
        Settings.from_env()

    key_file.write_text("x" * 4097, encoding="utf-8")
    with pytest.raises(ValueError, match="too large"):
        Settings.from_env()

    key_file.unlink()
    with pytest.raises(ValueError, match="could not be read"):
        Settings.from_env()
