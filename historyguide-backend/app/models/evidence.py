from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ExhibitEvidenceLink(Base):
    __tablename__ = "exhibit_evidence_links"

    exhibit_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("exhibits.id"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("evidence_sources.id"), primary_key=True
    )


class ExhibitApproval(Base):
    __tablename__ = "exhibit_approvals"

    exhibit_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("exhibits.id"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    display_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    approved_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
