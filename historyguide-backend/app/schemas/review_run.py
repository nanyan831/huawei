from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.genios_context import GeniosHandoffPackage


class PrepareRunRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    recommendation_limit: int = Field(default=3, ge=1, le=10)
    route_max_items: int = Field(default=5, ge=1, le=10)


class ApprovedEvidenceExcerpt(BaseModel):
    exhibit_id: str
    source_id: str
    title: str
    source_uri: str
    content_sha256: str
    excerpt_text: str
    truncated: bool


class PrepareRunResponse(BaseModel):
    run_id: str
    session_id: str
    expires_at: datetime
    handoff: GeniosHandoffPackage
    approved_evidence: list[ApprovedEvidenceExcerpt] = Field(default_factory=list)


class EvidenceCitation(BaseModel):
    exhibit_id: str = Field(min_length=1, max_length=64)
    source_id: str = Field(min_length=1, max_length=64)
    evidence_quote: str = Field(min_length=8, max_length=800)
    claim_text: str = Field(min_length=8, max_length=800)

    @field_validator("evidence_quote", "claim_text")
    @classmethod
    def require_nonblank_evidence(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Evidence quote and claim text must not be blank.")
        return value


class ReviewRunRequest(BaseModel):
    draft_answer: str = Field(min_length=1, max_length=8000)
    cited_exhibit_ids: str = Field(min_length=1, max_length=2000)
    citations: list[EvidenceCitation] = Field(default_factory=list, max_length=20)


class ReviewRunResponse(BaseModel):
    run_id: str
    session_id: str
    decision: Literal["pass", "revise", "block"]
    issues: str
    safe_answer: str
    draft_sha256: str


class FinalizeRunRequest(BaseModel):
    draft_answer: str = Field(min_length=1, max_length=8000)


class FinalizeRunResponse(BaseModel):
    run_id: str
    decision: Literal["pass", "block"]
    answer: str


class ReviewRunStats(BaseModel):
    total: int
    prepared: int
    reviewed: int
    finalized: int
    expired_open: int
    passed: int
    revise_requested: int
    blocked: int
    history_total: int
    history_prepared: int
    history_reviewed: int
    history_finalized: int
    history_expired_open: int
    history_passed: int
    history_revise_requested: int
