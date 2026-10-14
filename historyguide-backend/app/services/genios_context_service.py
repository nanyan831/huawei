from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState
from app.core.config import settings
from app.schemas.genios_context import (
    GeniosCapabilityPackage,
    GeniosContextPackage,
    GeniosEndpointCapability,
    GeniosGroundingPackage,
    GeniosHandoffPackage,
    GeniosPreflightCheck,
    GeniosPreflightPackage,
    GeniosReviewRequest,
    GeniosReviewResponse,
    GeniosSourceSafetySummary,
)
from app.schemas.visitor_state import VisitorStateRead, VisitorVisitEventRead
from app.services.exhibit_service import get_exhibit
from app.services.evidence_service import exhibit_approval_issue
from app.services.recommendation_service import recommend_exhibits
from app.services.route_plan_service import build_route_plan
from app.services.visit_summary_service import build_visit_summary
from app.services.visitor_state_service import get_visitor_state_integrity_report, list_visit_events


def build_genios_capability_package() -> GeniosCapabilityPackage:
    return GeniosCapabilityPackage(
        service_id=settings.service_id,
        version=settings.app_version,
        supported_visitor_types=["freshman", "alumnus", "tourist"],
        primary_workflow=[
            "Create or update Visitor State for the real visit session.",
            "Record exhibit visit events when the visitor scans or enters an exhibit.",
            "Request the GeniOS context package before dialogue or RAG grounding.",
            "Use the handoff package when one call should include preflight, context, route plan, and visit summary.",
            "Generate explanation content inside GeniOS with the verified knowledge base, not in the backend.",
            "For exhibit answers, prepare a run, review the draft, and release only the finalized answer.",
            "For general history questions without exhibit ids, use an approved-source history run instead of inventing exhibit ids.",
        ],
        endpoints=[
            GeniosEndpointCapability(
                name="GeniOS capabilities",
                path="/api/genios/capabilities",
                purpose="Discover backend collaboration boundaries, supported visitor types, and integration workflow.",
            ),
            GeniosEndpointCapability(
                name="GeniOS context package",
                path="/api/genios/context/{session_id}",
                purpose="Read structured Visitor State, exhibit context, recommendations, and missing exhibit references.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="GeniOS grounding package",
                path="/api/genios/grounding/{session_id}",
                purpose="Read exhibit records and source references for context grounding ids.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="GeniOS preflight package",
                path="/api/genios/preflight/{session_id}",
                purpose="Check whether one visit session is structurally ready for GeniOS handoff.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="GeniOS handoff package",
                path="/api/genios/handoff/{session_id}",
                purpose="Read preflight, context, route plan, and visit summary in one structured package.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="GeniOS answer review",
                method="POST",
                path="/api/genios/review",
                purpose="Deterministically review a draft answer against handoff safety, exhibit ids, and route order.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Prepare snapshot-bound review run",
                method="POST",
                path="/api/genios/runs",
                purpose="Capture a short-lived visitor and evidence snapshot before generating an exhibit answer.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Review snapshot-bound draft",
                method="POST",
                path="/api/genios/runs/{run_id}/review",
                purpose="Check a draft against the captured state and approved exhibit evidence.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Finalize reviewed answer",
                method="POST",
                path="/api/genios/runs/{run_id}/finalize",
                purpose="Return only the previously reviewed draft or a safe block answer while the snapshot is current.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Prepare approved-source history run",
                method="POST",
                path="/api/genios/history-runs",
                purpose="Bind a general history question to approved source ids without a visitor or exhibit id.",
            ),
            GeniosEndpointCapability(
                name="Review attributed history draft",
                method="POST",
                path="/api/genios/history-runs/{run_id}/review",
                purpose="Check visible source ids and exact quotations; semantic accuracy is not verified.",
            ),
            GeniosEndpointCapability(
                name="Finalize attributed history answer",
                method="POST",
                path="/api/genios/history-runs/{run_id}/finalize",
                purpose="Release only the unchanged, structurally attributed history draft.",
            ),
            GeniosEndpointCapability(
                name="Visitor State",
                method="POST/PATCH/GET",
                path="/api/visitor-states",
                purpose="Create, update, list, and read structured real-visit sessions.",
            ),
            GeniosEndpointCapability(
                name="Visitor State integrity report",
                path="/api/visitor-states/integrity-report",
                purpose="Inspect consistency between Visitor State snapshots and visit-event timelines.",
            ),
            GeniosEndpointCapability(
                name="Visitor State session integrity",
                path="/api/visitor-states/{session_id}/integrity",
                purpose="Inspect snapshot and visit-event timeline consistency for one active visit session.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Visit event",
                method="GET/POST",
                path="/api/visitor-states/{session_id}/visit-events",
                purpose="Record exhibit scan or entry events and read the structured visit-event timeline with optional pagination.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Recommendations",
                path="/api/recommendations/{session_id}",
                purpose="Read rule-based next-exhibit candidates with structured reasons.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Visit route plan",
                path="/api/visit-routes/{session_id}/plan",
                purpose="Read a rule-based ordered route plan derived from recommendations and remaining time.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Visit summary",
                path="/api/visits/{session_id}/summary",
                purpose="Read a structured summary for grounded recap generation.",
                requires_session=True,
            ),
            GeniosEndpointCapability(
                name="Exhibit quality report",
                path="/api/exhibits/quality-report",
                purpose="Inspect structured exhibit metadata completeness before integration.",
            ),
            GeniosEndpointCapability(
                name="Exhibit source report",
                path="/api/exhibits/source-report",
                purpose="Inspect source_reference grouping and unsourced exhibit ids before integration.",
            ),
        ],
        integration_notes=[
            "The backend returns structured data only and does not call large language models.",
            "Historical explanation text should be generated by GeniOS using verified RAG sources.",
            "Use grounding_exhibit_ids from context or handoff packages as exhibit-level RAG seed ids.",
            "Check grounding_sources_complete before generated explanation; unsourced grounding exhibits should be fixed first.",
            "Imported real exhibit records should include non-empty source_reference values.",
            "Missing exhibit references are reported in context and summary packages instead of being silently ignored.",
        ],
    )


