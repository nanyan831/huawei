from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings
from app.main import API_KEY_HEADER, OPERATOR_API_KEY_HEADER


def test_api_key_auth_is_disabled_by_default() -> None:
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/api/genios/capabilities")

    assert response.status_code == 200


def test_api_key_auth_keeps_probe_paths_public(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="secret-key"))
    app = main_module.create_app()
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/api/system/database").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_security_status_reports_key_configuration_without_secret_values() -> None:
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/api/system/security-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["business_api_key_configured"] is False
    assert payload["operator_api_key_configured"] is False
    assert payload["visitor_gateway_enabled"] is False
    assert payload["business_apis_require_api_key"] is False
    assert payload["operator_apis_require_operator_key"] is False
    assert payload["business_api_key_header"] == API_KEY_HEADER
    assert payload["operator_api_key_header"] == OPERATOR_API_KEY_HEADER
    assert "/health" in payload["public_probe_paths"]
    assert "/api/system/security-status" in payload["operator_paths"]
    assert "/api/system/access-policy" in payload["operator_paths"]
    assert "/api/audit-logs" in payload["operator_path_prefixes"]


def test_access_policy_reports_coarse_boundaries_without_secret_values(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(api_key="business-secret", operator_api_key="operator-secret"),
    )
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get(
        "/api/system/access-policy",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )

    assert response.status_code == 200
    payload_text = response.text
    assert "business-secret" not in payload_text
    assert "operator-secret" not in payload_text
    payload = response.json()
    policies = {policy["name"]: policy for policy in payload["policies"]}
    assert policies["public_probe"]["access_level"] == "public"
    assert policies["business_api"]["required_header"] == API_KEY_HEADER
    assert policies["operator_api"]["required_header"] == OPERATOR_API_KEY_HEADER
    assert policies["visitor_gateway"]["access_level"] == "visitor_token"
    assert policies["visitor_gateway"]["paths"] == []
    assert "/api/system/access-policy" in policies["operator_api"]["paths"]
    assert "scripts/" in policies["local_operator_workflow"]["path_prefixes"]
    assert "full RBAC" in payload["production_note"]


def test_api_key_auth_rejects_protected_api_without_key(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="secret-key"))
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/api/genios/capabilities")

    assert response.status_code == 401
    assert response.json() == {"detail": "Valid HistoryGuide API key is required."}


def test_answer_release_requires_business_key(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="secret-key"))
    client = TestClient(main_module.create_app())
    assert client.get("/openapi-genios-answers.json").status_code == 200
    response = client.post("/api/genios/answers/history", json={})
    assert response.status_code == 401
    assert "secret-key" not in response.text


def test_api_key_auth_accepts_protected_api_with_key(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="secret-key"))
    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/api/genios/capabilities", headers={API_KEY_HEADER: "secret-key"})

    assert response.status_code == 200
    assert response.json()["service_id"] == "nk-historyguide-backend"


def test_staged_business_key_rotation_accepts_both_keys_then_revokes_old(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "settings",
        Settings(api_key="old-secret", api_key_next="new-secret", operator_api_key="operator-secret"),
    )
    client = TestClient(main_module.create_app())
    assert client.get("/api/genios/capabilities").status_code == 401
    assert client.get(
        "/api/genios/capabilities", headers={API_KEY_HEADER: "old-secret"}
    ).status_code == 200
    assert client.get(
        "/api/genios/capabilities", headers={API_KEY_HEADER: "new-secret"}
    ).status_code == 200
    status = client.get(
        "/api/system/security-status", headers={OPERATOR_API_KEY_HEADER: "operator-secret"}
    )
    assert status.json()["business_api_key_rotation_staged"] is True
    assert "old-secret" not in status.text
    assert "new-secret" not in status.text

    monkeypatch.setattr(
        main_module, "settings",
        Settings(api_key="new-secret", operator_api_key="operator-secret"),
    )
    cutover_client = TestClient(main_module.create_app())
    assert cutover_client.get(
        "/api/genios/capabilities", headers={API_KEY_HEADER: "old-secret"}
    ).status_code == 401
    assert cutover_client.get(
        "/api/genios/capabilities", headers={API_KEY_HEADER: "new-secret"}
    ).status_code == 200


