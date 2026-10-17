# Web/H5 Integration Checklist

This checklist is for connecting a browser-based Web/H5 client to the NK HistoryGuide backend during a real museum visit. It is a backend integration acceptance checklist only. It does not define frontend screens, does not run RAG, does not generate explanation content, and does not add digital human or AR/VR features.

Use it together with `docs/web_h5_genios_integration.md`, which describes the recommended call sequence.

## 1. Runtime Prerequisites

Confirm these values before browser integration:

- backend base URL
- Web/H5 origin
- `HISTORYGUIDE_CORS_ORIGINS`
- `HISTORYGUIDE_API_KEY`, when the deployment is shared, public, or production-like
- `HISTORYGUIDE_OPERATOR_API_KEY`, when operator endpoints are exposed in a shared or production-like environment
- log mode, preferably `HISTORYGUIDE_LOG_FORMAT=json` in production-like environments

Run:

```powershell
python scripts\validate_runtime_config.py --profile staging
```

Stop integration if the profile reports failed security, CORS, database, or logging checks that apply to the target environment.

## 2. Browser And Header Gate

For an isolated direct-browser staging test, verify that browser requests can reach the backend only when the origin is explicitly allowed:

```text
HISTORYGUIDE_CORS_ORIGINS=https://your-h5-origin.example
```

When API key protection is enabled, the trusted server-side gateway (or GeniOS integration), not visitor-side JavaScript, must include:

```http
X-HistoryGuide-Api-Key: <configured-api-key>
```

Do not place a shared business or operator key in browser code, storage, QR codes, or a public app. The optional session-token gateway in `docs/visitor_gateway.md` is implemented locally but disabled by default and not deployed. A trusted issuer must create the session and grant a scoped token; the browser never sees the backend key. Production still requires HTTPS, audited token delivery, proxy rate limits, Coze model integration and forced final-answer display. CORS is not authentication. Direct-browser tests using the shared key must use only disposable keys in isolated staging and cannot establish production readiness.

Web/H5 may send a stable request id for client/backend log correlation:

```http
X-HistoryGuide-Request-Id: <client-request-id>
```

Every response should return `X-HistoryGuide-Request-Id`. Treat it as troubleshooting metadata only. It is not authentication, visitor identity, historical evidence, source reference, visitor profile data, or GeniOS prompt input.

## 3. Public And Operator Probe Gate

Before creating a visit session, trusted deployment tooling (not the visitor browser) should verify probes and access boundaries:

```http
GET /health
GET /ready
GET /api/system/database
GET /api/system/access-policy
GET /api/system/security-status
```

From trusted operator tooling, send:

```http
X-HistoryGuide-Operator-Key: <configured-operator-key>
```

Expected result:

- `/health` reports the service is alive.
- `/ready` reports database access as ready.
- `/api/system/database` does not expose the full database URL.
- `/api/system/access-policy` reports coarse `public_probe`, `business_api`, `operator_api`, and `local_operator_workflow` groups without exposing key values.
- `/api/system/security-status` reports configured key controls without exposing key values.

## 4. Real Visit Session Gate

Have the trusted gateway create exactly one Visitor State session for one physical visit:

```http
POST /api/visitor-states
```

The request should include:

- `session_id`
- `visitor_type`, one of `freshman`, `alumnus`, or `tourist`
- `current_exhibit`, usually `null` at entry
- `visited_history`, usually `[]` at entry
- `interest`
- `remaining_time`

Then confirm session recovery:

```http
GET /api/visitor-states/{session_id}
```

Do not create a new backend session for every visitor question.

## 5. QR Scan Or Exhibit Selection Gate

Each physical QR scan, NFC tap, or exhibit selection should record a visit event:

```http
POST /api/visitor-states/{session_id}/visit-events
```

The `exhibit_id` must be a stable id from the exhibit database and should match the QR-code or Web/H5 route configuration. Do not use temporary spreadsheet row numbers as exhibit ids.

