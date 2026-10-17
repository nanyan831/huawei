import hashlib
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.database.base import Base
from scripts import rehearse_legacy_adoption


def _head_schema_without_version(database_path: Path) -> None:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(
            "insert into exhibits "
            "(id, name, description, period, keywords, importance, people, themes, source_reference) "
            "values ('test-exhibit', 'Test', 'Description', 'period', '[]', 1, '[]', '[]', 'record')"
        ))
    engine.dispose()


def test_adoption_rehearsal_matches_head_and_preserves_source(tmp_path: Path) -> None:
    source_path = tmp_path / "unversioned-head.db"
    _head_schema_without_version(source_path)
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()

    result = rehearse_legacy_adoption.rehearse_legacy_adoption(source_path)

    assert result.matched_revision == "0008_claim_support_reviews"
    assert result.final_revision == "0008_claim_support_reviews"
    assert result.preserved_tables == 11
    assert result.preserved_rows == 1
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before
    with sqlite3.connect(source_path) as connection:
        assert connection.execute(
            "select name from sqlite_master where name = 'alembic_version'"
        ).fetchone() is None


def test_adoption_rehearsal_upgrades_older_unversioned_copy(tmp_path: Path) -> None:
    source_path = tmp_path / "unversioned-0002.db"
    config = Config(str(rehearse_legacy_adoption.ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{source_path.as_posix()}")
    command.upgrade(config, "0002_audit_logs")
    with sqlite3.connect(source_path) as connection:
        connection.execute("drop table alembic_version")
        connection.execute(
            "insert into exhibits "
            "(id, name, description, period, keywords, importance, people, themes, source_reference) "
            "values ('old-exhibit', 'Old', 'Description', 'period', '[]', 1, '[]', '[]', 'record')"
        )
        connection.commit()
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()

    result = rehearse_legacy_adoption.rehearse_legacy_adoption(source_path)

    assert result.matched_revision == "0002_audit_logs"
    assert result.final_revision == "0008_claim_support_reviews"
    assert result.preserved_tables == 4
    assert result.preserved_rows == 1
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before


def test_adoption_rehearsal_rejects_schema_drift_without_touching_source(tmp_path: Path) -> None:
    source_path = tmp_path / "drifted.db"
    _head_schema_without_version(source_path)
    with sqlite3.connect(source_path) as connection:
        connection.execute("create table unexpected (id integer primary key)")
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="does not match exactly one"):
        rehearse_legacy_adoption.rehearse_legacy_adoption(source_path)

    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before


def test_adoption_rehearsal_rejects_foreign_key_violations(tmp_path: Path) -> None:
    source_path = tmp_path / "broken-links.db"
    _head_schema_without_version(source_path)
    with sqlite3.connect(source_path) as connection:
        connection.execute(
            "insert into exhibit_evidence_links (exhibit_id, source_id) "
            "values ('test-exhibit', 'missing-source')"
        )
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="foreign-key violations"):
        rehearse_legacy_adoption.rehearse_legacy_adoption(source_path)

    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before
