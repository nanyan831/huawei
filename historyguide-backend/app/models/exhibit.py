from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Exhibit(Base):
    __tablename__ = "exhibits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    period: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    people: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    time_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    themes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)

