from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings


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

Severity = Literal["pass", "warn", "fail"]


@dataclass(frozen=True)
class DatabaseValidationCheck:
    name: str
    severity: Severity
    detail: str


@dataclass(frozen=True)
class DatabaseValidationResult:
    expected_head: str
    checks: tuple[DatabaseValidationCheck, ...]

    @property
    def fail_count(self) -> int:
        return sum(1 for check in self.checks if check.severity == "fail")

    @property
    def warn_count(self) -> int:
        return sum(1 for check in self.checks if check.severity == "warn")


def validate_staging_database(
    database_url: str,
    *,
    require_exhibits: bool = False,
    require_sourced_exhibits: bool = False,
    require_audit_logs: bool = False,
    required_source_ids: tuple[str, ...] = (),
) -> DatabaseValidationResult:
    expected_head = _expected_alembic_head()
    checks: list[DatabaseValidationCheck] = []

    sqlite_path_error = _sqlite_file_error(database_url)
    if sqlite_path_error is not None:
        checks.append(DatabaseValidationCheck("database_connectivity", "fail", sqlite_path_error))
        return DatabaseValidationResult(expected_head=expected_head, checks=tuple(checks))

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
            checks.append(DatabaseValidationCheck("database_connectivity", "pass", "read-only connection succeeded"))

            table_names = frozenset(inspect(connection).get_table_names())
            checks.extend(_table_checks(table_names))

            if "alembic_version" in table_names:
                revision = connection.execute(text("select version_num from alembic_version")).scalar()
                checks.append(_migration_check(str(revision) if revision is not None else "", expected_head))
            else:
                checks.append(
                    DatabaseValidationCheck(
                        "migration_head",
                        "fail",
                        f"alembic_version table is missing; expected head is {expected_head}",
                    )
                )

            if "exhibits" in table_names:
                checks.extend(
                    _exhibit_data_checks(
                        connection,
                        require_exhibits=require_exhibits,
                        require_sourced_exhibits=require_sourced_exhibits,
                    )
                )
            if "visitor_states" in table_names:
                checks.append(_count_check(connection, "visitor_state_count", "visitor_states", warn_when_zero=False))
            if "visitor_visit_events" in table_names:
                checks.append(_count_check(connection, "visit_event_count", "visitor_visit_events", warn_when_zero=False))
            if "audit_logs" in table_names:
                checks.append(
                    _count_check(
                        connection,
                        "audit_log_count",
                        "audit_logs",
                        warn_when_zero=require_audit_logs,
                        fail_when_zero=require_audit_logs,
                    )
                )
            if required_source_ids:
                if "evidence_sources" in table_names:
                    checks.extend(_required_source_checks(connection, required_source_ids))
                else:
                    checks.append(DatabaseValidationCheck(
                        "required_sources", "fail", "evidence_sources table is missing"
                    ))
    except SQLAlchemyError as exc:
        checks.append(DatabaseValidationCheck("database_connectivity", "fail", f"database check failed: {exc}"))
    finally:
        engine.dispose()

    return DatabaseValidationResult(expected_head=expected_head, checks=tuple(checks))


def _expected_alembic_head() -> str:
    config = Config(str(ALEMBIC_CONFIG_PATH))
    return ScriptDirectory.from_config(config).get_current_head()


def _sqlite_file_error(database_url: str) -> str | None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return None
    database = url.database
    if not database or database == ":memory:":
        return None
    database_path = Path(database)
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    if not database_path.exists():
        return f"SQLite database file does not exist: {database_path}"
    return None


def _table_checks(table_names: frozenset[str]) -> list[DatabaseValidationCheck]:
    checks: list[DatabaseValidationCheck] = []
    for table_name in sorted(EXPECTED_TABLES):
        if table_name in table_names:
            checks.append(DatabaseValidationCheck(f"table_{table_name}", "pass", "present"))
        else:
            checks.append(DatabaseValidationCheck(f"table_{table_name}", "fail", "missing"))
    return checks


def _migration_check(revision: str, expected_head: str) -> DatabaseValidationCheck:
    if revision == expected_head:
        return DatabaseValidationCheck("migration_head", "pass", f"at expected Alembic head {expected_head}")
    return DatabaseValidationCheck("migration_head", "fail", f"at revision {revision or '<empty>'}; expected {expected_head}")


