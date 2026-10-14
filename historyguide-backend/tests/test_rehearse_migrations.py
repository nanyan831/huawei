from pathlib import Path

from scripts import rehearse_migrations


def test_rehearse_migrations_applies_current_schema_to_isolated_database(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-rehearsal.db"

    result = rehearse_migrations.rehearse_migrations(database_path, keep_database=True)

    assert result.database_path == database_path
    assert result.database_kept is True
    assert database_path.exists()
    assert result.revision == "0005_history_review_runs"
    assert rehearse_migrations.EXPECTED_TABLES.issubset(result.tables)


def test_rehearse_migrations_main_reports_no_configured_database_changes(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "migration-main.db"

    exit_code = rehearse_migrations.main(["--database-path", str(database_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Migration rehearsal passed" in output
    assert "revision=0005_history_review_runs" in output
    assert "No configured application database changes were made" in output
    assert not database_path.exists()
