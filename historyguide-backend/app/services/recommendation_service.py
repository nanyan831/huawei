from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.exhibit import Exhibit
from app.models.visitor_state import VisitorState
from app.schemas.recommendation import ExhibitRecommendation
from app.services.exhibit_service import get_exhibit, list_exhibits
from app.services.evidence_service import exhibit_approval_issue


VISITOR_TYPE_TERMS: dict[str, list[str]] = {
    "freshman": ["freshman", "orientation", "spirit", "校训", "入学", "精神"],
    "alumnus": ["alumnus", "memory", "campus", "校友", "记忆", "院系"],
    "tourist": ["tourist", "overview", "architecture", "culture", "建筑", "文化"],
}


@dataclass(frozen=True)
class ScoredRecommendation:
    exhibit: Exhibit
    score: int
    reasons: list[str]


def recommend_exhibits(
    db: Session,
    visitor_state: VisitorState,
    *,
    limit: int = 3,
    approved_only: bool = False,
) -> list[ExhibitRecommendation]:
    visited = set(visitor_state.visited_history)
    if visitor_state.current_exhibit:
        visited.add(visitor_state.current_exhibit)

    current_exhibit = (
        get_exhibit(db, visitor_state.current_exhibit)
        if visitor_state.current_exhibit
        else None
    )

    scored = [
        _score_exhibit(exhibit, visitor_state, current_exhibit)
        for exhibit in list_exhibits(db)
        if exhibit.id not in visited
        and (not approved_only or (
            not exhibit.id.startswith("fixture-") and exhibit_approval_issue(db, exhibit) is None
        ))
    ]
    scored.sort(key=lambda item: (-item.score, item.exhibit.id))

    recommendations: list[ExhibitRecommendation] = []
    for priority, item in enumerate(scored[:limit], start=1):
        recommendations.append(
            ExhibitRecommendation(
                exhibit_id=item.exhibit.id,
                name=item.exhibit.name,
                reason="; ".join(item.reasons),
                priority=priority,
            )
        )
    return recommendations


def _score_exhibit(
    exhibit: Exhibit,
    visitor_state: VisitorState,
    current_exhibit: Exhibit | None,
) -> ScoredRecommendation:
    score = exhibit.importance * 10
    reasons = [f"importance level {exhibit.importance}"]
    searchable_text = _searchable_text(exhibit)

    matched_interests = [
        interest
        for interest in visitor_state.interest
        if interest.lower() in searchable_text
    ]
    if matched_interests:
        score += 25 * len(matched_interests)
        reasons.append("matches interests: " + ", ".join(matched_interests))

    visitor_terms = VISITOR_TYPE_TERMS.get(visitor_state.visitor_type, [])
    matched_visitor_terms = [term for term in visitor_terms if term.lower() in searchable_text]
    if matched_visitor_terms:
        score += 10
        reasons.append(f"fits {visitor_state.visitor_type} visitor context")

    if visitor_state.remaining_time <= 15:
        score += exhibit.importance * 3
        reasons.append("prioritized for limited remaining time")

    if current_exhibit and _shares_context(exhibit, current_exhibit):
        score += 5
        reasons.append("continues the current exhibit context")

    reasons.append("not yet visited")
    return ScoredRecommendation(exhibit=exhibit, score=score, reasons=reasons)


def _searchable_text(exhibit: Exhibit) -> str:
    parts = [
        exhibit.name,
        exhibit.description,
        exhibit.period,
        *(exhibit.keywords or []),
        *(exhibit.people or []),
        *(exhibit.themes or []),
    ]
    return " ".join(parts).lower()


def _shares_context(candidate: Exhibit, current: Exhibit) -> bool:
    if candidate.period == current.period:
        return True

    candidate_terms = set(candidate.keywords or []) | set(candidate.themes or [])
    current_terms = set(current.keywords or []) | set(current.themes or [])
    return bool(candidate_terms & current_terms)

