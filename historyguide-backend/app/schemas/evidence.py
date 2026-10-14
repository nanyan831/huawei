from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.exhibit import ExhibitCreate, ExhibitRead


class EvidenceSourceCreate(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$", max_length=64)
    title: str = Field(min_length=1, max_length=200)
    source_uri: str = Field(min_length=1, max_length=2000)
    content_text: str = Field(min_length=1, max_length=100_000)

    @field_validator("title", "source_uri", "content_text")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Source fields must not be blank.")
        return value


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
    model_config = {"extra": "forbid"}

    sources: list[EvidenceSourceCreate] = Field(min_length=1, max_length=20)


class EvidenceSourceBatchRead(BaseModel):
    imported_count: int
    items: list[EvidenceSourceSummary]


class ReviewerAction(BaseModel):
    reviewer: str = Field(min_length=1, max_length=80)

    @field_validator("reviewer")
    @classmethod
    def require_reviewer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A reviewer name is required.")
        return value.strip()


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


class EvidenceSourcePreview(BaseModel):
    id: str
    title: str
    source_uri: str
    content_sha256: str
    content_length: int


class EvidenceSourceBatchPreview(BaseModel):
    count: int
    items: list[EvidenceSourcePreview]


class OperatorExhibitCreate(ExhibitCreate):
    model_config = {"extra": "forbid"}

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$", max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=100_000)
    period: str = Field(min_length=1, max_length=120)
    source_reference: str = Field(min_length=1, max_length=2000)
    time_range: str | None = Field(default=None, max_length=120)
    keywords: list[str] = Field(default_factory=list, max_length=100)
    people: list[str] = Field(default_factory=list, max_length=100)
    themes: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("name", "description", "period", "source_reference")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Exhibit fields must not be blank.")
        return value

    @field_validator("keywords", "people", "themes")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 200 for value in values):
            raise ValueError("Metadata terms must be nonblank and at most 200 characters.")
        return values


class EvidenceExhibitBatchCreate(BaseModel):
    model_config = {"extra": "forbid"}

    exhibits: list[OperatorExhibitCreate] = Field(min_length=1, max_length=20)


class EvidenceExhibitBatchRead(BaseModel):
    count: int
    items: list[ExhibitRead]


class EvidenceExhibitRead(BaseModel):
    exhibit: ExhibitRead
    approval: ExhibitApprovalRead | None
    source_ids: list[str]
    approval_issue: str | None


class EvidenceExhibitPage(BaseModel):
    items: list[EvidenceExhibitRead]
    total: int
    offset: int
    limit: int