def build_genios_context_package(
    db: Session,
    visitor_state: VisitorState,
    *,
    recommendation_limit: int = 3,
) -> GeniosContextPackage:
    missing_exhibit_ids: list[str] = []

    current_exhibit = None
    if visitor_state.current_exhibit:
        current_exhibit = get_exhibit(db, visitor_state.current_exhibit)
        if current_exhibit is None:
            missing_exhibit_ids.append(visitor_state.current_exhibit)

    visited_exhibits = []
    for exhibit_id in visitor_state.visited_history:
        exhibit = get_exhibit(db, exhibit_id)
        if exhibit is None:
            if exhibit_id not in missing_exhibit_ids:
                missing_exhibit_ids.append(exhibit_id)
            continue
        visited_exhibits.append(exhibit)

    recommendations = recommend_exhibits(db, visitor_state, limit=recommendation_limit)

    return GeniosContextPackage(
        session_id=visitor_state.session_id,
        visitor_state=VisitorStateRead.model_validate(visitor_state),
        current_exhibit=current_exhibit,
        visited_exhibits=visited_exhibits,
        visit_events=[
            VisitorVisitEventRead.model_validate(visit_event)
            for visit_event in list_visit_events(db, visitor_state.session_id)
        ],
        recommendations=recommendations,
        grounding_exhibit_ids=_build_grounding_exhibit_ids(
            current_exhibit_id=visitor_state.current_exhibit,
            visited_history=visitor_state.visited_history,
            recommendation_ids=[recommendation.exhibit_id for recommendation in recommendations],
            missing_exhibit_ids=missing_exhibit_ids,
        ),
        missing_exhibit_ids=missing_exhibit_ids,
    )


