from sqlalchemy.orm import Session

from app.schemas.exhibit import ExhibitCreate
from app.services.exhibit_service import create_exhibit


def seed_exhibit(db_session: Session) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="test-exhibit-001",
            name="Verified Test Exhibit",
            description="A test exhibit record for API verification.",
            period="test-period",
            keywords=["context", "metadata"],
            importance=4,
            people=["Test Person"],
            time_range="test-time-range",
            themes=["visitor-state"],
            source_reference="Test fixture only.",
        ),
    )


def seed_second_exhibit(db_session: Session) -> None:
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="test-exhibit-002",
            name="Second Verified Test Exhibit",
            description="A second test exhibit record for API verification.",
            period="test-period",
            keywords=["context", "route"],
            importance=2,
            people=["Second Person"],
            time_range=None,
            themes=["visitor-state", "route"],
            source_reference="Test fixture only.",
        ),
    )


def test_list_exhibits_returns_seeded_exhibit(client, db_session: Session) -> None:
    seed_exhibit(db_session)

    response = client.get("/api/exhibits")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "test-exhibit-001"
    assert response.json()[0]["importance"] == 4


def test_get_exhibit_by_id(client, db_session: Session) -> None:
    seed_exhibit(db_session)

    response = client.get("/api/exhibits/test-exhibit-001")

    assert response.status_code == 200
    assert response.json()["name"] == "Verified Test Exhibit"
    assert response.json()["keywords"] == ["context", "metadata"]


def test_get_exhibit_returns_404_for_missing_id(client) -> None:
    response = client.get("/api/exhibits/missing-exhibit")

    assert response.status_code == 404
    assert response.json()["detail"] == "Exhibit 'missing-exhibit' was not found."


def test_list_exhibits_filters_by_keyword(client, db_session: Session) -> None:
    seed_exhibit(db_session)

    response = client.get("/api/exhibits?keyword=visitor-state")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["test-exhibit-001"]


def test_list_exhibits_supports_limit_and_offset(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    seed_second_exhibit(db_session)

    response = client.get("/api/exhibits?limit=1&offset=1")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["test-exhibit-002"]


def test_get_exhibit_facets_returns_metadata_counts(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    seed_second_exhibit(db_session)

    response = client.get("/api/exhibits/facets")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["periods"] == [{"value": "test-period", "count": 2}]
    assert body["keywords"][0] == {"value": "context", "count": 2}
    assert {"value": "metadata", "count": 1} in body["keywords"]
    assert {"value": "route", "count": 1} in body["keywords"]
    assert body["people"] == [
        {"value": "Second Person", "count": 1},
        {"value": "Test Person", "count": 1},
    ]
    assert body["themes"][0] == {"value": "visitor-state", "count": 2}


def test_get_exhibit_quality_report_returns_data_quality_issues(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="quality-exhibit-002",
            name="Quality Fixture Exhibit",
            description="A quality report fixture.",
            period="quality-period",
            keywords=[],
            importance=2,
            people=[],
            time_range=None,
            themes=[],
            source_reference=None,
        ),
    )

    response = client.get("/api/exhibits/quality-report")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["source_reference_coverage_percent"] == 50.0
    assert body["importance_distribution"] == [
        {"value": "2", "count": 1},
        {"value": "4", "count": 1},
    ]
    issues = {item["issue"]: item for item in body["issues"]}
    assert issues["missing_source_reference"] == {
        "issue": "missing_source_reference",
        "count": 1,
        "exhibit_ids": ["quality-exhibit-002"],
    }
    assert issues["empty_keywords"]["exhibit_ids"] == ["quality-exhibit-002"]
    assert issues["empty_themes"]["exhibit_ids"] == ["quality-exhibit-002"]
    assert issues["empty_people"]["exhibit_ids"] == ["quality-exhibit-002"]


def test_get_exhibit_source_report_groups_sources_and_flags_unsourced_records(client, db_session: Session) -> None:
    seed_exhibit(db_session)
    seed_second_exhibit(db_session)
    create_exhibit(
        db_session,
        ExhibitCreate(
            id="source-report-unsourced",
            name="Unsourced Fixture Exhibit",
            description="A source report fixture without source reference.",
            period="source-period",
            keywords=["source"],
            importance=1,
            people=[],
            time_range=None,
            themes=["source"],
            source_reference=" ",
        ),
    )

    response = client.get("/api/exhibits/source-report")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["sourced_count"] == 2
    assert body["unsourced_count"] == 1
    assert body["unsourced_exhibit_ids"] == ["source-report-unsourced"]
    assert body["source_references"] == [
        {
            "source_reference": "Test fixture only.",
            "count": 2,
            "exhibit_ids": ["test-exhibit-001", "test-exhibit-002"],
        }
    ]
