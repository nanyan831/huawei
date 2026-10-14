from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.audit_log import AuditLogRead, AuditLogStats
from app.services.audit_log_service import get_audit_log_stats, list_audit_logs


router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("/stats", response_model=AuditLogStats)
def read_audit_log_stats(db: Session = Depends(get_db)) -> AuditLogStats:
    return get_audit_log_stats(db)


@router.get("", response_model=list[AuditLogRead])
def read_audit_logs(
    action: str | None = Query(default=None, description="Filter by exact audit action."),
    resource_type: str | None = Query(default=None, description="Filter by audited resource type."),
    resource_id: str | None = Query(default=None, description="Filter by audited resource id."),
    actor: str | None = Query(default=None, description="Filter by actor."),
    limit: int | None = Query(default=None, ge=1, le=200, description="Maximum number of audit logs to return."),
    offset: int = Query(default=0, ge=0, description="Number of matching audit logs to skip."),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    return list_audit_logs(
        db,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor=actor,
        limit=limit,
        offset=offset,
    )
