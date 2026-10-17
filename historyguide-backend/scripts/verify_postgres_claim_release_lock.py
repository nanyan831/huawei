from __future__ import annotations

import argparse
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, delete, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.claim_support_review import ClaimSupportReview
from app.models.evidence import EvidenceSource
from app.schemas.history_review_run import HistoryCitation
from app.services.audit_log_service import record_audit_log
from app.services.claim_support_review_service import (
    approve_candidate,
    claim_support_issue,
    create_candidate,
    revoke_candidate,
)
from app.services.evidence_service import approve_source, create_source
from app.services.genios_answer_service import _require_claim_support


ACKNOWLEDGEMENT = "--acknowledge-staging-write-test"
REQUIRED_TABLES = {"alembic_version", "audit_logs", "claim_support_reviews", "evidence_sources"}


@dataclass(frozen=True)
class ProbeResult:
    revoke_blocked_while_release_held_lock: bool
    revocation_visible_after_release: bool
    probe_records_cleaned: bool


def _expected_alembic_head() -> str:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    return ScriptDirectory.from_config(config).get_current_head()


def validate_target_url(database_url: str) -> str | None:
    try:
        url = make_url(database_url)
    except Exception:
        return "Database URL is invalid."
    if url.get_backend_name() != "postgresql":
        return "This write test requires an isolated PostgreSQL staging database; SQLite is not accepted."
    if not url.database:
        return "The PostgreSQL database name is missing."
    return None


def _validate_schema(engine) -> None:
    expected_head = _expected_alembic_head()
    with engine.connect() as connection:
        missing = sorted(REQUIRED_TABLES - set(inspect(connection).get_table_names()))
        if missing:
            raise RuntimeError(f"Required migrated tables are missing: {', '.join(missing)}.")
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one_or_none()
        if revision != expected_head:
            raise RuntimeError(
                f"Database is at Alembic revision {revision or '<empty>'}; expected {expected_head}."
            )


def _cleanup_probe_records(session_factory, *, source_id: str, review_id: str = "") -> bool:
    with session_factory() as db:
        try:
            resource_ids = (source_id, review_id) if review_id else (source_id,)
            db.execute(delete(AuditLog).where(AuditLog.resource_id.in_(resource_ids)))
            if review_id:
                db.execute(delete(ClaimSupportReview).where(ClaimSupportReview.id == review_id))
            db.execute(delete(EvidenceSource).where(EvidenceSource.id == source_id))
            db.commit()
            remaining_review = (
                db.scalar(select(ClaimSupportReview.id).where(ClaimSupportReview.id == review_id))
                if review_id
                else None
            )
            remaining = remaining_review or db.scalar(
                select(EvidenceSource.id).where(EvidenceSource.id == source_id)
            )
            return remaining is None
        except Exception:
            db.rollback()
            return False


