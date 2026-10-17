"""Record curator claim-to-quote support decisions.

Revision ID: 0008_claim_support_reviews
Revises: 0007_source_approval_fingerprint
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_claim_support_reviews"
down_revision = "0007_source_approval_fingerprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "claim_support_reviews",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), sa.ForeignKey("evidence_sources.id"), nullable=False),
        sa.Column("source_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_claim_support_reviews_source_id", "claim_support_reviews", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_support_reviews_source_id", table_name="claim_support_reviews")
    op.drop_table("claim_support_reviews")
