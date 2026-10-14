# Museum evidence intake (draft only)

The cleaned public-source package is a research lead, not a curator-approved corpus. Its `manifest.json` says `staff_review_required` and `direct_database_import_allowed=false`; `sources.cleaned.json` lists source metadata and URLs, not the full inspected source text. Do not auto-approve those records or label their knowledge-base chunks as verified museum evidence.

## Operator workflow

1. Open the original university or museum record and capture a focused, exact excerpt. Record a stable source ID that matches the citation ID used in NK-GeniOS, a descriptive title, and the original URI or museum archive reference. Do not use fixture content.
2. Validate up to 20 records with `POST /api/evidence/sources/batch/preview`, check titles, original URIs, excerpt lengths and SHA-256 values, then submit the same reviewed records to `POST /api/evidence/sources/batch`. Preview does not write sources or audit logs and does not reserve IDs; import validates conflicts again. The whole batch is rejected on duplicate IDs and every accepted record starts as `draft`. Source rows and their import audit events commit together; an audit insert failure rolls the batch back. This endpoint does **not** import into the Coze knowledge base or approve material.
3. Inspect `GET /api/evidence/sources?status=draft` and `GET /api/evidence/sources/{source_id}`. The list omits the full text; detail returns it for staff review. Both require `X-HistoryGuide-Operator-Key`.
4. After a museum reviewer has checked the exact text and provenance, approve a source through `POST /api/evidence/sources/{source_id}/approve`. A reviewer name string is recorded for audit but is not identity verification; operational policy must authenticate the actual reviewer separately. Revoked records need new version IDs.
5. Confirm the backend approved ID matches the citation marker exposed to the Agent. For exhibit answers, also link the source to a real exhibit and approve that exhibit. For general history answers, approved sources can be passed to `/api/genios/history-runs` without inventing an exhibit ID.

For staging, run the read-only database check with each Coze citation ID that a test answer requires:

```powershell
python scripts/validate_staging_database.py --require-source-id S01 --require-source-id S02
```

It fails when an ID is missing, draft/revoked, fixture-labeled, lacks review/provenance metadata, or its stored text no longer matches the approval hash. It does not compare Coze's retrieved text to the backend text; inspect an actual Coze trace and the curator-approved original separately. Point the validator at the staging database, never a guessed or stale local file.

Example request body for a staff-curated excerpt (illustrative text only):

```json
{
  "sources": [
    {
      "id": "S01",
      "title": "Reviewed university history excerpt",
      "source_uri": "https://example.edu/original-record",
      "content_text": "Exact excerpt checked against the original record by museum staff."
    }
  ]
}
```

Keep API keys in the deployment secret store, not in JSON, prompts, screenshots, or chat. Never copy the illustrative example into a production knowledge base. A local staff-facing workspace now implements preview, draft import, approval, revocation, and exhibit-source linking at `/operator`; see `docs/operator_workspace.md`. Neither the page nor Coze synchronization has been deployed or accepted by museum staff.

## Intake contract and failures

The JSON API accepts an object with `sources`, as illustrated above. The workspace can also read an array and wrap it before sending the API request; the server does not accept a bare array. Every source must contain only `id`, `title`, `source_uri`, and `content_text`; supplying `status`, reviewer fields, or other extra keys is rejected. IDs use `[A-Za-z0-9][A-Za-z0-9._:-]{0,63}`. Title, URI, and body must be nonblank and at most 200, 2,000, and 100,000 characters respectively. Preserve exact original wording; the backend hashes it and does not retrieve any URI automatically.

All preview, intake, detail, and governance APIs require `X-HistoryGuide-Operator-Key`; a business key cannot authorize staff actions. Missing operator configuration returns 503, missing or invalid authentication returns 401, malformed fields return 422, and duplicate IDs or governance conflicts return 409. The evidence request-body limit is 8 MiB and returns 413 before JSON parsing, including streamed requests without Content-Length. Limits are engineering checks, not approval evidence.

For exhibits, the matching endpoints are `POST /api/evidence/exhibits/batch/preview` and `POST /api/evidence/exhibits/batch`, using `{"exhibits": [...]}`. Import commits exhibit rows and the audit summary in one transaction. Newly imported exhibits have no approval; importing a `source_reference` does not create a source link or prove provenance. Link each required approved source explicitly and then obtain an exhibit approval. Read the current `approval_issue` in `GET /api/evidence/exhibits/{exhibit_id}` after any source or exhibit change: a historical `approved` record alone is not the current safety decision.

## What the operator must retain

Keep the museum's independent approval package: original record/archive reference, excerpt boundaries, date, version, authorization, actual reviewer identity and sign-off, stable backend source ID, Coze document/chunk citation ID, and real exhibit ID where applicable. Current database fields do not enforce all of these records. A reviewer name must be nonblank and at most 80 characters, matching source and exhibit approval storage limits. A typed reviewer name is audit metadata, not proof of identity or a museum signature.

After revocation, retain the old version for audit and create a new source ID for any revised text; revoked sources cannot be reapproved. Recheck linked exhibit gates and prepare a new answer run after approval changes. Do not reuse a stale run or change fixture labels merely to make a validator pass. Local engineering validation is recorded separately in `docs/local_validation_2026-10-14.md`.