def run_probe(database_url: str, *, keep_probe_records: bool = False) -> ProbeResult:
    target_error = validate_target_url(database_url)
    if target_error:
        raise ValueError(target_error)

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=10000 -c lock_timeout=8000",
        },
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    probe_id = uuid.uuid4().hex
    source_id = f"staging-lock-{probe_id}"
    quote = "This staging probe verifies that an approved claim cannot be revoked during release."
    claim = "an approved claim cannot be revoked during release"
    review_id = ""
    release_locked = threading.Event()
    allow_release_commit = threading.Event()
    revoke_started = threading.Event()
    revoke_done = threading.Event()
    errors: list[str] = []
    timings: dict[str, float] = {}
    release_thread: threading.Thread | None = None
    revoke_thread: threading.Thread | None = None

    try:
        _validate_schema(engine)
        with session_factory() as setup_db:
            create_source(
                setup_db,
                source_id=source_id,
                title="Staging claim-release lock probe",
                source_uri=f"urn:historyguide:staging-lock-probe:{probe_id}",
                content_text=quote,
            )
            approve_source(setup_db, source_id, reviewer="staging-lock-probe")
            candidate = create_candidate(
                setup_db, source_id=source_id, evidence_quote=quote, claim_text=claim
            )
            review_id = candidate.id
            approve_candidate(setup_db, review_id, reviewer="staging-lock-probe")

        citation = HistoryCitation(
            source_id=source_id, evidence_quote=quote, claim_text=claim
        )

        def hold_release_lock() -> None:
            with session_factory() as db:
                try:
                    ids = _require_claim_support(db, [citation])
                    if ids != [review_id]:
                        raise RuntimeError("Release check returned an unexpected approval id.")
                    record_audit_log(
                        db,
                        action="staging_claim_release_lock_probe",
                        resource_type="claim_support_review",
                        resource_id=review_id,
                        actor="staging-lock-probe",
                    )
                    db.flush()
                    timings["lock_acquired"] = time.monotonic()
                    release_locked.set()
                    if not allow_release_commit.wait(timeout=10):
                        raise TimeoutError("Release-lock holder timed out waiting to commit.")
                    db.commit()
                    timings["release_committed"] = time.monotonic()
                except Exception as exc:
                    db.rollback()
                    errors.append(f"release thread failed ({type(exc).__name__})")
                    release_locked.set()

        def revoke_approval() -> None:
            with session_factory() as db:
                try:
                    revoke_started.set()
                    revoke_candidate(db, review_id, reviewer="staging-lock-probe-revoker")
                    timings["revoke_committed"] = time.monotonic()
                except Exception as exc:
                    db.rollback()
                    errors.append(f"revocation thread failed ({type(exc).__name__})")
                finally:
                    revoke_done.set()

        release_thread = threading.Thread(target=hold_release_lock, name="claim-release-lock")
        revoke_thread = threading.Thread(target=revoke_approval, name="claim-revocation")
        release_thread.start()
        if not release_locked.wait(timeout=10):
            raise RuntimeError("Release thread did not acquire the approval lock.")
        if errors:
            raise RuntimeError(errors[0])
        revoke_thread.start()
        if not revoke_started.wait(timeout=2):
            raise RuntimeError("Revocation thread did not start.")

        revoke_finished_early = revoke_done.wait(timeout=0.75)
        allow_release_commit.set()
        release_thread.join(timeout=12)
        revoke_thread.join(timeout=12)
        if release_thread.is_alive() or revoke_thread.is_alive():
            raise RuntimeError("Concurrency probe threads did not finish within the safety timeout.")
        if errors:
            raise RuntimeError("; ".join(errors))

        revoke_was_serialized = (
            not revoke_finished_early
            and timings.get("revoke_committed", 0)
            >= timings.get("release_committed", float("inf"))
        )
        with session_factory() as verify_db:
            revocation_visible = claim_support_issue(
                verify_db,
                source_id=source_id,
                evidence_quote=quote,
                claim_text=claim,
            ) is not None
        if not revoke_was_serialized:
            raise RuntimeError("Revocation was not serialized after the release transaction.")
        if not revocation_visible:
            raise RuntimeError("A fresh transaction did not observe the committed revocation.")

        cleaned = False if keep_probe_records else _cleanup_probe_records(
            session_factory, source_id=source_id, review_id=review_id
        )
        return ProbeResult(
            revoke_blocked_while_release_held_lock=True,
            revocation_visible_after_release=True,
            probe_records_cleaned=cleaned,
        )
    finally:
        allow_release_commit.set()
        for thread in (release_thread, revoke_thread):
            if thread is not None and thread.is_alive():
                thread.join(timeout=12)
        if source_id and not keep_probe_records:
            _cleanup_probe_records(session_factory, source_id=source_id, review_id=review_id)
        engine.dispose()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a destructive, self-cleaning PostgreSQL staging probe for the claim-release row lock. "
            "It creates one synthetic source and approval, holds the real release check open, attempts a "
            "concurrent revocation, verifies serialization, and removes its probe records by default."
        )
    )
    parser.add_argument("--database-url", default=None, help="Override HISTORYGUIDE_DATABASE_URL.")
    parser.add_argument(
        ACKNOWLEDGEMENT,
        action="store_true",
        help="Required acknowledgement that the target is isolated staging and probe writes are allowed.",
    )
    parser.add_argument(
        "--keep-probe-records",
        action="store_true",
        help="Keep the uniquely named synthetic records for investigation instead of cleaning them.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.acknowledge_staging_write_test:
        print(f"Refusing to write: pass {ACKNOWLEDGEMENT} only for an isolated staging database.")
        return 2
    database_url = args.database_url or Settings.from_env().database_url
    target_error = validate_target_url(database_url)
    if target_error:
        print(f"Refusing to run: {target_error}")
        return 2
    try:
        result = run_probe(database_url, keep_probe_records=args.keep_probe_records)
    except Exception as exc:
        print(
            "PostgreSQL claim-release lock probe FAILED. "
            f"Error type: {type(exc).__name__}. Database credentials and URL were not printed."
        )
        return 1

    print("PostgreSQL claim-release lock probe PASSED.")
    print("Concurrent revocation remained blocked until the release transaction committed.")
    print("A fresh transaction observed the revocation, so later releases fail closed.")
    print(
        "Synthetic probe records were retained for investigation."
        if args.keep_probe_records
        else f"Synthetic probe records cleaned: {result.probe_records_cleaned}."
    )
    return 0 if args.keep_probe_records or result.probe_records_cleaned else 1


if __name__ == "__main__":
    raise SystemExit(main())
