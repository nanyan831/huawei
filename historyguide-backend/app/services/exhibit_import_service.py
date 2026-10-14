import json
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.audit_log_service import record_audit_log
from app.models.exhibit import Exhibit
from app.services.exhibit_service import get_exhibit


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
    import_exhibit_batch(
        db, exhibits, actor="import_cli", resource_id=path.name,
        details={"path": str(path)},
    )
    return len(exhibits)


def validate_exhibit_batch(db: Session, exhibits: list[ExhibitCreate]) -> None:
    _validate_unique_ids(exhibits)
    _validate_source_references(exhibits)
    _validate_no_existing_ids(db, exhibits)


def import_exhibit_batch(
    db: Session, exhibits: list[ExhibitCreate], *, actor: str = "operator",
    resource_id: str = "operator_batch", details: dict | None = None,
) -> list[Exhibit]:
    """Import unapproved exhibits and their audit evidence in one transaction."""
    validate_exhibit_batch(db, exhibits)
    records = [Exhibit(**exhibit.model_dump()) for exhibit in exhibits]
    try:
        db.add_all(records)
        record_audit_log(
            db, action="exhibits_imported", resource_type="exhibit_import",
            resource_id=resource_id, actor=actor,
            details={
                **(details or {}), "imported_count": len(exhibits),
                "exhibit_ids": [exhibit.id for exhibit in exhibits],
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ExhibitImportError("Exhibit ids changed during import; retry with new ids.") from exc
    except Exception:
        db.rollback()
        raise
    return records


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
