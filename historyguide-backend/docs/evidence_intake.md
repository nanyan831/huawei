# Museum evidence intake (draft only)

The cleaned public-source package is a research lead, not a curator-approved corpus. Its `manifest.json` says `staff_review_required` and `direct_database_import_allowed=false`; `sources.cleaned.json` lists source metadata and URLs, not the full inspected source text. Do not auto-approve those records or label their knowledge-base chunks as verified museum evidence.

## Operator workflow

1. Open the original university or museum record and capture a focused, exact excerpt. Record a stable source ID that matches the citation ID used in NK-GeniOS, a descriptive title, and the original URI or museum archive reference. Do not use fixture content.
2. Submit up to 20 records per `POST /api/evidence/sources/batch`. The whole batch is rejected on duplicate IDs and every accepted record starts as `draft`. This endpoint does **not** import into the Coze knowledge base or approve material.
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

Keep API keys in the deployment secret store, not in JSON, prompts, screenshots, or chat. Never copy the illustrative example into a production knowledge base. The source-intake API is a backend foundation for a later staff UI; no staff-facing upload page or Coze synchronization has been deployed yet.
