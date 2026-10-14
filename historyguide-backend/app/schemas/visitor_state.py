from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


VisitorType = Literal["freshman", "alumnus", "tourist"]


class VisitorStateBase(BaseModel):
    visitor_type: VisitorType
    current_exhibit: str | None = None
    visited_history: list[str] = Field(default_factory=list)
    interest: list[str] = Field(default_factory=list)
    remaining_time: int = Field(ge=0, description="Remaining visit time in minutes.")

    @field_validator("visited_history", "interest")
    @classmethod
    def remove_blank_items(cls, value: list[str]) -> list[str]:
        return [item for item in value if item.strip()]


class VisitorStateCreate(VisitorStateBase):
    session_id: str


class VisitorStateUpdate(BaseModel):
    visitor_type: VisitorType | None = None
    current_exhibit: str | None = None
    visited_history: list[str] | None = None
    interest: list[str] | None = None
    remaining_time: int | None = Field(default=None, ge=0)

    @field_validator("visited_history", "interest")
    @classmethod
    def remove_blank_items(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return [item for item in value if item.strip()]


class VisitorVisitEvent(BaseModel):
    exhibit_id: str = Field(..., min_length=1)
    remaining_time: int | None = Field(default=None, ge=0)


class VisitorVisitEventRead(BaseModel):
    id: int
    session_id: str
    exhibit_id: str
    remaining_time: int | None = None
    event_time: datetime

    model_config = {"from_attributes": True}


class VisitorStateCountItem(BaseModel):
    value: str
    count: int = Field(ge=1)


class RemainingTimeStats(BaseModel):
    min: int = Field(ge=0)
    max: int = Field(ge=0)
    average: float = Field(ge=0)


class VisitorStateStats(BaseModel):
    total_sessions: int = Field(ge=0)
    visitor_types: list[VisitorStateCountItem] = Field(default_factory=list)
    current_exhibits: list[VisitorStateCountItem] = Field(default_factory=list)
    interests: list[VisitorStateCountItem] = Field(default_factory=list)
    no_current_exhibit_count: int = Field(ge=0)
    remaining_time: RemainingTimeStats | None = None


class VisitorStateIntegrityIssue(BaseModel):
    session_id: str
    issue: str
    detail: str
    exhibit_ids: list[str] = Field(default_factory=list)


class VisitorStateIntegrityReport(BaseModel):
    total_sessions: int = Field(ge=0)
    total_visit_events: int = Field(ge=0)
    sessions_with_visit_events: int = Field(ge=0)
    issue_count: int = Field(ge=0)
    issues: list[VisitorStateIntegrityIssue] = Field(default_factory=list)


class VisitorStateRead(VisitorStateBase):
    session_id: str

    model_config = {"from_attributes": True}
