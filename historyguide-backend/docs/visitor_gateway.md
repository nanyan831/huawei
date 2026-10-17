# Session-Scoped Visitor Gateway

The visitor gateway is **off by default** and has not been deployed. It prevents visitor JavaScript from carrying the shared business or operator key. It does not create a public visitor session, call Coze, generate a draft, or provide a production-ready rate limiter.

## Enable In Isolated Staging

Configure a distinct business key and randomly generated visitor signing key of at least 32 bytes (prefer secret files), an explicit browser origin, HTTPS at the trusted reverse proxy, and `HISTORYGUIDE_VISITOR_GATEWAY_ENABLED=true`. `HISTORYGUIDE_VISITOR_TOKEN_TTL_MINUTES` defaults to 120 and must be 5-480. Startup fails if the business or signing key is missing, reused, too short, or the lifetime is out of range. The signing key must remain server-side; changing it invalidates all issued visitor tokens. Do not use a previously exposed business key.

The public-facing reverse proxy must rate-limit visitor routes, cap request sizes, forward only trusted client headers, and protect the business-key grant routes from visitor access. The in-app validator warns that this external evidence is still required. Each signed bearer token is registered by SHA-256 digest in the database; the raw token is never stored there. Grant issuance and both revocation paths commit their audit events in the same transaction; an audit failure rolls back the credential change. A lost token can be revoked by the trusted issuer, while signing-key rotation invalidates all outstanding tokens. Do not put tokens in URLs or analytics logs. Apply migrations through the current head `0007_source_approval_fingerprint` in an isolated staging database before enabling this version of the gateway.

## Trusted Provisioning

1. A trusted kiosk or application server creates a Visitor State via the protected `POST /api/visitor-states` business API. It chooses a unique opaque `session_id` and records the actual visitor type and time budget.
2. The same trusted server calls `POST /api/visitor/grants` with `X-HistoryGuide-Api-Key` and `{"session_id":"..."}`. This returns `access_token` once, `expires_at`, and `Cache-Control: no-store`. Never call this grant route from the Agent prompt or visitor browser.
3. The trusted server delivers the scoped token to the corresponding browser session over HTTPS. Treat it as a short-lived visitor credential, not as a shared API key. Never place it in a public QR code, query string, or persistent browser storage.
4. To end or recover a session, the trusted server calls `POST /api/visitor/grants/revoke` with the business key and `{"session_id":"..."}`. This revokes all issued tokens for that session and returns `revoked_count`. The visitor may also call `POST /api/visitor/revoke` with its bearer token to revoke only that token. A revoked token fails immediately across workers sharing the database.

## Visitor Calls

The browser sends `Authorization: Bearer <access_token>` and never sends `X-HistoryGuide-Api-Key`. The token is bound to exactly one existing `session_id`; visitor routes derive the session from the token and reject a substituted exhibit-answer `session_id` field.

| Route | Result |
| --- | --- |
| `GET /api/visitor/me` | Own visit state |
| `POST /api/visitor/revoke` | Revoke the current token |
| `GET /api/visitor/route` | Route built only from approved, non-fixture exhibits |
| `GET /api/visitor/exhibits/{exhibit_id}` | One approved, non-fixture exhibit |
| `POST /api/visitor/visit-events` | Record an event only for the visitor's session and an approved exhibit |
| `POST /api/visitor/answers/history` | Run approved-source prepare/review/finalize and return only the final extractive answer |
| `POST /api/visitor/answers/exhibit` | Run the same exhibit/route gate using the token-bound session ID |

The answer routes accept an already drafted answer and citations. They do **not** call Coze or retrieve its knowledge base. A trusted integration must supply a draft and enforce that only the returned `answer` is displayed; a user-controlled browser must not be treated as a trusted Agent. `409` or other errors must show a generic safe fallback, never the draft. Exhibit `decision=block` returns only the safe block text. All visitor-token responses use `Cache-Control: no-store`.

Old expired grant rows require a scheduled retention/cleanup policy before production. Revocation is per token or per session; it does not authenticate a physical visitor, and a stolen token can be used until revoked or expired.

## Outstanding Gates

- No Coze model invocation, mandatory platform output workflow, or authentic Coze trace has been integrated.
- No production reverse-proxy rate limit, HTTPS/token-delivery audit, visitor identity policy, or load test has been verified.
- No museum-approved corpus, source-ID mapping, real exhibit approval, key rotation, backup/recovery drill, or staff sign-off has been recorded.
- This gateway uses short-lived bearer ownership, not user accounts or a complete RBAC system. Production remains **NO-GO**.