def build_genios_preflight_package(
    db: Session,
    visitor_state: VisitorState,
    *,
    recommendation_limit: int = 3,
) -> GeniosPreflightPackage:
    context = build_genios_context_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )
    integrity_report = get_visitor_state_integrity_report(
        db,
        session_id=visitor_state.session_id,
    )
    unsourced_grounding_exhibit_ids = _find_unsourced_grounding_exhibit_ids(
        db,
        context.grounding_exhibit_ids,
    )

    checks = [
        GeniosPreflightCheck(
            name="exhibit_references",
            status="fail" if context.missing_exhibit_ids else "pass",
            detail=(
                "Missing exhibit references must be resolved before grounded handoff."
                if context.missing_exhibit_ids
                else "Current and visited exhibit references resolve to known exhibit records."
            ),
        ),
        GeniosPreflightCheck(
            name="grounding_source_references",
            status="fail" if unsourced_grounding_exhibit_ids else "pass",
            detail=(
                "Grounding exhibit records without source_reference must be completed before generated explanation."
                if unsourced_grounding_exhibit_ids
                else "Grounding exhibit records include source_reference values."
            ),
        ),
        GeniosPreflightCheck(
            name="visitor_state_integrity",
            status="fail" if integrity_report.issue_count else "pass",
            detail=(
                "Visitor State snapshot and visit-event timeline have structural drift."
                if integrity_report.issue_count
                else "Visitor State snapshot and visit-event timeline are structurally aligned."
            ),
        ),
        GeniosPreflightCheck(
            name="visit_event_timeline",
            status="pass" if context.visit_events else "warn",
            detail=(
                "Visit-event timeline is available for continuity."
                if context.visit_events
                else "No visit-event timeline entries are recorded yet."
            ),
        ),
        GeniosPreflightCheck(
            name="recommendations",
            status="pass" if context.recommendations else "warn",
            detail=(
                "Recommendation candidates are available for route-aware dialogue."
                if context.recommendations
                else "No recommendation candidates are available from current exhibit data and state."
            ),
        ),
    ]

    return GeniosPreflightPackage(
        session_id=visitor_state.session_id,
        ready_for_handoff=not any(check.status == "fail" for check in checks),
        checks=checks,
        missing_exhibit_ids=context.missing_exhibit_ids,
        integrity_report=integrity_report,
        visit_event_count=len(context.visit_events),
        recommendation_count=len(context.recommendations),
    )


def build_genios_grounding_package(
    db: Session,
    visitor_state: VisitorState,
    *,
    recommendation_limit: int = 3,
) -> GeniosGroundingPackage:
    context = build_genios_context_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )
    exhibits = []
    for exhibit_id in context.grounding_exhibit_ids:
        exhibit = get_exhibit(db, exhibit_id)
        if exhibit is not None:
            exhibits.append(exhibit)

    source_references = []
    sourced_exhibit_ids = []
    unsourced_exhibit_ids = []
    for exhibit in exhibits:
        source_reference = (exhibit.source_reference or "").strip()
        if source_reference:
            if source_reference not in source_references:
                source_references.append(source_reference)
            sourced_exhibit_ids.append(exhibit.id)
        else:
            unsourced_exhibit_ids.append(exhibit.id)

    return GeniosGroundingPackage(
        session_id=visitor_state.session_id,
        grounding_exhibit_ids=context.grounding_exhibit_ids,
        exhibits=exhibits,
        source_references=source_references,
        source_reference_count=len(source_references),
        sourced_exhibit_ids=sourced_exhibit_ids,
        unsourced_exhibit_ids=unsourced_exhibit_ids,
        grounding_sources_complete=not unsourced_exhibit_ids,
        missing_exhibit_ids=context.missing_exhibit_ids,
    )


