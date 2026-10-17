from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.evidence import EvidenceSource
from scripts import verify_postgres_claim_release_lock as probe
from scripts import rehearse_migrations


def test_rejects_non_postgresql_targets() -> None:
    error = probe.validate_target_url("sqlite:///staging.db")

    assert error is not None
    assert "PostgreSQL" in error


def test_rejects_invalid_or_incomplete_urls() -> None:
    assert probe.validate_target_url("not a url") is not None
    assert probe.validate_target_url("postgresql+psycopg://localhost") is not None


def test_main_requires_explicit_write_acknowledgement(capsys) -> None:
    exit_code = probe.main(["--database-url", "postgresql+psycopg://localhost/staging"])

    assert exit_code == 2
    assert "Refusing to write" in capsys.readouterr().out


def test_main_rejects_sqlite_even_with_acknowledgement(capsys) -> None:
    exit_code = probe.main(
        ["--database-url", "sqlite:///staging.db", probe.ACKNOWLEDGEMENT]
    )

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "Refusing to run" in output
    assert "PostgreSQL" in output


def test_cleanup_removes_source_when_candidate_creation_never_completed(tmp_path: Path) -> None:
    database_path = tmp_path / "partial-probe.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        db.add(
            EvidenceSource(
                id="staging-lock-partial",
                title="Partial probe",
                source_uri="urn:staging-lock-partial",
                content_text="Synthetic only",
                content_sha256="0" * 64,
                status="draft",
            )
        )
        db.commit()

    assert probe._cleanup_probe_records(
        session_factory, source_id="staging-lock-partial"
    ) is True
    with session_factory() as db:
        assert db.scalar(
            select(EvidenceSource.id).where(EvidenceSource.id == "staging-lock-partial")
        ) is None
    engine.dispose()
