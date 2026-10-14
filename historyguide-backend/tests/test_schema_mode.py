from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from app.database.base import Base
from app.database.init_db import init_db
from scripts.rehearse_migrations import rehearse_migrations


def _engine(path: Path):
    return create_engine(f"sqlite:///{path.as_posix()}")


def test_migrated_mode_accepts_current_alembic_schema(tmp_path: Path) -> None:
    path = tmp_path / "migrated.db"
    rehearse_migrations(path, keep_database=True)
    engine = _engine(path)
    try:
        init_db(schema_mode="migrated", database_engine=engine)
    finally:
        engine.dispose()


def test_migrated_mode_rejects_unversioned_database_without_creating_tables(tmp_path: Path) -> None:
    path = tmp_path / "unversioned.db"
    engine = _engine(path)
    try:
        Base.metadata.create_all(engine)
        before = set(inspect(engine).get_table_names())
        with pytest.raises(RuntimeError, match="Alembic version table"):
            init_db(schema_mode="migrated", database_engine=engine)
        assert set(inspect(engine).get_table_names()) == before
    finally:
        engine.dispose()


def test_migrated_mode_rejects_schema_drift_without_repairing_it(tmp_path: Path) -> None:
    path = tmp_path / "drifted.db"
    rehearse_migrations(path, keep_database=True)
    engine = _engine(path)
    try:
        with engine.begin() as connection:
            connection.execute(text("drop table history_review_runs"))
        with pytest.raises(RuntimeError, match="schema differs"):
            init_db(schema_mode="migrated", database_engine=engine)
        assert "history_review_runs" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_auto_create_remains_available_for_local_demo(tmp_path: Path) -> None:
    path = tmp_path / "local-demo.db"
    engine = _engine(path)
    try:
        init_db(schema_mode="auto_create", database_engine=engine)
        assert "exhibits" in inspect(engine).get_table_names()
        assert "alembic_version" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
