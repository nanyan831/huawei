"""Add reviewed evidence sources and exhibit approvals.

Revision ID: 0003_evidence_governance
Revises: 0002_audit_logs
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_evidence_governance"
down_revision = "0002_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "exhibit_evidence_links",
        sa.Column("exhibit_id", sa.String(length=64), sa.ForeignKey("exhibits.id"), primary_key=True),
        sa.Column("source_id", sa.String(length=64), sa.ForeignKey("evidence_sources.id"), primary_key=True),
    )
    op.create_table(
        "exhibit_approvals",
        sa.Column("exhibit_id", sa.String(length=64), sa.ForeignKey("exhibits.id"), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("display_status", sa.String(length=20), nullable=False),
        sa.Column("approved_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("exhibit_approvals")
    op.drop_table("exhibit_evidence_links")
    op.drop_table("evidence_sources")
