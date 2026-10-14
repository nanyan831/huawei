from pydantic import BaseModel, Field

from app.schemas.exhibit import ExhibitRead
from app.schemas.visitor_state import VisitorStateRead, VisitorVisitEventRead


class VisitSummary(BaseModel):
    session_id: str
    visitor_state: VisitorStateRead
    visited_count: int = Field(ge=0)
    visited_exhibits: list[ExhibitRead] = Field(default_factory=list)
    visit_events: list[VisitorVisitEventRead] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    remaining_time: int = Field(ge=0)
    missing_exhibit_ids: list[str] = Field(default_factory=list)
    genios_next_step: str = (
        "Use this structured summary with the knowledge base to generate a grounded visit recap."
    )
