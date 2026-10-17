"""Bind approved sources to their reviewed title, URI, and body hash.

Revision ID: 0007_source_approval_fingerprint
Revises: 0006_visitor_access_grants
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_source_approval_fingerprint"
down_revision = "0006_visitor_access_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("evidence_sources") as batch_op:
        batch_op.add_column(sa.Column("approved_fingerprint", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("evidence_sources") as batch_op:
        batch_op.drop_column("approved_fingerprint")
