"""Initial NK HistoryGuide schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exhibits",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("period", sa.String(length=120), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("people", sa.JSON(), nullable=False),
        sa.Column("time_range", sa.String(length=120), nullable=True),
        sa.Column("themes", sa.JSON(), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exhibits_id", "exhibits", ["id"])
    op.create_index("ix_exhibits_name", "exhibits", ["name"])
    op.create_index("ix_exhibits_period", "exhibits", ["period"])

    op.create_table(
        "visitor_states",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("visitor_type", sa.String(length=40), nullable=False),
        sa.Column("current_exhibit", sa.String(length=64), nullable=True),
        sa.Column("visited_history", sa.JSON(), nullable=False),
        sa.Column("interest", sa.JSON(), nullable=False),
        sa.Column("remaining_time", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["current_exhibit"], ["exhibits.id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_visitor_states_current_exhibit", "visitor_states", ["current_exhibit"])
    op.create_index("ix_visitor_states_session_id", "visitor_states", ["session_id"])
    op.create_index("ix_visitor_states_visitor_type", "visitor_states", ["visitor_type"])

    op.create_table(
        "visitor_visit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("exhibit_id", sa.String(length=64), nullable=False),
        sa.Column("remaining_time", sa.Integer(), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["exhibit_id"], ["exhibits.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["visitor_states.session_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visitor_visit_events_exhibit_id", "visitor_visit_events", ["exhibit_id"])
    op.create_index("ix_visitor_visit_events_session_id", "visitor_visit_events", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_visitor_visit_events_session_id", table_name="visitor_visit_events")
    op.drop_index("ix_visitor_visit_events_exhibit_id", table_name="visitor_visit_events")
    op.drop_table("visitor_visit_events")

    op.drop_index("ix_visitor_states_visitor_type", table_name="visitor_states")
    op.drop_index("ix_visitor_states_session_id", table_name="visitor_states")
    op.drop_index("ix_visitor_states_current_exhibit", table_name="visitor_states")
    op.drop_table("visitor_states")

    op.drop_index("ix_exhibits_period", table_name="exhibits")
    op.drop_index("ix_exhibits_name", table_name="exhibits")
    op.drop_index("ix_exhibits_id", table_name="exhibits")
    op.drop_table("exhibits")
