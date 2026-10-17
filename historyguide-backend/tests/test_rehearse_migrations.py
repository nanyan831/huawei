import hashlib
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource
from app.services.evidence_service import approve_source, source_publication_issue
from scripts import rehearse_migrations


def test_rehearse_migrations_applies_current_schema_to_isolated_database(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-rehearsal.db"

    result = rehearse_migrations.rehearse_migrations(database_path, keep_database=True)

    assert result.database_path == database_path
    assert result.database_kept is True
    assert database_path.exists()
    assert result.revision == "0008_claim_support_reviews"
    assert rehearse_migrations.EXPECTED_TABLES.issubset(result.tables)


def test_rehearse_migrations_main_reports_no_configured_database_changes(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "migration-main.db"

    exit_code = rehearse_migrations.main(["--database-path", str(database_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Migration rehearsal passed" in output
    assert "revision=0008_claim_support_reviews" in output
    assert "No configured application database changes were made" in output
    assert not database_path.exists()


def test_legacy_approved_source_stays_closed_after_fingerprint_migration(tmp_path: Path) -> None:
    database_path = tmp_path / "older-approved.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    config = Config(str(rehearse_migrations.ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "0006_visitor_access_grants")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "insert into evidence_sources "
                "(id, title, source_uri, content_text, content_sha256, status, reviewed_by, reviewed_at) "
                "values ('legacy-source', 'Old title', 'museum:old', 'Old text', "
                ":sha256, 'approved', 'old-reviewer', '2026-10-01 00:00:00')"
            ), {"sha256": hashlib.sha256(b"Old text").hexdigest()})
        command.upgrade(config, "head")
        with Session(engine) as db:
            source = db.get(EvidenceSource, "legacy-source")
            assert source.approved_fingerprint is None
            assert source_publication_issue(source) is not None
            assert source_publication_issue(source) == "source approval fingerprint is missing or source metadata changed"
            approve_source(db, source.id, reviewer="fresh-test-reviewer")
            assert source_publication_issue(source) is None
    finally:
        engine.dispose()
