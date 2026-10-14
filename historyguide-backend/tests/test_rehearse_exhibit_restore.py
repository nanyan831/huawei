import json
from pathlib import Path

import pytest

from app.services.exhibit_import_service import ExhibitImportError
from scripts.rehearse_exhibit_restore import rehearse_exhibit_restore


def write_backup_file(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "restore-backup.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def valid_backup_payload() -> list[dict]:
    return [
        {
            "id": "restore-exhibit-001",
            "name": "Restore Fixture Exhibit",
            "description": "Non-historical restore fixture.",
            "period": "fixture-period",
            "keywords": ["fixture", "restore"],
            "importance": 3,
            "people": [],
            "time_range": None,
            "themes": ["restore"],
            "source_reference": "Test fixture only.",
        }
    ]


def test_rehearse_exhibit_restore_imports_backup_into_isolated_database(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, valid_backup_payload())

    result = rehearse_exhibit_restore(path)

    assert result.imported_count == 1
    assert result.sourced_count == 1
    assert result.unsourced_count == 0


def test_rehearse_exhibit_restore_rejects_empty_backup_by_default(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, [])

    with pytest.raises(ExhibitImportError, match="zero exhibit records"):
        rehearse_exhibit_restore(path)


def test_rehearse_exhibit_restore_can_allow_empty_backup(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, [])

    result = rehearse_exhibit_restore(path, require_non_empty=False)

    assert result.imported_count == 0
    assert result.sourced_count == 0


def test_rehearse_exhibit_restore_rejects_invalid_backup(tmp_path: Path) -> None:
    payload = valid_backup_payload()
    payload[0]["source_reference"] = ""
    path = write_backup_file(tmp_path, payload)

    with pytest.raises(ExhibitImportError, match="source_reference is required"):
        rehearse_exhibit_restore(path)