def _exhibit_data_checks(
    connection,
    *,
    require_exhibits: bool,
    require_sourced_exhibits: bool,
) -> list[DatabaseValidationCheck]:
    exhibit_count = int(connection.execute(text("select count(*) from exhibits")).scalar_one())
    unsourced_count = int(
        connection.execute(
            text(
                "select count(*) from exhibits "
                "where source_reference is null or trim(source_reference) = ''"
            )
        ).scalar_one()
    )

    exhibit_severity: Severity = "pass"
    if exhibit_count == 0:
        exhibit_severity = "fail" if require_exhibits else "warn"

    source_severity: Severity = "pass"
    if unsourced_count:
        source_severity = "fail" if require_sourced_exhibits else "warn"

    return [
        DatabaseValidationCheck("exhibit_count", exhibit_severity, f"{exhibit_count} exhibit records found"),
        DatabaseValidationCheck(
            "unsourced_exhibit_count",
            source_severity,
            f"{unsourced_count} exhibit records have empty source_reference",
        ),
    ]


def _count_check(
    connection,
    name: str,
    table_name: str,
    *,
    warn_when_zero: bool,
    fail_when_zero: bool = False,
) -> DatabaseValidationCheck:
    count = int(connection.execute(text(f"select count(*) from {table_name}")).scalar_one())
    if count == 0 and fail_when_zero:
        return DatabaseValidationCheck(name, "fail", f"0 records found in {table_name}")
    if count == 0 and warn_when_zero:
        return DatabaseValidationCheck(name, "warn", f"0 records found in {table_name}")
    return DatabaseValidationCheck(name, "pass", f"{count} records found in {table_name}")


def _required_source_checks(connection, source_ids: tuple[str, ...]) -> list[DatabaseValidationCheck]:
    checks: list[DatabaseValidationCheck] = []
    for source_id in source_ids:
        row = connection.execute(
            text(
                "select title, source_uri, content_text, content_sha256, status, "
                "reviewed_by, reviewed_at from evidence_sources where id = :source_id"
            ),
            {"source_id": source_id},
        ).mappings().first()
        if row is None:
            checks.append(DatabaseValidationCheck(
                f"source_{source_id}", "fail", "not present"
            ))
            continue
        hash_matches = hashlib.sha256(row["content_text"].encode("utf-8")).hexdigest() == row["content_sha256"]
        reviewed = bool(row["reviewed_by"] and row["reviewed_at"])
        provenance = bool(row["title"].strip() and row["source_uri"].strip())
        approved = row["status"] == "approved" and not source_id.startswith("fixture-")
        severity: Severity = "pass" if approved and hash_matches and reviewed and provenance else "fail"
        checks.append(DatabaseValidationCheck(
            f"source_{source_id}",
            severity,
            f"status={row['status']}, hash_matches={hash_matches}, "
            f"review_recorded={reviewed}, provenance_present={provenance}",
        ))
    return checks


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the configured NK HistoryGuide staging database with read-only checks. "
            "This script connects to the target database but does not run migrations, import records, "
            "write audit logs, validate historical accuracy, run RAG, or generate explanation content."
        )
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional database URL override. Defaults to HISTORYGUIDE_DATABASE_URL or app settings.",
    )
    parser.add_argument(
        "--require-exhibits",
        action="store_true",
        help="Fail when the target database has no exhibit records.",
    )
    parser.add_argument(
        "--require-sourced-exhibits",
        action="store_true",
        help="Fail when any exhibit record has an empty source_reference.",
    )
    parser.add_argument(
        "--require-audit-logs",
        action="store_true",
        help="Fail when the target database has no audit log records.",
    )
    parser.add_argument(
        "--require-source-id",
        action="append",
        default=[],
        metavar="ID",
        help="Require this backend evidence source ID to be approved and intact; repeat for each Coze citation ID.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if len(args.require_source_id) != len(set(args.require_source_id)) or any(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}", source_id) is None
        for source_id in args.require_source_id
    ):
        print("Required source IDs must be unique, nonempty identifiers of at most 64 safe characters.")
        return 2
    database_url = args.database_url or Settings.from_env().database_url
    result = validate_staging_database(
        database_url,
        require_exhibits=args.require_exhibits,
        require_sourced_exhibits=args.require_sourced_exhibits,
        require_audit_logs=args.require_audit_logs,
        required_source_ids=tuple(args.require_source_id),
    )

    print("Staging database validation")
    print(f"Expected Alembic head: {result.expected_head}")
    for check in result.checks:
        print(f"[{check.severity.upper()}] {check.name}: {check.detail}")
    print(
        f"Summary: fails={result.fail_count}, warnings={result.warn_count}. "
        "Read-only checks only; no migrations, imports, audit-log writes, RAG, or generated explanation content."
    )
    return 1 if result.fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
