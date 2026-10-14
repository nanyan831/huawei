# Local Demo Workflow

This workflow demonstrates the backend-only NK HistoryGuide MVP. It uses non-historical fixture data and does not generate museum explanation text.

## 1. Install

```powershell
cd .\historyguide-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 2. Import Fixture Exhibits

```powershell
python scripts\import_exhibits.py data\example_exhibits.fixture.json
```

Expected output:

```text
Imported 2 exhibit records.
```

If the fixture was already imported, duplicate ids are rejected:

```text
Import failed: Exhibit ids already exist in database: fixture-exhibit-001, fixture-exhibit-002
```

## 3. Start The Backend

```powershell
uvicorn app.main:app --reload
```

Use the local base URL:

```text
http://127.0.0.1:8000
```

## 4. Check Health

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
```

## 5. Check Database Status

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/system/database
```

Expected result: the response reports the configured database backend, persistence mode, MVP schema management mode, and migration target without exposing the full database URL.

## 6. List Exhibits

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/exhibits
```

Expected result: the fixture exhibits appear in importance order.

## 7. List Exhibits With Pagination

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/exhibits?limit=1&offset=1"
```

Expected result: the response includes one exhibit after skipping the first matching exhibit.

## 8. Get Exhibit Facets

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/exhibits/facets
```

Expected result: the response includes structured metadata counts for periods, keywords, people, and themes.

## 9. Get Exhibit Quality Report

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/exhibits/quality-report
```

Expected result: the response includes structured metadata completeness checks. It does not verify or generate historical content.

## 10. Get Exhibit Source Report

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/exhibits/source-report
```

Expected result: the response groups exhibits by `source_reference` and lists unsourced exhibit ids for verified data review.

## 11. Create Visitor State

```powershell
$body = @{
  session_id = "demo-session-001"
  visitor_type = "tourist"
  current_exhibit = "fixture-exhibit-001"
  visited_history = @("fixture-exhibit-001")
  interest = @("recommendation")
  remaining_time = 25
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/visitor-states `
  -ContentType "application/json" `
  -Body $body
```

## 12. List Visitor States

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/visitor-states?visitor_type=tourist&limit=10&offset=0"
```

Expected result: the response includes stored tourist visit sessions as structured Visitor State records.

## 13. Get Visitor State Stats

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visitor-states/stats
```

Expected result: the response includes aggregated counts for stored visitor types, current exhibits, interests, and remaining time.

## 14. Get Visitor State Integrity Report

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visitor-states/integrity-report
```

Expected result: the response reports whether Visitor State snapshots and visit-event timelines are structurally aligned.

## 15. Get Recommendations

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/recommendations/demo-session-001
```

Expected result: the backend recommends an unvisited fixture exhibit and returns a structured reason.

## 16. Record A Visit Event

```powershell
$eventBody = @{
  exhibit_id = "fixture-exhibit-002"
  remaining_time = 18
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/visitor-states/demo-session-001/visit-events `
  -ContentType "application/json" `
  -Body $eventBody
```

Expected result: the backend updates `current_exhibit`, appends the exhibit to `visited_history`, and stores the new remaining time.

## 17. Get Visit Event Timeline

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visitor-states/demo-session-001/visit-events
```

Expected result: the response includes timestamped structured visit events for the session.

Optional pagination for longer visit timelines:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/visitor-states/demo-session-001/visit-events?limit=20&offset=0"
```

## 18. Get Per-Session Visitor State Integrity

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visitor-states/demo-session-001/integrity
```

Expected result: the response checks whether this one active Visitor State snapshot and its visit-event timeline are structurally aligned.

## 19. Get Visit Route Plan

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visit-routes/demo-session-001/plan
```

Expected result: the response includes ordered route items selected from unvisited recommendation candidates and fitted within the remaining visit time. It does not perform map navigation or generate explanation text.

## 20. Get GeniOS Capabilities

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/genios/capabilities
```

Expected result: the response describes backend/GeniOS boundaries, supported visitor types, integration workflow, and structured endpoints.

## 21. Get GeniOS Context Package

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/genios/context/demo-session-001
```

Expected result: the response includes Visitor State, current exhibit, visited exhibits, visit-event timeline, recommendation candidates, grounding exhibit ids, missing exhibit ids, and the backend/GeniOS collaboration contract.

## 22. Get GeniOS Grounding Package

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/genios/grounding/demo-session-001
```

Expected result: the response resolves grounding exhibit ids to structured exhibit records and source references for GeniOS exhibit-level RAG preparation. It also reports whether all grounding exhibits include source references.

## 23. Get GeniOS Preflight Package

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/genios/preflight/demo-session-001
```

Expected result: the response reports whether the session is structurally ready for GeniOS handoff, including exhibit-reference checks, grounding source-reference completeness, Visitor State integrity, visit-event availability, and recommendation availability.

## 24. Get GeniOS Handoff Package

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/genios/handoff/demo-session-001
```

Expected result: the response combines source safety, the GeniOS context package, route plan, visit summary, and handoff note. It remains structured data only.

The handoff response also includes `source_safety` and the same preflight readiness structure, so GeniOS can inspect generation readiness from one combined response.

## 25. Get Visit Summary

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/visits/demo-session-001/summary
```

Expected result: the response includes a structured summary of the visit session, including visit-event timeline data. It does not generate a natural-language recap.

## 26. Integration Meaning

Frontend can use:

- exhibit APIs to render exhibit metadata
- exhibit list pagination to browse larger verified datasets
- exhibit facets API to build filters from actual structured data
- exhibit quality report API to inspect source and metadata completeness
- exhibit source report API to review source_reference grouping and unsourced records
- database status API to confirm backend and migration mode before deployment
- Visitor State APIs to record the visit process
- Visitor State list API to inspect or recover stored visit sessions
- Visitor State stats API to inspect aggregate stored session state
- Visitor State integrity report API to compare state snapshots with visit-event timelines
- per-session Visitor State integrity API to check one active visit before handoff or recovery
- visit event API to record QR scan or exhibit-entry events without rebuilding full state
- visit event timeline API to replay recorded exhibit-entry events, with pagination for longer visits
- recommendation API to show next-exhibit candidates
- route plan API to display a simple structured visit sequence
- visit summary API to render or request a final recap from structured state and event timeline data

GeniOS can use:

- GeniOS capabilities API to discover backend boundaries, supported visitor types, and integration workflow
- GeniOS context API as the structured input for dialogue, RAG retrieval, grounding, visit-continuity awareness, and explanation generation
- grounding exhibit ids as exhibit-level RAG seed ids inside the GeniOS context and handoff packages
- GeniOS grounding API to resolve grounding exhibit ids to exhibit records, source references, and source completeness status
- GeniOS preflight API to check session readiness before a structured handoff
- exhibit facets API to inspect available structured metadata before integration
- exhibit quality report API to inspect metadata completeness before integration
- exhibit source report API to inspect source grouping before grounding setup
- GeniOS handoff API to retrieve source safety, preflight, context, route plan, and summary in one backend call
- visit event updates as the state signal before requesting a fresh context package
- visit event timeline API as structured visit continuity input, with pagination for focused review
- Visitor State integrity report API to check context consistency before integration demos
- per-session Visitor State integrity API to check one active session before a GeniOS handoff
- route plan API as structured input for route-aware dialogue decisions
- visit summary API as structured input for a grounded natural-language visit recap that can reflect visit-event continuity

The backend should not be extended into LLM generation, digital humans, AR/VR, or unrelated chat features.
