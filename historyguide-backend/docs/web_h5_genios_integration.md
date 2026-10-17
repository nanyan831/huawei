# Web/H5 And GeniOS Integration Sequence

This document describes the visit-state and structured-data integration sequence. Its legacy Handoff examples are not a visitor-facing answer workflow. The backend does not generate explanation text, and this document does not define a frontend UI, a GeniOS prompt, RAG retrieval logic, digital humans, AR, or VR. The required answer-review workflow is in `docs/agent_architecture_2026.md` and `docs/coze_agent_run_workflow.md`; it is not deployed yet.

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
- calls to a trusted server-side gateway for protected backend and GeniOS operations
- display of exhibit metadata, route hints, and only a finalized generated answer

## Required Runtime Settings

For a local or isolated staging browser test that calls the backend directly, configure explicit CORS origins:

```text
HISTORYGUIDE_CORS_ORIGINS=http://localhost:5173,https://your-h5-origin.example
```

For shared, public, or production-like deployments, configure:

```text
HISTORYGUIDE_API_KEY=<strong-shared-backend-key>
```

When `HISTORYGUIDE_API_KEY` is set, the trusted gateway and GeniOS integration must send:

```http
X-HistoryGuide-Api-Key: <configured-api-key>
```

Never embed this shared key or the operator key in visitor JavaScript, HTML, browser storage, QR codes, or a public mobile app. The optional local gateway in `docs/visitor_gateway.md` provides short-lived session-bound visitor tokens, approved exhibit/route reads, visit events, and reviewed-answer release without exposing the business key to the browser. A trusted service must first create the session and grant the token; the gateway does not yet call Coze or implement production reverse-proxy rate limiting. CORS restricts browser origins but does not protect a shared secret. A direct-browser staging test may use only a disposable, isolated test key; it is not a production architecture.

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

When a visitor enters the experience, the trusted gateway creates one Visitor State session on behalf of Web/H5:

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

When the visitor scans an exhibit QR code or enters an exhibit zone, the gateway records a visit event:

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

### 7. Use Handoff For Structured Preflight

For structured visit context, an integration may call:

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

GeniOS should check this preflight signal:

```text
source_safety.ready_for_generation == true
```

before drafting an explanation. It does not authorize displaying that draft. If it is `false`, inspect:

- `source_safety.blocking_check_names`
- `source_safety.unsourced_exhibit_ids`
- `source_safety.missing_exhibit_ids`
- `preflight.checks`

For visitor-facing exhibit or route answers, the trusted integration must use `POST /api/genios/runs`, `POST /api/genios/runs/{run_id}/review`, and `POST /api/genios/runs/{run_id}/finalize` in that order. General history answers use the separate `/api/genios/history-runs` path. The gateway or a mandatory Coze workflow must make the matching `finalize` response's `answer` the only displayed generated answer. On a block, stale snapshot, `401`, `409`, timeout, or tool failure, display only the safe fallback. A prompt instruction or `ready_for_generation=true` alone is insufficient.

### 8. Continue The Visit

For each new scan or exhibit entry:

1. `POST /api/visitor-states/{session_id}/visit-events`
2. `GET /api/genios/handoff/{session_id}`
3. GeniOS drafts with approved sources only if `source_safety.ready_for_generation` is `true`
4. The trusted integration reviews and finalizes the exact draft through the appropriate run path
5. Web/H5 displays only the finalized `answer` and structured route hints

If the visitor changes interests or remaining time without scanning a new exhibit, update the session:

```http
PATCH /api/visitor-states/{session_id}
```

### 9. End The Visit

At the end of the visit, request:

```http
GET /api/visits/{session_id}/summary
```

This returns structured recap input, including visited exhibits and visit-event timeline data. GeniOS may use it with approved RAG sources to draft a natural-language recap. Do not display a generated historical recap without the applicable review and finalize path.

## Minimal Happy Path

```text
POST /api/visitor-states
POST /api/visitor-states/{session_id}/visit-events
GET /api/genios/handoff/{session_id} (structured preflight only)
POST /api/genios/runs -> review -> finalize (exhibit/route answer)
Display only finalize.answer; fail closed on any review/finalize failure
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
- Use handoff for structured visit context, not as the final answer gate.
- Require `source_safety.ready_for_generation=true` before drafting an exhibit explanation; require a successful finalize before display.
- Keep shared business and operator keys out of visitor clients; use a trusted server-side gateway.
- Use verified museum data with non-empty `source_reference`.
- Do not make the backend generate explanation text.
- Do not extend this backend into a general Nankai history chatbot.
- Do not add digital human, AR, VR, or unrelated chat features to this backend.
