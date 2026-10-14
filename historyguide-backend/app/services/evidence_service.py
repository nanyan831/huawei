import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource, ExhibitApproval, ExhibitEvidenceLink
from app.models.exhibit import Exhibit
from app.schemas.evidence import EvidenceSourceCreate, EvidenceSourcePreview
from app.services.audit_log_service import record_audit_log


def create_source(
    db: Session, *, source_id: str, title: str, source_uri: str, content_text: str
) -> EvidenceSource:
    if db.get(EvidenceSource, source_id) is not None:
        raise ValueError(f"Evidence source '{source_id}' already exists.")
    source = EvidenceSource(
        id=source_id,
        title=title,
        source_uri=source_uri,
        content_text=content_text,
        content_sha256=hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
        status="draft",
    )
    try:
        db.add(source)
        record_audit_log(
            db, action="evidence_source_created", resource_type="evidence_source",
            resource_id=source_id, actor="operator", details={"content_sha256": source.content_sha256},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(source)
    return source


def create_sources_batch(
    db: Session, sources: list[EvidenceSourceCreate]
) -> list[EvidenceSource]:
    validate_sources_batch(db, sources)
    created: list[EvidenceSource] = []
    try:
        for item in sources:
            source = EvidenceSource(
                id=item.id,
                title=item.title,
                source_uri=item.source_uri,
                content_text=item.content_text,
                content_sha256=hashlib.sha256(item.content_text.encode("utf-8")).hexdigest(),
                status="draft",
            )
            created.append(source)
            db.add(source)
            record_audit_log(
                db,
                action="evidence_source_created",
                resource_type="evidence_source",
                resource_id=item.id,
                actor="operator",
                details={"content_sha256": source.content_sha256, "import_mode": "batch_draft"},
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Evidence source ids changed during import; retry with new ids.") from exc
    except Exception:
        db.rollback()
        raise
    return created


def validate_sources_batch(
    db: Session, sources: list[EvidenceSourceCreate]
) -> list[EvidenceSourcePreview]:
    """Validate a batch without storing records or audit events."""
    ids = [source.id for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evidence source ids in batch.")
    if any(db.get(EvidenceSource, source_id) is not None for source_id in ids):
        raise ValueError("At least one evidence source id already exists.")
    return [
        EvidenceSourcePreview(
            id=item.id,
            title=item.title,
            source_uri=item.source_uri,
            content_sha256=hashlib.sha256(item.content_text.encode("utf-8")).hexdigest(),
            content_length=len(item.content_text),
        )
        for item in sources
    ]


def list_sources(
    db: Session, *, status: str | None, offset: int, limit: int
) -> tuple[list[EvidenceSource], int]:
    predicate = EvidenceSource.status == status if status else None
    count_query = select(func.count()).select_from(EvidenceSource)
    items_query = select(EvidenceSource)
    if predicate is not None:
        count_query = count_query.where(predicate)
        items_query = items_query.where(predicate)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(items_query.order_by(EvidenceSource.id).offset(offset).limit(limit)))
    return items, total


def approve_source(db: Session, source_id: str, *, reviewer: str) -> EvidenceSource:
    source = db.get(EvidenceSource, source_id)
    if source is None:
        raise LookupError(f"Evidence source '{source_id}' was not found.")
    if source.status == "revoked":
        raise ValueError("Revoked evidence cannot be approved again; create a new version.")
    if not _content_hash_matches(source):
        raise ValueError("Evidence content changed after its hash was recorded; create a new version.")
    try:
        source.status = "approved"
        source.reviewed_by = reviewer
        source.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="evidence_source_approved", resource_type="evidence_source",
            resource_id=source_id, actor=reviewer,
            details={"content_sha256": source.content_sha256},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(source)
    return source


def revoke_source(db: Session, source_id: str, *, reviewer: str) -> EvidenceSource:
    source = db.get(EvidenceSource, source_id)
    if source is None:
        raise LookupError(f"Evidence source '{source_id}' was not found.")
    try:
        source.status = "revoked"
        source.reviewed_by = reviewer
        source.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="evidence_source_revoked", resource_type="evidence_source",
            resource_id=source_id, actor=reviewer,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(source)
    return source


def link_source(db: Session, exhibit_id: str, source_id: str) -> ExhibitEvidenceLink:
    if db.get(Exhibit, exhibit_id) is None:
        raise LookupError(f"Exhibit '{exhibit_id}' was not found.")
    if db.get(EvidenceSource, source_id) is None:
        raise LookupError(f"Evidence source '{source_id}' was not found.")
    link = db.get(ExhibitEvidenceLink, (exhibit_id, source_id))
    if link is None:
        link = ExhibitEvidenceLink(exhibit_id=exhibit_id, source_id=source_id)
        try:
            db.add(link)
            record_audit_log(
                db, action="exhibit_evidence_linked", resource_type="exhibit",
                resource_id=exhibit_id, actor="operator", details={"source_id": source_id},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
    return link


def approve_exhibit(db: Session, exhibit_id: str, *, reviewer: str) -> ExhibitApproval:
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit is None:
        raise LookupError(f"Exhibit '{exhibit_id}' was not found.")
    if exhibit.id.startswith("fixture-") or "fixture" in (exhibit.source_reference or "").lower():
        raise ValueError("Development fixtures cannot be approved for museum use.")
    if not (exhibit.source_reference or "").strip():
        raise ValueError("Exhibit source_reference is required.")
    sources = _linked_sources(db, exhibit_id)
    if not sources or any(
        source.status != "approved" or not _content_hash_matches(source)
        for source in sources
    ):
        raise ValueError("At least one linked, approved evidence source is required.")
    approval = db.get(ExhibitApproval, exhibit_id)
    if approval is None:
        approval = ExhibitApproval(exhibit_id=exhibit_id)
        db.add(approval)
    try:
        approval.status = "approved"
        approval.display_status = "on_display"
        approval.approved_fingerprint = _fingerprint(exhibit, sources)
        approval.reviewed_by = reviewer
        approval.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="exhibit_approved", resource_type="exhibit",
            resource_id=exhibit_id, actor=reviewer,
            details={"fingerprint": approval.approved_fingerprint},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(approval)
    return approval


def revoke_exhibit(db: Session, exhibit_id: str, *, reviewer: str) -> ExhibitApproval:
    approval = db.get(ExhibitApproval, exhibit_id)
    if approval is None:
        raise LookupError(f"Exhibit approval for '{exhibit_id}' was not found.")
    try:
        approval.status = "revoked"
        approval.reviewed_by = reviewer
        approval.reviewed_at = datetime.now(timezone.utc)
        record_audit_log(
            db, action="exhibit_approval_revoked", resource_type="exhibit",
            resource_id=exhibit_id, actor=reviewer,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(approval)
    return approval


def exhibit_approval_issue(db: Session, exhibit: Exhibit) -> str | None:
    approval = db.get(ExhibitApproval, exhibit.id)
    if approval is None or approval.status != "approved":
        return f"Exhibit {exhibit.id} has no current museum approval."
    if approval.display_status != "on_display":
        return f"Exhibit {exhibit.id} is not confirmed on display."
    sources = _linked_sources(db, exhibit.id)
    if not sources or any(source.status != "approved" for source in sources):
        return f"Exhibit {exhibit.id} has missing or revoked evidence."
    if any(not _content_hash_matches(source) for source in sources):
        return f"Exhibit {exhibit.id} has evidence content changed after approval."
    if approval.approved_fingerprint != _fingerprint(exhibit, sources):
        return f"Exhibit {exhibit.id} changed after approval."
    return None


def _linked_sources(db: Session, exhibit_id: str) -> list[EvidenceSource]:
    return list(
        db.scalars(
            select(EvidenceSource)
            .join(ExhibitEvidenceLink, ExhibitEvidenceLink.source_id == EvidenceSource.id)
            .where(ExhibitEvidenceLink.exhibit_id == exhibit_id)
            .order_by(EvidenceSource.id)
        )
    )


def _fingerprint(exhibit: Exhibit, sources: list[EvidenceSource]) -> str:
    payload = {
        "exhibit": {
            "id": exhibit.id,
            "name": exhibit.name,
            "description": exhibit.description,
            "period": exhibit.period,
            "keywords": exhibit.keywords,
            "importance": exhibit.importance,
            "people": exhibit.people,
            "time_range": exhibit.time_range,
            "themes": exhibit.themes,
            "source_reference": exhibit.source_reference,
        },
        "sources": [
            {"id": source.id, "sha256": source.content_sha256}
            for source in sources
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _content_hash_matches(source: EvidenceSource) -> bool:
    return hashlib.sha256(source.content_text.encode("utf-8")).hexdigest() == source.content_sha256
