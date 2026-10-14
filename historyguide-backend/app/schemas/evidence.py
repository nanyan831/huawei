from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSourceCreate(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    source_uri: str = Field(min_length=1)
    content_text: str = Field(min_length=1, max_length=100_000)


class EvidenceSourceRead(EvidenceSourceCreate):
    model_config = {"from_attributes": True}

    content_sha256: str
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None


class EvidenceSourceSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    source_uri: str
    content_sha256: str
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None


class EvidenceSourcePage(BaseModel):
    items: list[EvidenceSourceSummary]
    total: int
    offset: int
    limit: int


class EvidenceSourceBatchCreate(BaseModel):
    sources: list[EvidenceSourceCreate] = Field(min_length=1, max_length=20)


class EvidenceSourceBatchRead(BaseModel):
    imported_count: int
    items: list[EvidenceSourceSummary]


class ReviewerAction(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)


class ExhibitApprovalRead(BaseModel):
    model_config = {"from_attributes": True}

    exhibit_id: str
    status: str
    display_status: str
    approved_fingerprint: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None


class EvidenceLinkRead(BaseModel):
    model_config = {"from_attributes": True}

    exhibit_id: str
    source_id: str
