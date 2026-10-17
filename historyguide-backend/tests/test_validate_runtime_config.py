from app.core.config import Settings
from scripts import validate_runtime_config


def test_validate_runtime_config_reports_production_failures_without_secret_values(capsys) -> None:
    exit_code = validate_runtime_config.main(["--profile", "production"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] business_api_key" in output
    assert "[FAIL] operator_api_key" in output
    assert "[FAIL] database_url" in output
    assert "Secret values were not printed" in output


def test_validate_runtime_config_accepts_hardened_staging_settings(monkeypatch, capsys) -> None:
    monkeypatch.setenv("HISTORYGUIDE_API_KEY", "business-secret")
    monkeypatch.setenv("HISTORYGUIDE_OPERATOR_API_KEY", "operator-secret")
    monkeypatch.setenv("HISTORYGUIDE_CORS_ORIGINS", "https://historyguide.example")
    monkeypatch.setenv("HISTORYGUIDE_DATABASE_URL", "postgresql://example.invalid/historyguide")
    monkeypatch.setenv("HISTORYGUIDE_SCHEMA_MODE", "migrated")
    monkeypatch.setenv("HISTORYGUIDE_LOG_FORMAT", "json")
    monkeypatch.setenv("HISTORYGUIDE_CLAIM_SUPPORT_REQUIRED", "true")

    exit_code = validate_runtime_config.main(["--profile", "staging"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[FAIL]" not in output
    assert "business-secret" not in output
    assert "operator-secret" not in output
    assert "Secret values were not printed" in output


def test_validate_runtime_config_fails_when_operator_key_reuses_business_key() -> None:
    settings = Settings(api_key="same-secret", operator_api_key="same-secret")

    checks = validate_runtime_config.validate_runtime_config(settings, profile="staging")

    assert any(
        check.name == "operator_key_separation" and check.severity == "fail"
        for check in checks
    )


def test_validate_runtime_config_rejects_wildcard_cors() -> None:
    settings = Settings(cors_origins=("*",))

    checks = validate_runtime_config.validate_runtime_config(settings, profile="local")

    assert any(check.name == "cors_origins" and check.severity == "fail" for check in checks)


def test_validate_runtime_config_checks_rotation_keys_without_printing_values() -> None:
    settings = Settings(
        api_key="old-secret", api_key_next="old-secret", operator_api_key="operator-secret"
    )
    checks = validate_runtime_config.validate_runtime_config(settings, profile="staging")
    assert any(
        check.name == "business_key_rotation" and check.severity == "fail"
        for check in checks
    )
    assert "old-secret" not in str(checks)

    settings = Settings(
        api_key="old-secret", api_key_next="new-secret", operator_api_key="new-secret"
    )
    checks = validate_runtime_config.validate_runtime_config(settings, profile="staging")
    assert any(
        check.name == "operator_key_separation" and check.severity == "fail"
        for check in checks
    )


def test_shared_runtime_requires_migrated_schema_mode() -> None:
    checks = validate_runtime_config.validate_runtime_config(
        Settings(schema_mode="auto_create"), profile="staging"
    )
    assert any(check.name == "schema_mode" and check.severity == "fail" for check in checks)


def test_visitor_gateway_config_requires_separate_key_and_valid_ttl() -> None:
    for settings in (
        Settings(visitor_gateway_enabled=True, api_key="business"),
        Settings(visitor_gateway_enabled=True, api_key="business", visitor_signing_key="business"),
        Settings(visitor_gateway_enabled=True, api_key="business", visitor_signing_key="too-short"),
        Settings(
            visitor_gateway_enabled=True, api_key="business", visitor_signing_key="visitor",
            visitor_token_ttl_minutes=999,
        ),
    ):
        checks = validate_runtime_config.validate_runtime_config(settings, profile="staging")
        assert any(check.name == "visitor_gateway" and check.severity == "fail" for check in checks)

    checks = validate_runtime_config.validate_runtime_config(
        Settings(
            visitor_gateway_enabled=True, api_key="business",
            visitor_signing_key="separate-visitor-signing-key-0123456789",
        ),
        profile="staging",
    )
    assert any(check.name == "visitor_gateway" and check.severity == "warn" for check in checks)
