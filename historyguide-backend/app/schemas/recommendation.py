from pydantic import BaseModel, Field


class ExhibitRecommendation(BaseModel):
    exhibit_id: str
    name: str
    reason: str
    priority: int = Field(ge=1)

