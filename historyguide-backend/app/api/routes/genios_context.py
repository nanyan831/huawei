from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.genios_context import (
    GeniosCapabilityPackage,
    GeniosContextPackage,
    GeniosFlatHandoffPackage,
    GeniosGroundingPackage,
    GeniosHandoffPackage,
    GeniosPreflightPackage,
    GeniosReviewRequest,
    GeniosReviewResponse,
)
from app.services.genios_context_service import (
    build_genios_capability_package,
    build_genios_context_package,
    build_genios_grounding_package,
    build_genios_handoff_package,
    build_genios_preflight_package,
    review_genios_answer,
)
from app.services.visitor_state_service import get_visitor_state


router = APIRouter(prefix="/api/genios", tags=["genios"])


@router.get("/capabilities", response_model=GeniosCapabilityPackage)
def read_genios_capabilities() -> GeniosCapabilityPackage:
    return build_genios_capability_package()


@router.get("/context/{session_id}", response_model=GeniosContextPackage)
def read_genios_context(
    session_id: str,
    recommendation_limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> GeniosContextPackage:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_genios_context_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )


@router.get("/grounding/{session_id}", response_model=GeniosGroundingPackage)
def read_genios_grounding(
    session_id: str,
    recommendation_limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> GeniosGroundingPackage:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_genios_grounding_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )


@router.get("/preflight/{session_id}", response_model=GeniosPreflightPackage)
def read_genios_preflight(
    session_id: str,
    recommendation_limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> GeniosPreflightPackage:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_genios_preflight_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
    )


@router.get("/handoff/{session_id}", response_model=GeniosHandoffPackage)
def read_genios_handoff(
    session_id: str,
    recommendation_limit: int = Query(default=3, ge=1, le=10),
    route_max_items: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
) -> GeniosHandoffPackage:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    return build_genios_handoff_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
        route_max_items=route_max_items,
    )


@router.get("/handoff-flat/{session_id}", response_model=GeniosFlatHandoffPackage)
def read_genios_flat_handoff(
    session_id: str,
    recommendation_limit: int = Query(default=3, ge=1, le=10),
    route_max_items: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
) -> GeniosFlatHandoffPackage:
    visitor_state = get_visitor_state(db, session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{session_id}' was not found.",
        )

    handoff = build_genios_handoff_package(
        db,
        visitor_state,
        recommendation_limit=recommendation_limit,
        route_max_items=route_max_items,
    )
    current_exhibit_id = ""
    if handoff.context.current_exhibit is not None:
        current_exhibit_id = handoff.context.current_exhibit.id

    return GeniosFlatHandoffPackage(
        session_id=handoff.session_id,
        ready_for_generation=handoff.source_safety.ready_for_generation,
        grounding_sources_complete=handoff.source_safety.grounding_sources_complete,
        source_reference_count=handoff.source_safety.source_reference_count,
        sourced_exhibit_ids=",".join(handoff.source_safety.sourced_exhibit_ids),
        unsourced_exhibit_ids=",".join(handoff.source_safety.unsourced_exhibit_ids),
        missing_exhibit_ids=",".join(handoff.source_safety.missing_exhibit_ids),
        blocking_check_names=",".join(handoff.source_safety.blocking_check_names),
        visitor_type=handoff.context.visitor_state.visitor_type,
        current_exhibit_id=current_exhibit_id,
        visited_count=handoff.visit_summary.visited_count,
        recommendation_count=len(handoff.context.recommendations),
        recommendation_exhibit_ids=",".join(
            recommendation.exhibit_id for recommendation in handoff.context.recommendations
        ),
        route_exhibit_ids=",".join(item.exhibit_id for item in handoff.route_plan.items),
        planned_minutes=handoff.route_plan.planned_minutes,
        remaining_time=handoff.route_plan.remaining_time,
        handoff_note=handoff.handoff_note,
    )


@router.post("/review", response_model=GeniosReviewResponse)
def review_genios_draft(
    review: GeniosReviewRequest,
    db: Session = Depends(get_db),
) -> GeniosReviewResponse:
    visitor_state = get_visitor_state(db, review.session_id)
    if visitor_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visitor session '{review.session_id}' was not found.",
        )

    return review_genios_answer(db, visitor_state, review)
