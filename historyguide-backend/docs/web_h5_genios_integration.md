# Web/H5 And GeniOS Integration Sequence

This document describes the recommended integration sequence for a real NK HistoryGuide museum visit. It is a backend integration guide only. The backend does not generate explanation text, and this document does not define a frontend UI, a GeniOS prompt, RAG retrieval logic, digital humans, AR, or VR.

## Integration Boundary

The backend provides:

- structured exhibit records
- Visitor State creation and updates
- exhibit-entry visit events
- recommendation and route candidates
- GeniOS context, grounding, preflight, and handoff packages
- source-safety signals for generated explanation readiness

GeniOS provides:

- dialogue
- RAG retrieval
- knowledge grounding
- generated explanation content
- personalized natural-language responses

Web/H5 provides:

- QR scan or exhibit selection entry
- visitor type and interest collection
- API calls to the backend and GeniOS
- display of exhibit metadata, route hints, and generated GeniOS output

## Required Runtime Settings

Before Web/H5 calls the backend directly from a browser, configure explicit CORS origins:

```text
HISTORYGUIDE_CORS_ORIGINS=http://localhost:5173,https://your-h5-origin.example
```

For shared, public, or production-like deployments, configure:

```text
HISTORYGUIDE_API_KEY=<strong-shared-backend-key>
```

When `HISTORYGUIDE_API_KEY` is set, Web/H5 and GeniOS callers must send:

```http
X-HistoryGuide-Api-Key: <configured-api-key>
```

For log correlation, Web/H5 and GeniOS callers may also send:

```http
X-HistoryGuide-Request-Id: <client-request-id>
```

The backend returns `X-HistoryGuide-Request-Id` on every response. Use it to correlate Web/H5 logs, GeniOS calls, backend request logs, and operator reports. It is not authentication, visitor identity, historical evidence, or prompt input.

## Pre-Visit Data Checks

Run these checks before a demo or museum integration session:

1. Import only verified exhibit seed data.
2. Run the source report.
3. Run the quality report.
4. Confirm database readiness.
5. Confirm GeniOS capability discovery.

Useful endpoints:

```http
GET /ready
GET /api/system/database
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
GET /api/genios/capabilities
```

Do not start generated historical explanation if source reports show unresolved real exhibit source gaps.

## Recommended Visit Flow

### 1. Start A Visit Session

When a visitor enters the experience, Web/H5 creates one Visitor State session:

```http
POST /api/visitor-states
```

Example request:

```json
{
  "session_id": "visit-20260924-001",
  "visitor_type": "tourist",
  "current_exhibit": null,
  "visited_history": [],
  "interest": ["architecture"],
  "remaining_time": 30
}
```

Use one `session_id` for the whole physical visit. Do not create a new session for every question.

### 2. Record QR Scan Or Exhibit Entry

When the visitor scans an exhibit QR code or enters an exhibit zone, Web/H5 records a visit event:

```http
POST /api/visitor-states/{session_id}/visit-events
```

Example request:

```json
{
  "exhibit_id": "fixture-exhibit-001",
  "remaining_time": 25
}
```

This updates `current_exhibit`, appends the exhibit to `visited_history`, and stores a timestamped timeline event.

### 3. Refresh Frontend Context

After a scan, Web/H5 can refresh structured metadata and route hints:

```http
GET /api/visitor-states/{session_id}
GET /api/exhibits/{exhibit_id}
GET /api/recommendations/{session_id}?limit=3
GET /api/visit-routes/{session_id}/plan?max_items=5
```

These responses are structured UI data only. They do not contain generated museum explanation.

### 4. Prepare GeniOS Context

Before GeniOS answers a visitor or generates an exhibit explanation, request:

```http
GET /api/genios/context/{session_id}?recommendation_limit=3
```

Use this package for Visitor State, current exhibit, visited exhibits, visit-event timeline, recommendations, `grounding_exhibit_ids`, missing exhibit ids, and collaboration boundaries.

### 5. Prepare Exhibit-Level Grounding

Use the context package's `grounding_exhibit_ids`, or call the grounding endpoint directly:

```http
GET /api/genios/grounding/{session_id}?recommendation_limit=3
```

GeniOS should use the returned exhibit ids, exhibit records, and source references as exhibit-level RAG seed information. The backend does not retrieve knowledge-base passages.

Generation should pause when:

- `grounding_sources_complete` is `false`
- `unsourced_exhibit_ids` is not empty
- `missing_exhibit_ids` is not empty

### 6. Run Preflight Before Handoff

Before a full GeniOS handoff, run:

```http
GET /api/genios/preflight/{session_id}?recommendation_limit=3
```

Treat failed checks as blockers for generated explanation. Warnings mean the session can continue, but GeniOS should adapt the experience. For example, no visit-event timeline means there may be less visit continuity.

### 7. Use Handoff For One-Call GeniOS Integration

For the normal GeniOS integration path, prefer:

```http
GET /api/genios/handoff/{session_id}?recommendation_limit=3&route_max_items=5
```

The handoff response contains:

- `source_safety`
- `preflight`
- `context`
- `route_plan`
- `visit_summary`
- `handoff_note`

See `docs/api_contract.md` for a complete non-historical fixture handoff response example.

GeniOS should check:

```text
source_safety.ready_for_generation == true
```

before generated explanation. If it is `false`, inspect:

- `source_safety.blocking_check_names`
- `source_safety.unsourced_exhibit_ids`
- `source_safety.missing_exhibit_ids`
- `preflight.checks`

### 8. Continue The Visit

For each new scan or exhibit entry:

1. `POST /api/visitor-states/{session_id}/visit-events`
2. `GET /api/genios/handoff/{session_id}`
3. GeniOS performs RAG and generated explanation only if `source_safety.ready_for_generation` is `true`
4. Web/H5 displays GeniOS output and structured route hints

If the visitor changes interests or remaining time without scanning a new exhibit, update the session:

```http
PATCH /api/visitor-states/{session_id}
```

### 9. End The Visit

At the end of the visit, request:

```http
GET /api/visits/{session_id}/summary
```

This returns structured recap input, including visited exhibits and visit-event timeline data. GeniOS may use it with verified RAG sources to generate a natural-language recap.

## Minimal Happy Path

```text
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/genios/handoff/{session_id}
GeniOS checks source_safety.ready_for_generation
GeniOS performs RAG and generated explanation
GET /api/visit-routes/{session_id}/plan
GET /api/visits/{session_id}/summary
```

## Error Handling Guidance

Missing session:

- Recreate or recover the session with `POST /api/visitor-states`
- Do not ask GeniOS to infer a session from chat history

Missing exhibit reference:

- Treat as data or QR-code configuration error
- Check `missing_exhibit_ids`
- Do not generate historical explanation for that exhibit

Unsourced grounding exhibit:

- Treat as source-safety blocker
- Check `unsourced_exhibit_ids`
- Fix exhibit data before generated explanation

Visitor State integrity failure:

- Inspect `GET /api/visitor-states/{session_id}/integrity`
- Prefer recording future exhibit changes through visit events instead of manually patching `visited_history`

## Integration Rules

- Keep one `session_id` for one physical visit.
- Record physical exhibit movement through visit events.
- Use handoff as the default GeniOS integration endpoint.
- Require `source_safety.ready_for_generation=true` before GeniOS generated explanation.
- Use verified museum data with non-empty `source_reference`.
- Do not make the backend generate explanation text.
- Do not extend this backend into a general Nankai history chatbot.
- Do not add digital human, AR, VR, or unrelated chat features to this backend.
