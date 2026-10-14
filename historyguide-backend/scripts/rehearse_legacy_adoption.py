from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"


@dataclass(frozen=True)
class LegacyAdoptionResult:
    matched_revision: str
    final_revision: str
    preserved_tables: int
    preserved_rows: int


def rehearse_legacy_adoption(source_path: Path) -> LegacyAdoptionResult:
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise ValueError("Source SQLite database file does not exist.")

    temporary_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="historyguide-adoption-") as directory:
        directory_path = Path(directory).resolve()
        if not directory_path.is_relative_to(temporary_root):
            raise RuntimeError("Temporary rehearsal path escaped its intended directory.")
        clone_path = directory_path / "source-copy.db"
        reference_path = directory_path / "reference.db"
        _backup_read_only(source_path, clone_path)
        _assert_integrity(clone_path)

        source_signature = _schema_signature(clone_path)
        if "alembic_version" in _table_names(clone_path):
            raise ValueError("Source already has Alembic history; use the normal migration rehearsal.")
        if not source_signature:
            raise ValueError("Source database has no application tables to adopt.")
        original_digests = _table_digests(clone_path)

        config = _config(reference_path)
        script = ScriptDirectory.from_config(config)
        revisions = list(reversed([revision.revision for revision in script.walk_revisions()]))
        matching_revisions: list[str] = []
        for revision in revisions:
            command.upgrade(config, revision)
            if _schema_signature(reference_path) == source_signature:
                matching_revisions.append(revision)
        if len(matching_revisions) != 1:
            raise ValueError(
                "Unversioned source schema does not match exactly one migration revision; "
                "no adoption was attempted."
            )

        matched_revision = matching_revisions[0]
        clone_config = _config(clone_path)
        command.stamp(clone_config, matched_revision)
        command.upgrade(clone_config, "head")
        _assert_integrity(clone_path)
        if _schema_signature(clone_path) != _schema_signature(reference_path):
            raise RuntimeError("Adopted clone schema differs from the migration head.")
        adopted_digests = _table_digests(clone_path)
        if any(adopted_digests.get(name) != digest for name, digest in original_digests.items()):
            raise RuntimeError("Existing table data changed during adoption rehearsal.")
        final_revision = _revision(clone_path)
        expected_head = script.get_current_head()
        if final_revision != expected_head:
            raise RuntimeError("Adoption rehearsal did not reach the migration head.")
        return LegacyAdoptionResult(
            matched_revision=matched_revision,
            final_revision=final_revision,
            preserved_tables=len(original_digests),
            preserved_rows=sum(count for count, _ in original_digests.values()),
        )


def _backup_read_only(source_path: Path, clone_path: Path) -> None:
    with closing(sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(clone_path)) as target:
            source.backup(target)


def _config(database_path: Path) -> Config:
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return config


def _table_names(database_path: Path) -> set[str]:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def _schema_signature(database_path: Path) -> tuple:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            signatures = []
            for table_name in sorted(set(inspector.get_table_names()) - {"alembic_version"}):
                columns = tuple(
                    (column["name"], str(column["type"]), column["nullable"],
                     column.get("primary_key", 0), column.get("default"))
                    for column in inspector.get_columns(table_name)
                )
                indexes = tuple(sorted(
                    (index["name"], tuple(index["column_names"]), index["unique"])
                    for index in inspector.get_indexes(table_name)
                ))
                foreign_keys = tuple(sorted(
                    (tuple(key["constrained_columns"]), key["referred_table"],
                     tuple(key["referred_columns"]),
                     key.get("options", {}).get("ondelete"),
                     key.get("options", {}).get("onupdate"))
                    for key in inspector.get_foreign_keys(table_name)
                ))
                unique_constraints = tuple(sorted(
                    tuple(constraint["column_names"])
                    for constraint in inspector.get_unique_constraints(table_name)
                ))
                check_constraints = tuple(sorted(
                    constraint["sqltext"]
                    for constraint in inspector.get_check_constraints(table_name)
                ))
                signatures.append((
                    table_name, columns, indexes, foreign_keys,
                    unique_constraints, check_constraints,
                ))
            return tuple(signatures)
    finally:
        engine.dispose()


def _table_digests(database_path: Path) -> dict[str, tuple[int, str]]:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.connect() as connection:
            digests = {}
            for table_name in sorted(set(inspect(connection).get_table_names()) - {"alembic_version"}):
                table = Table(table_name, MetaData(), autoload_with=connection)
                primary_key = tuple(table.primary_key.columns)
                if not primary_key:
                    raise ValueError(f"Table {table_name} has no primary key for data comparison.")
                digest = hashlib.sha256()
                row_count = 0
                for row in connection.execute(select(table).order_by(*primary_key)):
                    encoded = json.dumps(
                        tuple(row._mapping[column] for column in table.columns),
                        ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"),
                    ).encode("utf-8")
                    digest.update(len(encoded).to_bytes(8, "big"))
                    digest.update(encoded)
                    row_count += 1
                digests[table_name] = (row_count, digest.hexdigest())
            return digests
    finally:
        engine.dispose()


def _revision(database_path: Path) -> str:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        with engine.connect() as connection:
            return connection.execute(text("select version_num from alembic_version")).scalar_one()
    finally:
        engine.dispose()


def _assert_integrity(database_path: Path) -> None:
    with closing(sqlite3.connect(database_path)) as connection:
        if connection.execute("pragma quick_check").fetchone() != ("ok",):
            raise ValueError("SQLite clone failed integrity check.")
        if connection.execute("pragma foreign_key_check").fetchone() is not None:
            raise ValueError("SQLite clone has foreign-key violations.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rehearse Alembic adoption on a temporary SQLite backup; never stamp the source database."
    )
    parser.add_argument("source_database", type=Path)
    args = parser.parse_args(argv)
    result = rehearse_legacy_adoption(args.source_database)
    print(
        "Legacy adoption rehearsal passed: "
        f"matched={result.matched_revision}, head={result.final_revision}, "
        f"preserved_tables={result.preserved_tables}, preserved_rows={result.preserved_rows}. "
        "Source database was opened read-only and never stamped or migrated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
