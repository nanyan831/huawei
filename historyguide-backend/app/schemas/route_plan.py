from pydantic import BaseModel, Field


class RoutePlanItem(BaseModel):
    order: int = Field(ge=1)
    exhibit_id: str
    name: str
    estimated_minutes: int = Field(ge=1)
    reason: str


class RoutePlan(BaseModel):
    session_id: str
    remaining_time: int = Field(ge=0)
    planned_minutes: int = Field(ge=0)
    items: list[RoutePlanItem] = Field(default_factory=list)
    planning_note: str = (
        "Rule-based route plan using unvisited exhibits, visitor interests, and remaining time. "
        "It does not perform map navigation or generated explanation."
    )

