from fastapi.testclient import TestClient

from app.core.config import Settings
from app import main as main_module


def test_create_app_adds_cors_for_configured_origin(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        Settings(cors_origins=("http://localhost:5173",)),
    )

    app = main_module.create_app()
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
