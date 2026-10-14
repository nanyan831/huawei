import pytest
from sqlalchemy import event, select

from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceSource, ExhibitApproval, ExhibitEvidenceLink
from app.models.exhibit import Exhibit
from app.services.evidence_service import (
    approve_exhibit,
    approve_source,
    create_source,
    link_source,
    revoke_exhibit,
    revoke_source,
)


def _exhibit(db_session, exhibit_id: str = "transaction-exhibit") -> Exhibit:
    exhibit = Exhibit(
        id=exhibit_id,
        name="Transaction test exhibit",
        description="A test exhibit for transaction rollback.",
        period="test-period",
        keywords=[],
        importance=3,
        people=[],
        time_range=None,
        themes=[],
        source_reference="Museum archive transaction test.",
    )
    db_session.add(exhibit)
    db_session.commit()
    return exhibit


def _source(db_session, source_id: str = "transaction-source") -> EvidenceSource:
    return create_source(
        db_session,
        source_id=source_id,
        title="Transaction test source",
        source_uri="museum-archive:transaction-test",
        content_text="Transaction rollback evidence.",
    )


def _fail_audit_insert(mapper, connection, target) -> None:
    raise RuntimeError("injected audit failure")


def _assert_audit_failure(db_session, action) -> None:
    event.listen(AuditLog, "before_insert", _fail_audit_insert)
    try:
        with pytest.raises(RuntimeError, match="injected audit failure"):
            action()
    finally:
        event.remove(AuditLog, "before_insert", _fail_audit_insert)


def test_single_source_create_rolls_back_when_audit_insert_fails(db_session) -> None:
    _assert_audit_failure(
        db_session,
        lambda: create_source(
            db_session,
            source_id="failed-source",
            title="Failed source",
            source_uri="museum-archive:failed",
            content_text="This insert must roll back.",
        ),
    )

    db_session.expire_all()
    assert db_session.get(EvidenceSource, "failed-source") is None
    assert db_session.scalar(select(AuditLog).where(AuditLog.resource_id == "failed-source")) is None


def test_single_source_review_changes_roll_back_when_audit_insert_fails(db_session) -> None:
    source = _source(db_session)

    _assert_audit_failure(
        db_session,
        lambda: approve_source(db_session, source.id, reviewer="reviewer"),
    )
    db_session.expire_all()
    source = db_session.get(EvidenceSource, source.id)
    assert source.status == "draft"
    assert source.reviewed_by is None

    approve_source(db_session, source.id, reviewer="reviewer")
    _assert_audit_failure(
        db_session,
        lambda: revoke_source(db_session, source.id, reviewer="reviewer"),
    )
    db_session.expire_all()
    assert db_session.get(EvidenceSource, source.id).status == "approved"


def test_source_link_rolls_back_when_audit_insert_fails(db_session) -> None:
    exhibit = _exhibit(db_session)
    source = _source(db_session)

    _assert_audit_failure(
        db_session,
        lambda: link_source(db_session, exhibit.id, source.id),
    )

    db_session.expire_all()
    assert db_session.get(ExhibitEvidenceLink, (exhibit.id, source.id)) is None


def test_exhibit_approval_changes_roll_back_when_audit_insert_fails(db_session) -> None:
    exhibit = _exhibit(db_session)
    source = _source(db_session)
    approve_source(db_session, source.id, reviewer="reviewer")
    link_source(db_session, exhibit.id, source.id)

    _assert_audit_failure(
        db_session,
        lambda: approve_exhibit(db_session, exhibit.id, reviewer="reviewer"),
    )
    db_session.expire_all()
    assert db_session.get(ExhibitApproval, exhibit.id) is None

    approve_exhibit(db_session, exhibit.id, reviewer="reviewer")
    _assert_audit_failure(
        db_session,
        lambda: revoke_exhibit(db_session, exhibit.id, reviewer="reviewer"),
    )
    db_session.expire_all()
    approval = db_session.get(ExhibitApproval, exhibit.id)
    assert approval.status == "approved"
    assert approval.display_status == "on_display"
