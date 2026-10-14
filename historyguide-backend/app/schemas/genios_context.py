from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.exhibit import ExhibitRead
from app.schemas.recommendation import ExhibitRecommendation
from app.schemas.route_plan import RoutePlan
from app.schemas.visit_summary import VisitSummary
from app.schemas.visitor_state import (
    VisitorStateIntegrityReport,
    VisitorStateRead,
    VisitorVisitEventRead,
)


class GeniosCollaborationContract(BaseModel):
    backend_role: str = Field(
        default="Provide structured visit context, exhibit data, visitor state, and recommendation candidates."
    )
    genios_role: str = Field(
        default="Handle dialogue, RAG retrieval, knowledge grounding, and generated explanation content."
    )
    generation_boundary: str = Field(
        default="The backend does not generate museum explanation text or call large language models."
    )


class GeniosEndpointCapability(BaseModel):
    name: str
    method: str = "GET"
    path: str
    purpose: str
    requires_session: bool = False


class GeniosCapabilityPackage(BaseModel):
    service_id: str
    version: str
    collaboration_contract: GeniosCollaborationContract = Field(default_factory=GeniosCollaborationContract)
    supported_visitor_types: list[str] = Field(default_factory=list)
    primary_workflow: list[str] = Field(default_factory=list)
    endpoints: list[GeniosEndpointCapability] = Field(default_factory=list)
    integration_notes: list[str] = Field(default_factory=list)


class GeniosContextPackage(BaseModel):
    session_id: str
    visitor_state: VisitorStateRead
    current_exhibit: ExhibitRead | None = None
    visited_exhibits: list[ExhibitRead] = Field(default_factory=list)
    visit_events: list[VisitorVisitEventRead] = Field(default_factory=list)
    recommendations: list[ExhibitRecommendation] = Field(default_factory=list)
    grounding_exhibit_ids: list[str] = Field(default_factory=list)
    missing_exhibit_ids: list[str] = Field(default_factory=list)
    collaboration_contract: GeniosCollaborationContract = Field(default_factory=GeniosCollaborationContract)


class GeniosPreflightCheck(BaseModel):
    name: str
    status: Literal["pass", "warn", "fail"]
    detail: str


class GeniosPreflightPackage(BaseModel):
    session_id: str
    ready_for_handoff: bool
    checks: list[GeniosPreflightCheck] = Field(default_factory=list)
    missing_exhibit_ids: list[str] = Field(default_factory=list)
    integrity_report: VisitorStateIntegrityReport
    visit_event_count: int = Field(ge=0)
    recommendation_count: int = Field(ge=0)
    collaboration_contract: GeniosCollaborationContract = Field(default_factory=GeniosCollaborationContract)


class GeniosGroundingPackage(BaseModel):
    session_id: str
    grounding_exhibit_ids: list[str] = Field(default_factory=list)
    exhibits: list[ExhibitRead] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    source_reference_count: int = Field(default=0, ge=0)
    sourced_exhibit_ids: list[str] = Field(default_factory=list)
    unsourced_exhibit_ids: list[str] = Field(default_factory=list)
    grounding_sources_complete: bool = False
    missing_exhibit_ids: list[str] = Field(default_factory=list)
    collaboration_contract: GeniosCollaborationContract = Field(default_factory=GeniosCollaborationContract)


class GeniosSourceSafetySummary(BaseModel):
    ready_for_generation: bool
    grounding_sources_complete: bool
    source_reference_count: int = Field(default=0, ge=0)
    sourced_exhibit_ids: list[str] = Field(default_factory=list)
    unsourced_exhibit_ids: list[str] = Field(default_factory=list)
    missing_exhibit_ids: list[str] = Field(default_factory=list)
    blocking_check_names: list[str] = Field(default_factory=list)
    safety_note: str


class GeniosHandoffPackage(BaseModel):
    session_id: str
    source_safety: GeniosSourceSafetySummary
    preflight: GeniosPreflightPackage
    context: GeniosContextPackage
    route_plan: RoutePlan
    visit_summary: VisitSummary
    handoff_note: str = (
        "Structured backend handoff for GeniOS. Use it for dialogue, RAG grounding, route-aware "
        "decisions, and recap generation. The backend does not generate explanation text."
    )


class GeniosFlatHandoffPackage(BaseModel):
    session_id: str
    ready_for_generation: bool
    grounding_sources_complete: bool
    source_reference_count: int = Field(default=0, ge=0)
    sourced_exhibit_ids: str = ""
    unsourced_exhibit_ids: str = ""
    missing_exhibit_ids: str = ""
    blocking_check_names: str = ""
    visitor_type: str
    current_exhibit_id: str = ""
    visited_count: int = Field(default=0, ge=0)
    recommendation_count: int = Field(default=0, ge=0)
    recommendation_exhibit_ids: str = ""
    route_exhibit_ids: str = ""
    planned_minutes: int = Field(default=0, ge=0)
    remaining_time: int | None = None
    handoff_note: str


class GeniosReviewRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    draft_answer: str = Field(min_length=1, max_length=8000)
    cited_exhibit_ids: str = Field(
        default="",
        max_length=2000,
        description="Comma-separated exhibit ids cited by the draft answer.",
    )
    recommendation_limit: int = Field(default=3, ge=1, le=10)
    route_max_items: int = Field(default=5, ge=1, le=10)


class GeniosReviewResponse(BaseModel):
    session_id: str
    decision: Literal["pass", "revise", "block"]
    issues: str = ""
    safe_answer: str
    ready_for_generation: bool
    grounding_sources_complete: bool
    route_order_valid: bool
    exhibit_ids_valid: bool
    source_references_valid: bool
    fixture_data_detected: bool
    checked_exhibit_ids: str = ""
