from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review_run import ReviewRun
from app.models.history_review_run import HistoryReviewRun
from app.schemas.review_run import ReviewRunStats


def get_review_run_stats(db: Session) -> ReviewRunStats:
    status_counts = dict(
        db.execute(
            select(ReviewRun.status, func.count(ReviewRun.id)).group_by(ReviewRun.status)
        ).all()
    )
    decision_counts = dict(
        db.execute(
            select(ReviewRun.decision, func.count(ReviewRun.id))
            .where(ReviewRun.decision.is_not(None))
            .group_by(ReviewRun.decision)
        ).all()
    )
    expired_open = db.scalar(
        select(func.count(ReviewRun.id)).where(
            ReviewRun.status != "finalized",
            ReviewRun.expires_at <= datetime.now(timezone.utc),
        )
    ) or 0
    history_status_counts = dict(
        db.execute(
            select(HistoryReviewRun.status, func.count(HistoryReviewRun.id))
            .group_by(HistoryReviewRun.status)
        ).all()
    )
    history_decision_counts = dict(
        db.execute(
            select(HistoryReviewRun.decision, func.count(HistoryReviewRun.id))
            .where(HistoryReviewRun.decision.is_not(None))
            .group_by(HistoryReviewRun.decision)
        ).all()
    )
    history_expired_open = db.scalar(
        select(func.count(HistoryReviewRun.id)).where(
            HistoryReviewRun.status != "finalized",
            HistoryReviewRun.expires_at <= datetime.now(timezone.utc),
        )
    ) or 0
    return ReviewRunStats(
        total=sum(status_counts.values()),
        prepared=status_counts.get("prepared", 0),
        reviewed=status_counts.get("reviewed", 0),
        finalized=status_counts.get("finalized", 0),
        expired_open=expired_open,
        passed=decision_counts.get("pass", 0),
        revise_requested=decision_counts.get("revise", 0),
        blocked=decision_counts.get("block", 0),
        history_total=sum(history_status_counts.values()),
        history_prepared=history_status_counts.get("prepared", 0),
        history_reviewed=history_status_counts.get("reviewed", 0),
        history_finalized=history_status_counts.get("finalized", 0),
        history_expired_open=history_expired_open,
        history_passed=history_decision_counts.get("pass", 0),
        history_revise_requested=history_decision_counts.get("revise", 0),
    )
