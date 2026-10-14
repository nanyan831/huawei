from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HistoryPrepareRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(min_length=1, max_length=10)


class HistoryEvidenceExcerpt(BaseModel):
    source_id: str
    title: str
    source_uri: str
    content_sha256: str
    excerpt_text: str
    truncated: bool


class HistoryPrepareResponse(BaseModel):
    run_id: str
    expires_at: datetime
    approved_evidence: list[HistoryEvidenceExcerpt]


class HistoryCitation(BaseModel):
    source_id: str = Field(min_length=1, max_length=64)
    evidence_quote: str = Field(min_length=8, max_length=800)


class HistoryReviewRequest(BaseModel):
    draft_answer: str = Field(min_length=1, max_length=8000)
    citations: list[HistoryCitation] = Field(default_factory=list, max_length=20)


class HistoryReviewResponse(BaseModel):
    run_id: str
    decision: Literal["pass", "revise"]
    issues: str
    safe_answer: str
    draft_sha256: str
    semantic_verified: bool = False


class HistoryFinalizeRequest(BaseModel):
    draft_answer: str = Field(min_length=1, max_length=8000)


class HistoryFinalizeResponse(BaseModel):
    run_id: str
    answer: str
    semantic_verified: bool = False
