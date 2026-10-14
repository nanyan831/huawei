"""Add review run receipts for snapshot-bound answer checks.

Revision ID: 0004_review_runs
Revises: 0003_evidence_governance
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_review_runs"
down_revision = "0003_evidence_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("visitor_states.session_id"), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("recommendation_limit", sa.Integer(), nullable=False),
        sa.Column("route_max_items", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("draft_sha256", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("issues", sa.Text(), nullable=True),
        sa.Column("safe_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_runs_session_id", "review_runs", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_review_runs_session_id", table_name="review_runs")
    op.drop_table("review_runs")
