from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base


class VisitorState(Base):
    __tablename__ = "visitor_states"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    visitor_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    current_exhibit: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("exhibits.id"),
        nullable=True,
        index=True,
    )
    visited_history: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interest: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    remaining_time: Mapped[int] = mapped_column(Integer, nullable=False)

    current_exhibit_detail = relationship("Exhibit")


class VisitorVisitEventLog(Base):
    __tablename__ = "visitor_visit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("visitor_states.session_id"),
        nullable=False,
        index=True,
    )
    exhibit_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exhibits.id"),
        nullable=False,
        index=True,
    )
    remaining_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    visitor_state = relationship("VisitorState")
    exhibit = relationship("Exhibit")