def test_security_status_requires_business_key_when_only_business_key_is_configured(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(api_key="business-secret"))
    app = main_module.create_app()
    client = TestClient(app)

    assert client.get("/api/system/security-status").status_code == 401

    response = client.get(
        "/api/system/security-status",
        headers={API_KEY_HEADER: "business-secret"},
    )

    assert response.status_code == 200
    payload_text = response.text
    assert "business-secret" not in payload_text
    assert response.json()["business_api_key_configured"] is True


def test_operator_api_key_protects_operator_endpoints_without_business_api_key(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "settings", Settings(operator_api_key="operator-secret"))
    app = main_module.create_app()
    client = TestClient(app)

    assert client.get("/api/genios/capabilities").status_code == 200

    missing_key_response = client.get("/api/audit-logs")
    assert missing_key_response.status_code == 401
    assert missing_key_response.json() == {"detail": "Valid HistoryGuide operator API key is required."}

    response = client.get(
        "/api/audit-logs",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )
    assert response.status_code == 200


def test_security_status_requires_operator_key_when_operator_key_is_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(api_key="business-secret", operator_api_key="operator-secret"),
    )
    app = main_module.create_app()
    client = TestClient(app)

    business_key_response = client.get(
        "/api/system/security-status",
        headers={API_KEY_HEADER: "business-secret"},
    )
    assert business_key_response.status_code == 401

    operator_key_response = client.get(
        "/api/system/security-status",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )
    assert operator_key_response.status_code == 200
    payload_text = operator_key_response.text
    assert "business-secret" not in payload_text
    assert "operator-secret" not in payload_text
    assert operator_key_response.json()["operator_api_key_configured"] is True


def test_access_policy_requires_operator_key_when_operator_key_is_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(api_key="business-secret", operator_api_key="operator-secret"),
    )
    app = main_module.create_app()
    client = TestClient(app)

    business_key_response = client.get(
        "/api/system/access-policy",
        headers={API_KEY_HEADER: "business-secret"},
    )
    assert business_key_response.status_code == 401

    operator_key_response = client.get(
        "/api/system/access-policy",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )
    assert operator_key_response.status_code == 200


def test_operator_api_key_is_required_for_operator_endpoint_when_both_keys_are_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(api_key="business-secret", operator_api_key="operator-secret"),
    )
    app = main_module.create_app()
    client = TestClient(app)

    business_key_response = client.get(
        "/api/system/operational-alerts",
        headers={API_KEY_HEADER: "business-secret"},
    )
    assert business_key_response.status_code == 401
    assert business_key_response.json() == {"detail": "Valid HistoryGuide operator API key is required."}

    operator_key_response = client.get(
        "/api/system/operational-alerts",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )
    assert operator_key_response.status_code == 200


def test_operator_key_does_not_replace_business_api_key_for_business_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(api_key="business-secret", operator_api_key="operator-secret"),
    )
    app = main_module.create_app()
    client = TestClient(app)

    operator_key_response = client.get(
        "/api/genios/capabilities",
        headers={OPERATOR_API_KEY_HEADER: "operator-secret"},
    )
    assert operator_key_response.status_code == 401

    business_key_response = client.get(
        "/api/genios/capabilities",
        headers={API_KEY_HEADER: "business-secret"},
    )
    assert business_key_response.status_code == 200


def test_access_keys_are_scoped_to_each_application(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "settings",
        Settings(api_key="business-first", operator_api_key="operator-first"),
    )
    first_app = main_module.create_app()
    monkeypatch.setattr(
        main_module, "settings",
        Settings(api_key="business-second", operator_api_key="operator-second"),
    )
    second_app = main_module.create_app()
    with TestClient(first_app) as first, TestClient(second_app) as second:
        for client, own, other in ((first, "first", "second"), (second, "second", "first")):
            assert client.get(
                "/api/genios/capabilities", headers={API_KEY_HEADER: f"business-{own}"},
            ).status_code == 200
            assert client.get(
                "/api/genios/capabilities", headers={API_KEY_HEADER: f"business-{other}"},
            ).status_code == 401
            assert client.get(
                "/api/audit-logs", headers={OPERATOR_API_KEY_HEADER: f"operator-{own}"},
            ).status_code == 200
            assert client.get(
                "/api/audit-logs", headers={OPERATOR_API_KEY_HEADER: f"operator-{other}"},
            ).status_code == 401
