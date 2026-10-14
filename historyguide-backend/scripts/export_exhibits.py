import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services.exhibit_export_service import export_exhibits_to_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export NK HistoryGuide exhibit records to a JSON seed file."
    )
    parser.add_argument("path", type=Path, help="Destination path for the UTF-8 JSON seed file.")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        exported_count = export_exhibits_to_file(db, args.path)
    finally:
        db.close()

    print(f"Exported {exported_count} exhibit records to {args.path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
