from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.history_review_run import HistoryEvidenceExcerpt


class ApprovedSourceSearchRequest(BaseModel):
    model_config = {"extra": "forbid"}

    keywords: list[str] = Field(min_length=1, max_length=5)
    limit: int = Field(default=5, ge=1, le=5)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not 2 <= len(value) <= 40 for value in normalized):
            raise ValueError("Each keyword must contain 2-40 characters.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Duplicate keywords are not allowed.")
        return normalized


class ApprovedSourceSearchResponse(BaseModel):
    retrieval_mode: Literal["lexical"] = "lexical"
    matches: list[HistoryEvidenceExcerpt]
