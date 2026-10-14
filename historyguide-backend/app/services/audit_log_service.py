from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCountItem, AuditLogStats


def record_audit_log(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    actor: str = "system",
    details: dict | None = None,
    commit: bool = False,
) -> AuditLog:
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor=actor,
        details=details or {},
    )
    db.add(audit_log)
    if commit:
        db.commit()
        db.refresh(audit_log)
    return audit_log


def list_audit_logs(
    db: Session,
    *,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if action:
        statement = statement.where(AuditLog.action == action)
    if resource_type:
        statement = statement.where(AuditLog.resource_type == resource_type)
    if resource_id:
        statement = statement.where(AuditLog.resource_id == resource_id)
    if actor:
        statement = statement.where(AuditLog.actor == actor)
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(db.scalars(statement).all())


def get_audit_log_stats(db: Session) -> AuditLogStats:
    logs = list_audit_logs(db)
    return AuditLogStats(
        total_logs=len(logs),
        actions=_count_values(log.action for log in logs),
        resource_types=_count_values(log.resource_type for log in logs),
        actors=_count_values(log.actor for log in logs),
        latest_created_at=logs[0].created_at if logs else None,
    )


def _count_values(values) -> list[AuditLogCountItem]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = value.strip() if value else ""
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return [
        AuditLogCountItem(value=value, count=count)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
