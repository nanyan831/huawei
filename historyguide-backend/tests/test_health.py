def test_health_check_returns_service_status(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "nk-historyguide-backend",
        "version": "0.1.0",
    }


def test_readiness_check_returns_database_status(client) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "nk-historyguide-backend",
        "version": "0.1.0",
        "database": "ok",
    }


def test_database_status_describes_backend_without_exposing_full_url(client) -> None:
    response = client.get("/api/system/database")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "nk-historyguide-backend"
    assert body["version"] == "0.1.0"
    assert body["backend"] == "sqlite"
    assert body["driver"] == "sqlite"
    assert body["persistence"] == "local_file"
    assert body["schema_management"] == "sqlalchemy_create_all_mvp_with_alembic_scaffold"
    assert body["migration_target"] == "alembic_staging_then_postgresql"
    assert "historyguide.db" not in str(body)
    assert "Alembic migration scaffolding" in body["production_note"]
