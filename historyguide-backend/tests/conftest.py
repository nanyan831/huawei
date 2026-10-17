from collections.abc import Generator
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Application imports initialize the configured engine and may read secret files.
# Isolate them before importing app, including tests that create their own app.
_external_settings = {
    name: value for name, value in os.environ.items() if name.startswith("HISTORYGUIDE_")
}
for _name in _external_settings:
    os.environ.pop(_name)
_database_directory = TemporaryDirectory(prefix="historyguide-pytest-")
_database_path = Path(_database_directory.name) / "application.db"
os.environ["HISTORYGUIDE_DATABASE_URL"] = f"sqlite:///{_database_path.as_posix()}"
os.environ["HISTORYGUIDE_SCHEMA_MODE"] = "auto_create"

from app.database.base import Base
from app.database.session import engine as application_engine, get_db
from app.main import app
from app.models import audit_log  # noqa: F401
from app.models import evidence  # noqa: F401
from app.models import history_review_run  # noqa: F401
from app.models import exhibit  # noqa: F401
from app.models import review_run  # noqa: F401
from app.models import visitor_state  # noqa: F401
from app.models import visitor_access_grant  # noqa: F401


def pytest_unconfigure(config) -> None:
    application_engine.dispose()
    _database_directory.cleanup()
    for name in tuple(os.environ):
        if name.startswith("HISTORYGUIDE_"):
            os.environ.pop(name)
    os.environ.update(_external_settings)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        from fastapi.testclient import TestClient

        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
