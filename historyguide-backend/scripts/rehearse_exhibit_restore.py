import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.base import Base
from app.models import audit_log as _audit_log  # noqa: F401
from app.models import exhibit as _exhibit  # noqa: F401
from app.models import visitor_state as _visitor_state  # noqa: F401
from app.services.exhibit_import_service import ExhibitImportError, import_exhibits_from_file
from app.services.exhibit_service import get_exhibit_quality_report, get_exhibit_source_report, list_exhibits


@dataclass(frozen=True)
class RestoreRehearsalResult:
    imported_count: int
    sourced_count: int
    unsourced_count: int
    quality_issue_count: int


def rehearse_exhibit_restore(path: Path, *, require_non_empty: bool = True) -> RestoreRehearsalResult:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        imported_count = import_exhibits_from_file(db, path)
        if require_non_empty and imported_count == 0:
            raise ExhibitImportError("Restore rehearsal imported zero exhibit records.")

        source_report = get_exhibit_source_report(db)
        quality_report = get_exhibit_quality_report(db)
        restored_count = len(list_exhibits(db))

        if restored_count != imported_count:
            raise ExhibitImportError(
                f"Restore rehearsal count mismatch: imported {imported_count}, restored {restored_count}."
            )

        if source_report.unsourced_count:
            raise ExhibitImportError(
                "Restore rehearsal found unsourced exhibit records: "
                + ", ".join(source_report.unsourced_exhibit_ids)
            )

        return RestoreRehearsalResult(
            imported_count=imported_count,
            sourced_count=source_report.sourced_count,
            unsourced_count=source_report.unsourced_count,
            quality_issue_count=sum(issue.count for issue in quality_report.issues),
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rehearse restoring an NK HistoryGuide exhibit backup into an isolated in-memory "
            "SQLite database. The configured application database is not used or modified."
        )
    )
    parser.add_argument("path", type=Path, help="Path to a UTF-8 exhibit backup JSON file.")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow a backup that restores zero exhibit records.",
    )
    args = parser.parse_args()

    try:
        result = rehearse_exhibit_restore(args.path, require_non_empty=not args.allow_empty)
    except ExhibitImportError as exc:
        print(f"Restore rehearsal failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Restore rehearsal passed: "
        f"imported={result.imported_count}, "
        f"sourced={result.sourced_count}, "
        f"unsourced={result.unsourced_count}, "
        f"quality_issue_count={result.quality_issue_count}. "
        "No configured database changes were made."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
