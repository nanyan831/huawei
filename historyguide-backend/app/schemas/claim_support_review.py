from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ClaimSupportCandidate(BaseModel):
    source_id: str = Field(min_length=1, max_length=64)
    evidence_quote: str = Field(min_length=8, max_length=800)
    claim_text: str = Field(min_length=8, max_length=800)


class ClaimSupportApproval(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    support_confirmed: Literal[True]


class ClaimSupportRevocation(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)


class ClaimSupportRead(BaseModel):
    id: str
    source_id: str
    source_fingerprint: str
    evidence_quote: str
    claim_text: str
    status: Literal["draft", "approved", "revoked"]
    reviewed_by: str | None
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class ClaimSupportPage(BaseModel):
    items: list[ClaimSupportRead]
    total: int
    offset: int
    limit: int
