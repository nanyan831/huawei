"""Persist revocable visitor access grants.

Revision ID: 0006_visitor_access_grants
Revises: 0005_history_review_runs
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_visitor_access_grants"
down_revision = "0005_history_review_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visitor_access_grants",
        sa.Column("token_sha256", sa.String(length=64), primary_key=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("visitor_states.session_id"), nullable=False),
        sa.Column("expires_at_epoch", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_visitor_access_grants_session_id", "visitor_access_grants", ["session_id"])
    op.create_index("ix_visitor_access_grants_expires_at_epoch", "visitor_access_grants", ["expires_at_epoch"])


def downgrade() -> None:
    op.drop_index("ix_visitor_access_grants_expires_at_epoch", table_name="visitor_access_grants")
    op.drop_index("ix_visitor_access_grants_session_id", table_name="visitor_access_grants")
    op.drop_table("visitor_access_grants")
