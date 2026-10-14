from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"
EXPECTED_TABLES = frozenset(
    {
        "alembic_version",
        "audit_logs",
        "evidence_sources",
        "exhibit_evidence_links",
        "exhibit_approvals",
        "review_runs",
        "history_review_runs",
        "exhibits",
        "visitor_states",
        "visitor_visit_events",
    }
)


@dataclass(frozen=True)
class MigrationRehearsalResult:
    database_path: Path
    database_kept: bool
    revision: str
    tables: tuple[str, ...]


def rehearse_migrations(
    database_path: Path | None = None,
    *,
    keep_database: bool = False,
) -> MigrationRehearsalResult:
    if database_path is None:
        handle = tempfile.NamedTemporaryFile(prefix="historyguide-migration-", suffix=".db", delete=False)
        handle.close()
        rehearsal_path = Path(handle.name)
    else:
        rehearsal_path = database_path

    rehearsal_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = _sqlite_database_url(rehearsal_path)
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", database_url)
    expected_head = ScriptDirectory.from_config(config).get_current_head()

    original_database_url = os.environ.get("HISTORYGUIDE_DATABASE_URL")
    os.environ["HISTORYGUIDE_DATABASE_URL"] = database_url

    engine = None
    try:
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            tables = tuple(sorted(inspect(connection).get_table_names()))
            revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
    finally:
        if engine is not None:
            engine.dispose()
        _restore_database_url(original_database_url)

    missing_tables = EXPECTED_TABLES.difference(tables)
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        _remove_unless_kept(rehearsal_path, keep_database)
        raise RuntimeError(f"Migration rehearsal missing expected tables: {missing}")

    if revision != expected_head:
        _remove_unless_kept(rehearsal_path, keep_database)
        raise RuntimeError(f"Migration rehearsal ended at revision {revision}, expected {expected_head}")

    result = MigrationRehearsalResult(
        database_path=rehearsal_path,
        database_kept=keep_database,
        revision=revision,
        tables=tables,
    )
    _remove_unless_kept(rehearsal_path, keep_database)
    return result


def _sqlite_database_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _restore_database_url(original_database_url: str | None) -> None:
    if original_database_url is None:
        os.environ.pop("HISTORYGUIDE_DATABASE_URL", None)
    else:
        os.environ["HISTORYGUIDE_DATABASE_URL"] = original_database_url


def _remove_unless_kept(path: Path, keep_database: bool) -> None:
    if keep_database:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        return


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Alembic migrations against an isolated SQLite database and verify the current "
            "NK HistoryGuide schema. The rehearsal does not use or modify the configured app database."
        )
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=None,
        help="Optional isolated SQLite file to use for the rehearsal.",
    )
    parser.add_argument(
        "--keep-database",
        action="store_true",
        help="Keep the rehearsal SQLite file after the check for manual inspection.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = rehearse_migrations(args.database_path, keep_database=args.keep_database)
    database_note = str(result.database_path) if result.database_kept else "temporary database removed"
    print(
        "Migration rehearsal passed: "
        f"revision={result.revision}, "
        f"tables={len(result.tables)}, "
        f"database={database_note}. "
        "No configured application database changes were made."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
