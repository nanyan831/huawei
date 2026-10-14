from sqlalchemy.orm import Session

from app.schemas.system import OperationalAlert, OperationalAlertsResponse
from app.services.audit_log_service import get_audit_log_stats
from app.services.exhibit_service import get_exhibit_quality_report, get_exhibit_source_report
from app.services.visitor_state_service import get_visitor_state_integrity_report


def get_operational_alerts(db: Session) -> OperationalAlertsResponse:
    alerts: list[OperationalAlert] = []

    source_report = get_exhibit_source_report(db)
    if source_report.total == 0:
        alerts.append(
            OperationalAlert(
                name="no_exhibit_records",
                severity="warn",
                resource_type="exhibit",
                count=0,
                detail="No exhibit records are available. Import verified museum records before real demos.",
            )
        )
    if source_report.unsourced_count:
        alerts.append(
            OperationalAlert(
                name="unsourced_exhibits",
                severity="fail",
                resource_type="exhibit",
                count=source_report.unsourced_count,
                detail="Some exhibit records do not have source_reference values.",
            )
        )

    quality_report = get_exhibit_quality_report(db)
    metadata_gap_count = sum(
        issue.count
        for issue in quality_report.issues
        if issue.issue in {"empty_keywords", "empty_themes", "empty_people"}
    )
    if metadata_gap_count:
        alerts.append(
            OperationalAlert(
                name="exhibit_metadata_gaps",
                severity="warn",
                resource_type="exhibit",
                count=metadata_gap_count,
                detail="Some exhibit records have empty keywords, themes, or people metadata.",
            )
        )

    integrity_report = get_visitor_state_integrity_report(db)
    if integrity_report.issue_count:
        alerts.append(
            OperationalAlert(
                name="visitor_state_integrity_issues",
                severity="fail",
                resource_type="visitor_state",
                count=integrity_report.issue_count,
                detail="Visitor State snapshots and visit-event timelines have structural drift.",
            )
        )

    audit_stats = get_audit_log_stats(db)
    if audit_stats.total_logs == 0:
        alerts.append(
            OperationalAlert(
                name="audit_logs_empty",
                severity="warn",
                resource_type="audit_log",
                count=0,
                detail="No audit logs have been recorded yet. State-changing operations should leave audit evidence.",
            )
        )

    fail_count = sum(1 for alert in alerts if alert.severity == "fail")
    warn_count = sum(1 for alert in alerts if alert.severity == "warn")
    return OperationalAlertsResponse(
        status="attention_required" if alerts else "ok",
        total_alerts=len(alerts),
        fail_count=fail_count,
        warn_count=warn_count,
        alerts=alerts,
    )