def build_genios_handoff_package(
    db: Session,
    visitor_state: VisitorState,
    *,
    recommendation_limit: int = 3,
    route_max_items: int = 5,
) -> GeniosHandoffPackage:
    preflight = build_genios_preflight_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )
    grounding = build_genios_grounding_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )

    return GeniosHandoffPackage(
        session_id=visitor_state.session_id,
        source_safety=_build_source_safety_summary(db, preflight, grounding),
        preflight=preflight,
        context=build_genios_context_package(
            db,
            visitor_state,
            recommendation_limit=recommendation_limit,
        ),
        route_plan=build_route_plan(db, visitor_state, max_items=route_max_items),
        visit_summary=build_visit_summary(db, visitor_state),
    )


def review_genios_answer(
    db: Session,
    visitor_state: VisitorState,
    review: GeniosReviewRequest,
) -> GeniosReviewResponse:
    handoff = build_genios_handoff_package(
        db,
        visitor_state,
        recommendation_limit=review.recommendation_limit,
        route_max_items=review.route_max_items,
    )
    cited_exhibit_ids = _parse_comma_separated_ids(review.cited_exhibit_ids)
    grounding_exhibit_ids = set(handoff.context.grounding_exhibit_ids)
    sourced_exhibit_ids = set(handoff.source_safety.sourced_exhibit_ids)
    invalid_exhibit_ids = [
        exhibit_id for exhibit_id in cited_exhibit_ids if exhibit_id not in grounding_exhibit_ids
    ]
    unsourced_cited_ids = [
        exhibit_id for exhibit_id in cited_exhibit_ids if exhibit_id not in sourced_exhibit_ids
    ]

    route_exhibit_ids = [item.exhibit_id for item in handoff.route_plan.items]
    route_id_set = set(route_exhibit_ids)
    cited_route_ids = [exhibit_id for exhibit_id in cited_exhibit_ids if exhibit_id in route_id_set]
    expected_route_ids = [exhibit_id for exhibit_id in route_exhibit_ids if exhibit_id in cited_route_ids]
    route_order_valid = cited_route_ids == expected_route_ids

    grounding_exhibits = []
    for exhibit_id in handoff.context.grounding_exhibit_ids:
        exhibit = get_exhibit(db, exhibit_id)
        if exhibit is not None:
            grounding_exhibits.append(exhibit)
    fixture_data_detected = any(
        exhibit.id.startswith("fixture-")
        or "fixture" in (exhibit.source_reference or "").lower()
        for exhibit in grounding_exhibits
    )
    approval_issues = [
        issue
        for exhibit in grounding_exhibits
        if (issue := exhibit_approval_issue(db, exhibit)) is not None
    ]
    exhibit_ids_valid = bool(cited_exhibit_ids) and not invalid_exhibit_ids
    source_references_valid = (
        bool(cited_exhibit_ids) and not unsourced_cited_ids and not approval_issues
    )

    blocking_issues: list[str] = []
    revision_issues: list[str] = []
    if not handoff.source_safety.ready_for_generation:
        blocking_issues.append("Visitor context is not ready for generation.")
    if not handoff.source_safety.grounding_sources_complete:
        blocking_issues.append("Grounding source references are incomplete.")
    if handoff.source_safety.missing_exhibit_ids:
        blocking_issues.append(
            "Missing exhibit ids: " + ",".join(handoff.source_safety.missing_exhibit_ids)
        )
    if handoff.source_safety.unsourced_exhibit_ids:
        blocking_issues.append(
            "Unsourced exhibit ids: " + ",".join(handoff.source_safety.unsourced_exhibit_ids)
        )
    if fixture_data_detected:
        blocking_issues.append("Development fixture data cannot be used for real museum explanations.")
    blocking_issues.extend(approval_issues)

    if not cited_exhibit_ids:
        revision_issues.append("At least one cited exhibit id is required for review.")
    if invalid_exhibit_ids:
        revision_issues.append("Unknown grounding exhibit ids: " + ",".join(invalid_exhibit_ids))
    if unsourced_cited_ids:
        revision_issues.append("Cited exhibit ids lack verified sources: " + ",".join(unsourced_cited_ids))
    if not route_order_valid:
        revision_issues.append("Cited route exhibits do not follow the backend route order.")

    issues = blocking_issues + revision_issues
    if blocking_issues:
        decision = "block"
        safe_answer = "当前参观上下文或资料来源未通过安全检查，暂时无法提供可靠讲解。"
    elif revision_issues:
        decision = "revise"
        safe_answer = "当前回答的展品引用或参观顺序未通过检查，请依据 HistoryGuide 工具结果重新生成。"
    else:
        decision = "pass"
        safe_answer = review.draft_answer.strip()

    return GeniosReviewResponse(
        session_id=review.session_id,
        decision=decision,
        issues=" | ".join(issues),
        safe_answer=safe_answer,
        ready_for_generation=handoff.source_safety.ready_for_generation and not approval_issues,
        grounding_sources_complete=handoff.source_safety.grounding_sources_complete,
        route_order_valid=route_order_valid,
        exhibit_ids_valid=exhibit_ids_valid,
        source_references_valid=source_references_valid,
        fixture_data_detected=fixture_data_detected,
        checked_exhibit_ids=",".join(cited_exhibit_ids),
    )


