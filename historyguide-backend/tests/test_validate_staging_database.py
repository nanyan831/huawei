import hashlib
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.evidence_fingerprint import source_approval_fingerprint
from scripts import rehearse_migrations, validate_staging_database


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_validate_staging_database_passes_for_migrated_database(tmp_path: Path) -> None:
    database_path = tmp_path / "staging.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)

    result = validate_staging_database.validate_staging_database(_database_url(database_path))

    assert result.fail_count == 0
    assert result.expected_head == "0008_claim_support_reviews"
    check_names = {check.name for check in result.checks}
    assert "database_connectivity" in check_names
    assert "migration_head" in check_names
    assert "exhibit_count" in check_names


def test_validate_staging_database_can_require_exhibits(tmp_path: Path) -> None:
    database_path = tmp_path / "empty-staging.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)

    result = validate_staging_database.validate_staging_database(
        _database_url(database_path),
        require_exhibits=True,
    )

    assert result.fail_count == 1
    failed_names = {check.name for check in result.checks if check.severity == "fail"}
    assert failed_names == {"exhibit_count"}


def test_validate_staging_database_can_require_sourced_exhibits(tmp_path: Path) -> None:
    database_path = tmp_path / "unsourced-staging.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)
    engine = create_engine(_database_url(database_path))
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into exhibits "
                "(id, name, description, period, keywords, importance, people, time_range, themes, source_reference) "
                "values "
                "('fixture-unsourced', 'Unsourced Fixture', 'Non-historical fixture', "
                "'fixture', '[]', 1, '[]', null, '[]', '')"
            )
        )
    engine.dispose()

    result = validate_staging_database.validate_staging_database(
        _database_url(database_path),
        require_sourced_exhibits=True,
    )

    assert result.fail_count == 1
    failed_names = {check.name for check in result.checks if check.severity == "fail"}
    assert failed_names == {"unsourced_exhibit_count"}


def test_validate_staging_database_reports_missing_sqlite_without_creating_file(tmp_path: Path) -> None:
    database_path = tmp_path / "missing.db"

    result = validate_staging_database.validate_staging_database(_database_url(database_path))

    assert result.fail_count == 1
    assert result.checks[0].name == "database_connectivity"
    assert "does not exist" in result.checks[0].detail
    assert not database_path.exists()


def test_validate_staging_database_main_reports_read_only_boundary(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "main-staging.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)

    exit_code = validate_staging_database.main(["--database-url", _database_url(database_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Staging database validation" in output
    assert "Expected Alembic head: 0008_claim_support_reviews" in output
    assert "Read-only checks only" in output
    assert "no migrations, imports, audit-log writes, RAG, or generated explanation content" in output


def test_required_source_ids_reject_draft_missing_and_changed_text(tmp_path: Path) -> None:
    database_path = tmp_path / "source-staging.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)
    engine = create_engine(_database_url(database_path))
    original_text = "Museum-reviewed original excerpt."
    original_hash = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    with engine.begin() as connection:
        for source_id, status in (("S01", "approved"), ("S02", "draft")):
            connection.execute(
                text(
                    "insert into evidence_sources "
                    "(id, title, source_uri, content_text, content_sha256, approved_fingerprint, "
                    "status, reviewed_by, reviewed_at) "
                    "values (:id, :title, :uri, :content, :sha256, :fingerprint, "
                    ":status, :reviewer, :reviewed_at)"
                ),
                {
                    "id": source_id,
                    "title": "Museum record",
                    "uri": "museum-archive:record",
                    "content": original_text,
                    "sha256": original_hash,
                    "fingerprint": source_approval_fingerprint(
                        source_id, "Museum record", "museum-archive:record", original_hash
                    ) if status == "approved" else None,
                    "status": status,
                    "reviewer": "curator" if status == "approved" else None,
                    "reviewed_at": "2026-10-14 00:00:00" if status == "approved" else None,
                },
            )
    result = validate_staging_database.validate_staging_database(
        _database_url(database_path), required_source_ids=("S01", "S02", "S03")
    )
    source_checks = {check.name: check for check in result.checks if check.name.startswith("source_")}
    assert source_checks["source_S01"].severity == "pass"
    assert source_checks["source_S02"].severity == "fail"
    assert source_checks["source_S03"].severity == "fail"
    assert original_text not in " ".join(check.detail for check in source_checks.values())

    with engine.begin() as connection:
        connection.execute(text("update evidence_sources set content_text = 'tampered' where id = 'S01'"))
    result = validate_staging_database.validate_staging_database(
        _database_url(database_path), required_source_ids=("S01",)
    )
    changed = next(check for check in result.checks if check.name == "source_S01")
    assert changed.severity == "fail"
    assert "hash_matches=False" in changed.detail
    with engine.begin() as connection:
        connection.execute(text("update evidence_sources set content_text = :body where id = 'S01'"), {"body": original_text})
        connection.execute(text("update evidence_sources set source_uri = 'museum-archive:changed' where id = 'S01'"))
    metadata_result = validate_staging_database.validate_staging_database(
        _database_url(database_path), required_source_ids=("S01",)
    )
    metadata_check = next(check for check in metadata_result.checks if check.name == "source_S01")
    assert metadata_check.severity == "fail"
    assert "approval_fingerprint_matches=False" in metadata_check.detail
    engine.dispose()


def test_required_source_rejects_fixture_uri_and_empty_body(tmp_path: Path) -> None:
    database_path = tmp_path / "unsafe-source.db"
    rehearse_migrations.rehearse_migrations(database_path, keep_database=True)
    engine = create_engine(_database_url(database_path))
    with engine.begin() as connection:
        for source_id, uri, body in (
            ("S_FIXTURE", "fixture:old", "Synthetic text."),
            ("S_EMPTY", "museum:archive", "  "),
        ):
            connection.execute(
                text(
                    "insert into evidence_sources "
                    "(id, title, source_uri, content_text, content_sha256, status, reviewed_by, reviewed_at) "
                    "values (:id, 'Museum record', :uri, :body, :sha256, 'approved', 'curator', :reviewed_at)"
                ),
                {
                    "id": source_id, "uri": uri, "body": body,
                    "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "reviewed_at": "2026-10-14 00:00:00",
                },
            )
    result = validate_staging_database.validate_staging_database(
        _database_url(database_path), required_source_ids=("S_FIXTURE", "S_EMPTY")
    )
    source_checks = {check.name: check for check in result.checks if check.name.startswith("source_")}
    assert source_checks["source_S_FIXTURE"].severity == "fail"
    assert source_checks["source_S_EMPTY"].severity == "fail"
    engine.dispose()


def test_required_source_id_cli_rejects_duplicates_and_unsafe_text(capsys) -> None:
    assert validate_staging_database.main(["--require-source-id", "S01", "--require-source-id", "S01"]) == 2
    assert validate_staging_database.main(["--require-source-id", "S01\nLEAK"]) == 2
    assert "unique" in capsys.readouterr().out