After recording the event, verify:

```http
GET /api/visitor-states/{session_id}
GET /api/visitor-states/{session_id}/visit-events
GET /api/visitor-states/{session_id}/integrity
```

Expected result:

- `current_exhibit` matches the scanned exhibit.
- `visited_history` includes the scanned exhibit without duplicate additions from repeat scans.
- the visit-event timeline contains the scan.
- integrity checks do not report timeline drift.

## 6. Exhibit Metadata Gate

Before displaying exhibit metadata or asking GeniOS for generated explanation, verify the exhibit record:

```http
GET /api/exhibits/{exhibit_id}
GET /api/exhibits/source-report
GET /api/exhibits/quality-report
```

Expected result:

- the exhibit exists.
- `source_reference` is non-empty for real museum records.
- source and quality reports do not show blockers for the exhibits used in the session.

The backend never creates, infers, rewrites, or fills in missing historical facts.

## 7. Structured Context Gate

For route hints and structured UI state, call:

```http
GET /api/recommendations/{session_id}?limit=3
GET /api/visit-routes/{session_id}/plan?max_items=5
GET /api/visits/{session_id}/summary
```

These responses are structured data only. They are not natural-language museum explanations.

## 8. GeniOS Handoff Gate

Before GeniOS drafts a personalized explanation, the trusted integration should verify:

```http
GET /api/genios/context/{session_id}
GET /api/genios/grounding/{session_id}
GET /api/genios/preflight/{session_id}
GET /api/genios/handoff/{session_id}
```

Generation should proceed only when:

```text
source_safety.ready_for_generation=true
grounding_sources_complete=true
```

Stop generated explanation when:

- `source_safety.ready_for_generation` is `false`
- `grounding_sources_complete` is `false`
- `missing_exhibit_ids` is not empty
- `unsourced_exhibit_ids` is not empty
- preflight reports a failed grounding or integrity check

These are preflight signals, not permission to display a draft. For an exhibit/route answer, require `POST /api/genios/runs` -> `review` -> `finalize`; for general history, use `/api/genios/history-runs` -> `review` -> `finalize`. Only the applicable finalize response's `answer` may reach Web/H5. The forced output workflow/gateway is not yet deployed. GeniOS remains responsible for dialogue, RAG retrieval, knowledge grounding, and drafting.

## 9. Logging Evidence Gate

For every integration run, preserve:

- request URL
- response status
- returned `X-HistoryGuide-Request-Id`
- session id
- scanned exhibit id
- `source_safety.ready_for_generation`
- `grounding_sources_complete`
- run id, review decision, and finalize outcome (no draft or source text in routine logs)
- related centralized request log entry, when available

Use `docs/centralized_logging.md` for JSON log field names and redaction rules.

## 10. Stop Conditions

Stop the Web/H5 integration run and fix data, configuration, or client behavior when:

- CORS does not allow the intended Web/H5 origin.
- protected business APIs return `401`.
- operator endpoints are reachable without the intended operator key in shared environments.
- `POST /api/visitor-states` cannot create or recover one visit session.
- `POST /api/visitor-states/{session_id}/visit-events` cannot record a scan.
- the scanned `exhibit_id` is missing from the exhibit database.
- real exhibit records have empty `source_reference`.
- `source_safety.ready_for_generation=false`.
- `grounding_sources_complete=false`.
- the answer bypasses review/finalize, or review/finalize returns `401`, `409`, timeout, or failure.
- a shared business or operator key is present in visitor-side code or storage.
- request ids are not captured by Web/H5 logs and backend logs.

## 11. Boundary Reminder

This checklist keeps the backend aligned with the NK HistoryGuide positioning: a context-aware AI guide for real museum visits.

Do not use this checklist to expand the backend into:

- a general Nankai history chatbot
- large model training
- a GeniOS replacement
- frontend page implementation
- digital human features
- AR/VR features
- unrelated chat or entertainment features
