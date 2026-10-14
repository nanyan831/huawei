"""Add source-attributed runs for general history questions.

Revision ID: 0005_history_review_runs
Revises: 0004_review_runs
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_history_review_runs"
down_revision = "0004_review_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "history_review_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("draft_sha256", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("issues", sa.Text(), nullable=True),
        sa.Column("safe_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("history_review_runs")
