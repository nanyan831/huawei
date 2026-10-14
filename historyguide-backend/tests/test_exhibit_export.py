import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.exhibit_export_service import export_exhibits_to_file
from app.services.exhibit_service import create_exhibit


def test_export_exhibits_to_file_writes_seed_json(tmp_path: Path, db_session: Session) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="export-exhibit-001",
            name="Export Fixture Exhibit",
            description="Non-historical export fixture.",
            period="fixture-period",
            keywords=["fixture", "export"],
            importance=3,
            people=["Fixture Person"],
            time_range="fixture-time",
            themes=["development"],
            source_reference="Test fixture only.",
        ),
    )

    export_path = tmp_path / "backup" / "exhibits.json"

    exported_count = export_exhibits_to_file(db_session, export_path)

    assert exported_count == 1
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload == [
        {
            "id": "export-exhibit-001",
            "name": "Export Fixture Exhibit",
            "description": "Non-historical export fixture.",
            "period": "fixture-period",
            "keywords": ["fixture", "export"],
            "importance": 3,
            "people": ["Fixture Person"],
            "time_range": "fixture-time",
            "themes": ["development"],
            "source_reference": "Test fixture only.",
        }
    ]


def test_export_exhibits_to_file_writes_empty_array(tmp_path: Path, db_session: Session) -> None:
    export_path = tmp_path / "empty.json"

    exported_count = export_exhibits_to_file(db_session, export_path)

    assert exported_count == 0
    assert json.loads(export_path.read_text(encoding="utf-8")) == []