def _parse_comma_separated_ids(value: str) -> list[str]:
    ids: list[str] = []
    for item in value.split(","):
        exhibit_id = item.strip()
        if exhibit_id and exhibit_id not in ids:
            ids.append(exhibit_id)
    return ids


def _build_grounding_exhibit_ids(
    *,
    current_exhibit_id: str | None,
    visited_history: list[str],
    recommendation_ids: list[str],
    missing_exhibit_ids: list[str],
) -> list[str]:
    ordered_ids: list[str] = []
    if current_exhibit_id:
        ordered_ids.append(current_exhibit_id)
    ordered_ids.extend(visited_history)
    ordered_ids.extend(recommendation_ids)

    missing = set(missing_exhibit_ids)
    grounding_ids: list[str] = []
    for exhibit_id in ordered_ids:
        if exhibit_id in missing or exhibit_id in grounding_ids:
            continue
        grounding_ids.append(exhibit_id)
    return grounding_ids


def _find_unsourced_grounding_exhibit_ids(db: Session, exhibit_ids: list[str]) -> list[str]:
    unsourced_exhibit_ids = []
    for exhibit_id in exhibit_ids:
        exhibit = get_exhibit(db, exhibit_id)
        if exhibit is None:
            continue
        if not (exhibit.source_reference or "").strip():
            unsourced_exhibit_ids.append(exhibit_id)
    return unsourced_exhibit_ids


def _build_source_safety_summary(
    db: Session,
    preflight: GeniosPreflightPackage,
    grounding: GeniosGroundingPackage,
) -> GeniosSourceSafetySummary:
    blocking_check_names = [check.name for check in preflight.checks if check.status == "fail"]
    approval_issues = [
        issue
        for exhibit_read in grounding.exhibits
        if (exhibit := get_exhibit(db, exhibit_read.id)) is not None
        if (issue := exhibit_approval_issue(db, exhibit)) is not None
    ]
    if approval_issues:
        blocking_check_names.append("museum_approval")
    ready_for_generation = (
        preflight.ready_for_handoff
        and grounding.grounding_sources_complete
        and not grounding.missing_exhibit_ids
        and not approval_issues
    )

    return GeniosSourceSafetySummary(
        ready_for_generation=ready_for_generation,
        grounding_sources_complete=grounding.grounding_sources_complete,
        source_reference_count=grounding.source_reference_count,
        sourced_exhibit_ids=grounding.sourced_exhibit_ids,
        unsourced_exhibit_ids=grounding.unsourced_exhibit_ids,
        missing_exhibit_ids=grounding.missing_exhibit_ids,
        blocking_check_names=blocking_check_names,
        safety_note=(
            "Grounding source references are complete for generated explanation."
            if ready_for_generation
            else "Resolve failed preflight checks, missing sources, and museum approvals before generated explanation."
        ),
    )
