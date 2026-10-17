from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.history_review_run import HistoryCitation
from app.schemas.review_run import EvidenceCitation


class HistoryAnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(min_length=1, max_length=10)
    draft_answer: str = Field(min_length=1, max_length=8000)
    citations: list[HistoryCitation] = Field(min_length=1, max_length=20)


class ExhibitAnswerRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    recommendation_limit: int = Field(default=3, ge=1, le=10)
    route_max_items: int = Field(default=5, ge=1, le=10)
    draft_answer: str = Field(min_length=1, max_length=8000)
    cited_exhibit_ids: str = Field(min_length=1, max_length=2000)
    citations: list[EvidenceCitation] = Field(min_length=1, max_length=20)


class ReleasedAnswer(BaseModel):
    run_id: str
    decision: Literal["pass", "block"]
    answer: str
    semantic_verified: bool = False
    claim_support_reviewed: bool = False
