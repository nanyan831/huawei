from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exhibit import Exhibit
from app.schemas.exhibit import (
    ExhibitCreate,
    ExhibitFacetItem,
    ExhibitFacets,
    ExhibitQualityIssue,
    ExhibitQualityReport,
    ExhibitSourceReferenceItem,
    ExhibitSourceReport,
)


def list_exhibits(
    db: Session,
    *,
    keyword: str | None = None,
    period: str | None = None,
    importance_min: int | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Exhibit]:
    statement = select(Exhibit).order_by(Exhibit.importance.desc(), Exhibit.id)

    if period:
        statement = statement.where(Exhibit.period == period)
    if importance_min is not None:
        statement = statement.where(Exhibit.importance >= importance_min)

    exhibits = list(db.scalars(statement).all())
    if keyword:
        normalized = keyword.lower()
        exhibits = [
            exhibit
            for exhibit in exhibits
            if normalized in exhibit.name.lower()
            or normalized in exhibit.description.lower()
            or any(normalized in item.lower() for item in exhibit.keywords)
            or any(normalized in item.lower() for item in exhibit.people)
            or any(normalized in item.lower() for item in exhibit.themes)
        ]
    if offset:
        exhibits = exhibits[offset:]
    if limit is not None:
        exhibits = exhibits[:limit]
    return exhibits


def get_exhibit(db: Session, exhibit_id: str) -> Exhibit | None:
    return db.get(Exhibit, exhibit_id)


def get_exhibit_facets(db: Session) -> ExhibitFacets:
    exhibits = list_exhibits(db)
    return ExhibitFacets(
        total=len(exhibits),
        periods=_count_scalar_values(exhibit.period for exhibit in exhibits),
        keywords=_count_list_values(exhibit.keywords for exhibit in exhibits),
        people=_count_list_values(exhibit.people for exhibit in exhibits),
        themes=_count_list_values(exhibit.themes for exhibit in exhibits),
    )


def get_exhibit_quality_report(db: Session) -> ExhibitQualityReport:
    exhibits = list_exhibits(db)
    total = len(exhibits)
    source_reference_count = sum(1 for exhibit in exhibits if _has_text(exhibit.source_reference))

    issues = [
        _quality_issue(
            "missing_source_reference",
            [exhibit.id for exhibit in exhibits if not _has_text(exhibit.source_reference)],
        ),
        _quality_issue(
            "empty_keywords",
            [exhibit.id for exhibit in exhibits if not _has_nonblank_items(exhibit.keywords)],
        ),
        _quality_issue(
            "empty_themes",
            [exhibit.id for exhibit in exhibits if not _has_nonblank_items(exhibit.themes)],
        ),
        _quality_issue(
            "empty_people",
            [exhibit.id for exhibit in exhibits if not _has_nonblank_items(exhibit.people)],
        ),
    ]

    return ExhibitQualityReport(
        total=total,
        source_reference_coverage_percent=(source_reference_count / total * 100) if total else 0,
        importance_distribution=_count_scalar_values(str(exhibit.importance) for exhibit in exhibits),
        issues=issues,
    )


def get_exhibit_source_report(db: Session) -> ExhibitSourceReport:
    exhibits = list_exhibits(db)
    grouped_sources: dict[str, list[str]] = {}
    unsourced_exhibit_ids: list[str] = []

    for exhibit in exhibits:
        source_reference = exhibit.source_reference.strip() if exhibit.source_reference else ""
        if not source_reference:
            unsourced_exhibit_ids.append(exhibit.id)
            continue
        grouped_sources.setdefault(source_reference, []).append(exhibit.id)

    source_references = [
        ExhibitSourceReferenceItem(
            source_reference=source_reference,
            count=len(exhibit_ids),
            exhibit_ids=sorted(exhibit_ids),
        )
        for source_reference, exhibit_ids in sorted(
            grouped_sources.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
    ]

    return ExhibitSourceReport(
        total=len(exhibits),
        sourced_count=sum(item.count for item in source_references),
        unsourced_count=len(unsourced_exhibit_ids),
        unsourced_exhibit_ids=sorted(unsourced_exhibit_ids),
        source_references=source_references,
    )


def create_exhibit(db: Session, exhibit: ExhibitCreate) -> Exhibit:
    db_exhibit = Exhibit(**exhibit.model_dump())
    db.add(db_exhibit)
    db.commit()
    db.refresh(db_exhibit)
    return db_exhibit


def create_exhibits(db: Session, exhibits: list[ExhibitCreate]) -> list[Exhibit]:
    db_exhibits = [Exhibit(**exhibit.model_dump()) for exhibit in exhibits]
    db.add_all(db_exhibits)
    db.commit()
    for exhibit in db_exhibits:
        db.refresh(exhibit)
    return db_exhibits


def _count_scalar_values(values) -> list[ExhibitFacetItem]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = value.strip() if value else ""
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return _facet_items(counts)


def _count_list_values(values_by_exhibit) -> list[ExhibitFacetItem]:
    counts: dict[str, int] = {}
    for values in values_by_exhibit:
        for value in values or []:
            normalized = value.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
    return _facet_items(counts)


def _facet_items(counts: dict[str, int]) -> list[ExhibitFacetItem]:
    return [
        ExhibitFacetItem(value=value, count=count)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _quality_issue(issue: str, exhibit_ids: list[str]) -> ExhibitQualityIssue:
    return ExhibitQualityIssue(issue=issue, count=len(exhibit_ids), exhibit_ids=sorted(exhibit_ids))


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_nonblank_items(values: list[str]) -> bool:
    return any(value.strip() for value in values or [])
