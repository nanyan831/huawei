import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services.exhibit_import_service import (
    ExhibitImportError,
    import_exhibits_from_file,
    validate_exhibits_for_import,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import verified NK HistoryGuide exhibit records from a JSON seed file."
    )
    parser.add_argument("path", type=Path, help="Path to a UTF-8 JSON file containing an exhibit array.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the seed file and database id conflicts without writing records.",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.dry_run:
            validated_exhibits = validate_exhibits_for_import(db, args.path)
            print(f"Validated {len(validated_exhibits)} exhibit records. No records were imported.")
            return 0

        imported_count = import_exhibits_from_file(db, args.path)
    except ExhibitImportError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Imported {imported_count} exhibit records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
