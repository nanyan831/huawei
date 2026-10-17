from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.review_run import EvidenceCitation


class VisitorGrantRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)


class VisitorGrantResponse(BaseModel):
    session_id: str
    access_token: str
    expires_at: datetime


class VisitorRevokeResponse(BaseModel):
    revoked_count: int = Field(ge=0)


class VisitorExhibitAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_limit: int = Field(default=3, ge=1, le=10)
    route_max_items: int = Field(default=5, ge=1, le=10)
    draft_answer: str = Field(min_length=1, max_length=8000)
    cited_exhibit_ids: str = Field(min_length=1, max_length=2000)
    citations: list[EvidenceCitation] = Field(min_length=1, max_length=20)
