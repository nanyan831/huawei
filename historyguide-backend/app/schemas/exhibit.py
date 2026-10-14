from pydantic import BaseModel, Field


class ExhibitBase(BaseModel):
    id: str = Field(..., examples=["exhibit-001"])
    name: str
    description: str
    period: str
    keywords: list[str] = Field(default_factory=list)
    importance: int = Field(ge=1, le=5)
    people: list[str] = Field(default_factory=list)
    time_range: str | None = None
    themes: list[str] = Field(default_factory=list)
    source_reference: str | None = None


class ExhibitCreate(ExhibitBase):
    pass


class ExhibitRead(ExhibitBase):
    model_config = {"from_attributes": True}


class ExhibitFacetItem(BaseModel):
    value: str
    count: int = Field(ge=1)


class ExhibitFacets(BaseModel):
    total: int = Field(ge=0)
    periods: list[ExhibitFacetItem] = Field(default_factory=list)
    keywords: list[ExhibitFacetItem] = Field(default_factory=list)
    people: list[ExhibitFacetItem] = Field(default_factory=list)
    themes: list[ExhibitFacetItem] = Field(default_factory=list)


class ExhibitQualityIssue(BaseModel):
    issue: str
    count: int = Field(ge=0)
    exhibit_ids: list[str] = Field(default_factory=list)


class ExhibitQualityReport(BaseModel):
    total: int = Field(ge=0)
    source_reference_coverage_percent: float = Field(ge=0, le=100)
    importance_distribution: list[ExhibitFacetItem] = Field(default_factory=list)
    issues: list[ExhibitQualityIssue] = Field(default_factory=list)


class ExhibitSourceReferenceItem(BaseModel):
    source_reference: str
    count: int = Field(ge=1)
    exhibit_ids: list[str] = Field(default_factory=list)


class ExhibitSourceReport(BaseModel):
    total: int = Field(ge=0)
    sourced_count: int = Field(ge=0)
    unsourced_count: int = Field(ge=0)
    unsourced_exhibit_ids: list[str] = Field(default_factory=list)
    source_references: list[ExhibitSourceReferenceItem] = Field(default_factory=list)
