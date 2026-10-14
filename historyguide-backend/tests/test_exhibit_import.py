import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.exhibit_import_service import (
    ExhibitImportError,
    import_exhibits_from_file,
    load_exhibit_seed_file,
    validate_exhibits_for_import,
)
from app.services.exhibit_service import create_exhibit, get_exhibit


def write_seed_file(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "exhibits.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def valid_payload() -> list[dict]:
    return [
        {
            "id": "import-exhibit-001",
            "name": "Import Fixture Exhibit",
            "description": "Non-historical test fixture.",
            "period": "fixture-period",
            "keywords": ["fixture"],
            "importance": 3,
            "people": [],
            "time_range": None,
            "themes": ["import"],
            "source_reference": "Test fixture only.",
        }
    ]


def test_load_exhibit_seed_file_validates_json_array(tmp_path: Path) -> None:
    path = write_seed_file(tmp_path, valid_payload())

    exhibits = load_exhibit_seed_file(path)

    assert len(exhibits) == 1
    assert exhibits[0].id == "import-exhibit-001"


def test_load_exhibit_seed_file_rejects_non_array(tmp_path: Path) -> None:
    path = write_seed_file(tmp_path, {"id": "not-array"})

    with pytest.raises(ExhibitImportError, match="JSON array"):
        load_exhibit_seed_file(path)


def test_load_exhibit_seed_file_rejects_duplicate_ids(tmp_path: Path) -> None:
    payload = valid_payload() + valid_payload()
    path = write_seed_file(tmp_path, payload)

    with pytest.raises(ExhibitImportError, match="Duplicate exhibit ids"):
        load_exhibit_seed_file(path)


def test_load_exhibit_seed_file_rejects_invalid_importance(tmp_path: Path) -> None:
    payload = valid_payload()
    payload[0]["importance"] = 9
    path = write_seed_file(tmp_path, payload)

    with pytest.raises(ExhibitImportError, match="invalid"):
        load_exhibit_seed_file(path)


def test_load_exhibit_seed_file_requires_source_reference(tmp_path: Path) -> None:
    payload = valid_payload()
    payload[0]["source_reference"] = " "
    path = write_seed_file(tmp_path, payload)

    with pytest.raises(ExhibitImportError, match="source_reference is required"):
        load_exhibit_seed_file(path)


def test_import_exhibits_from_file_writes_records(tmp_path: Path, db_session: Session) -> None:
    path = write_seed_file(tmp_path, valid_payload())

    imported_count = import_exhibits_from_file(db_session, path)

    assert imported_count == 1
    assert get_exhibit(db_session, "import-exhibit-001") is not None


def test_validate_exhibits_for_import_does_not_write_records(tmp_path: Path, db_session: Session) -> None:
    path = write_seed_file(tmp_path, valid_payload())

    exhibits = validate_exhibits_for_import(db_session, path)

    assert len(exhibits) == 1
    assert get_exhibit(db_session, "import-exhibit-001") is None


def test_import_exhibits_from_file_rejects_existing_ids(tmp_path: Path, db_session: Session) -> None:
    create_exhibit(db_session, ExhibitCreate.model_validate(valid_payload()[0]))
    path = write_seed_file(tmp_path, valid_payload())

    with pytest.raises(ExhibitImportError, match="already exist"):
        import_exhibits_from_file(db_session, path)


def test_validate_exhibits_for_import_rejects_existing_ids(tmp_path: Path, db_session: Session) -> None:
    create_exhibit(db_session, ExhibitCreate.model_validate(valid_payload()[0]))
    path = write_seed_file(tmp_path, valid_payload())

    with pytest.raises(ExhibitImportError, match="already exist"):
        validate_exhibits_for_import(db_session, path)
