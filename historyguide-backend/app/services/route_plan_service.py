from sqlalchemy.orm import Session

from app.models.visitor_state import VisitorState
from app.schemas.route_plan import RoutePlan, RoutePlanItem
from app.services.exhibit_service import get_exhibit
from app.services.recommendation_service import recommend_exhibits


def build_route_plan(
    db: Session,
    visitor_state: VisitorState,
    *,
    max_items: int = 5,
    approved_only: bool = False,
) -> RoutePlan:
    remaining_budget = visitor_state.remaining_time
    planned_minutes = 0
    items: list[RoutePlanItem] = []

    if remaining_budget <= 0:
        return RoutePlan(
            session_id=visitor_state.session_id,
            remaining_time=visitor_state.remaining_time,
            planned_minutes=planned_minutes,
            items=items,
        )

    recommendations = recommend_exhibits(
        db, visitor_state, limit=max_items * 2, approved_only=approved_only
    )
    for recommendation in recommendations:
        exhibit = get_exhibit(db, recommendation.exhibit_id)
        if exhibit is None:
            continue

        estimated_minutes = estimate_exhibit_minutes(exhibit.importance)
        if planned_minutes + estimated_minutes > remaining_budget:
            continue

        items.append(
            RoutePlanItem(
                order=len(items) + 1,
                exhibit_id=recommendation.exhibit_id,
                name=recommendation.name,
                estimated_minutes=estimated_minutes,
                reason=recommendation.reason,
            )
        )
        planned_minutes += estimated_minutes

        if len(items) >= max_items:
            break

    return RoutePlan(
        session_id=visitor_state.session_id,
        remaining_time=visitor_state.remaining_time,
        planned_minutes=planned_minutes,
        items=items,
    )


def estimate_exhibit_minutes(importance: int) -> int:
    if importance >= 5:
        return 10
    if importance >= 3:
        return 7
    return 5

