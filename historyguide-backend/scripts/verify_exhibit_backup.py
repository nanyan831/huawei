import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.exhibit_import_service import ExhibitImportError, load_exhibit_seed_file


def verify_exhibit_backup_file(path: Path, *, require_non_empty: bool = False) -> int:
    exhibits = load_exhibit_seed_file(path)
    if require_non_empty and not exhibits:
        raise ExhibitImportError("Backup file is empty.")
    return len(exhibits)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify an NK HistoryGuide exhibit backup JSON file without connecting to the database. "
            "This checks structure, duplicate ids, field validation, and source_reference presence."
        )
    )
    parser.add_argument("path", type=Path, help="Path to a UTF-8 exhibit backup JSON file.")
    parser.add_argument(
        "--require-non-empty",
        action="store_true",
        help="Fail if the backup file contains no exhibit records.",
    )
    args = parser.parse_args()

    try:
        exhibit_count = verify_exhibit_backup_file(args.path, require_non_empty=args.require_non_empty)
    except ExhibitImportError as exc:
        print(f"Backup verification failed: {exc}", file=sys.stderr)
        return 1

    print(f"Verified {exhibit_count} exhibit records in backup file. No database changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
