import json
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.audit_log_service import record_audit_log
from app.services.exhibit_service import create_exhibits, get_exhibit


class ExhibitImportError(ValueError):
    pass


def load_exhibit_seed_file(path: Path) -> list[ExhibitCreate]:
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExhibitImportError(f"Invalid JSON: {exc.msg}") from exc

    if not isinstance(raw_data, list):
        raise ExhibitImportError("Exhibit seed file must contain a JSON array.")

    exhibits: list[ExhibitCreate] = []
    for index, item in enumerate(raw_data):
        if not isinstance(item, dict):
            raise ExhibitImportError(f"Item {index} must be a JSON object.")
        try:
            exhibits.append(ExhibitCreate.model_validate(item))
        except ValidationError as exc:
            raise ExhibitImportError(f"Item {index} is invalid: {exc}") from exc

    _validate_unique_ids(exhibits)
    _validate_source_references(exhibits)
    return exhibits


def import_exhibits_from_file(db: Session, path: Path) -> int:
    exhibits = validate_exhibits_for_import(db, path)
    create_exhibits(db, exhibits)
    record_audit_log(
        db,
        action="exhibits_imported",
        resource_type="exhibit_import",
        resource_id=path.name,
        actor="import_cli",
        details={
            "path": str(path),
            "imported_count": len(exhibits),
            "exhibit_ids": [exhibit.id for exhibit in exhibits],
        },
        commit=True,
    )
    return len(exhibits)


def validate_exhibits_for_import(db: Session, path: Path) -> list[ExhibitCreate]:
    exhibits = load_exhibit_seed_file(path)
    _validate_no_existing_ids(db, exhibits)
    return exhibits


def _validate_unique_ids(exhibits: list[ExhibitCreate]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for exhibit in exhibits:
        if exhibit.id in seen:
            duplicates.append(exhibit.id)
        seen.add(exhibit.id)

    if duplicates:
        raise ExhibitImportError("Duplicate exhibit ids in seed file: " + ", ".join(sorted(set(duplicates))))


def _validate_no_existing_ids(db: Session, exhibits: list[ExhibitCreate]) -> None:
    existing_ids = [exhibit.id for exhibit in exhibits if get_exhibit(db, exhibit.id) is not None]
    if existing_ids:
        raise ExhibitImportError("Exhibit ids already exist in database: " + ", ".join(sorted(existing_ids)))


def _validate_source_references(exhibits: list[ExhibitCreate]) -> None:
    missing_ids = [
        exhibit.id for exhibit in exhibits if exhibit.source_reference is None or not exhibit.source_reference.strip()
    ]
    if missing_ids:
        raise ExhibitImportError(
            "Exhibit source_reference is required for imported records: " + ", ".join(sorted(missing_ids))
        )
