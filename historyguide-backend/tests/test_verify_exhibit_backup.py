import json
from pathlib import Path

import pytest

from app.services.exhibit_import_service import ExhibitImportError
from scripts.verify_exhibit_backup import verify_exhibit_backup_file


def write_backup_file(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "exhibit-backup.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def valid_backup_payload() -> list[dict]:
    return [
        {
            "id": "backup-exhibit-001",
            "name": "Backup Fixture Exhibit",
            "description": "Non-historical backup fixture.",
            "period": "fixture-period",
            "keywords": ["fixture", "backup"],
            "importance": 3,
            "people": [],
            "time_range": None,
            "themes": ["backup"],
            "source_reference": "Test fixture only.",
        }
    ]


def test_verify_exhibit_backup_file_accepts_valid_backup(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, valid_backup_payload())

    exhibit_count = verify_exhibit_backup_file(path)

    assert exhibit_count == 1


def test_verify_exhibit_backup_file_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, valid_backup_payload() + valid_backup_payload())

    with pytest.raises(ExhibitImportError, match="Duplicate exhibit ids"):
        verify_exhibit_backup_file(path)


def test_verify_exhibit_backup_file_requires_source_reference(tmp_path: Path) -> None:
    payload = valid_backup_payload()
    payload[0]["source_reference"] = ""
    path = write_backup_file(tmp_path, payload)

    with pytest.raises(ExhibitImportError, match="source_reference is required"):
        verify_exhibit_backup_file(path)


def test_verify_exhibit_backup_file_can_require_non_empty_backup(tmp_path: Path) -> None:
    path = write_backup_file(tmp_path, [])

    with pytest.raises(ExhibitImportError, match="empty"):
        verify_exhibit_backup_file(path, require_non_empty=True)
