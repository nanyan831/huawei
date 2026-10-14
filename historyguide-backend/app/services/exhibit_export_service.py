import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitRead
from app.services.exhibit_service import list_exhibits


def export_exhibits_to_file(db: Session, path: Path) -> int:
    exhibits = list_exhibits(db)
    payload = [
        ExhibitRead.model_validate(exhibit).model_dump(mode="json")
        for exhibit in exhibits
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(payload)
