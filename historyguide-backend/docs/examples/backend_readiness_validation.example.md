# Backend Readiness Validation Example

This example shows how an operator can record output from `scripts\validate_backend_readiness.py` before a production-like handoff, public demo, museum-site rehearsal, or real visitor-facing backend run.

This example uses placeholder values only. It is not evidence that any real staging, production-like, or museum deployment has been validated.

The validator is read-only backend validation. It does not write to the database, does not print key values, does not validate historical accuracy, does not run RAG, does not generate explanation content, does not train models, does not define GeniOS prompts, does not implement digital humans, does not implement AR/VR, and does not replace museum or expert review.

## Run Metadata

- date: 2026-09-27
- operator: example-operator
- environment: staging-example
- backend base URL: `https://staging-historyguide.example.test`
- backend version or source revision: `example-revision-001`
- database URL label, not secret: `staging-postgres-example`
- Web/H5 origin: `https://museum-h5.example.test`
- GeniOS environment: `genios-staging-example`
- session id: `staging-session-001`
- final decision: proceed_with_warnings
- note: placeholder values only

## Runtime Command

```powershell
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Example output summary:

```text
[PASS] readiness status=200 request_id=example-readiness-001 status_value=ready database=ok
[PASS] database_status status=200 request_id=example-database-001 backend=postgresql persistence=network
[PASS] operational_alerts status=200 request_id=example-alerts-001 severity=ok blocking_check_names=[]
[PASS] exhibit_source_report status=200 request_id=example-source-001 total_exhibits=42 unsourced_exhibit_ids=[]
[PASS] exhibit_quality_report status=200 request_id=example-quality-001 missing_exhibit_ids=[] blocking_check_names=[]
[PASS] audit_log_stats status=200 request_id=example-audit-001 total_logs=18
```

Record:

- `request_id=example-readiness-001`
- `blocking_check_names=[]`
- `unsourced_exhibit_ids=[]`
- `missing_exhibit_ids=[]`
- backend readiness validation result: pass

## Visit Session Command

```powershell
python scripts\validate_backend_readiness.py --base-url https://staging-historyguide.example.test --api-key <business-key> --operator-key <operator-key> --session-id staging-session-001 --require-visit-events --require-exhibits --require-sourced-exhibits --require-audit-logs --require-clean-operational-alerts
```

Example output summary:

```text
[PASS] visitor_state_integrity status=200 request_id=example-integrity-001 issue_count=0
[PASS] visit_events status=200 request_id=example-events-001 event_count=3
[PASS] recommendations status=200 request_id=example-recommendations-001 recommendation_count=2
[PASS] route_plan status=200 request_id=example-route-001 route_item_count=2
[PASS] visit_summary status=200 request_id=example-summary-001 visited_count=3
[PASS] genios_grounding status=200 request_id=example-grounding-001 grounding_sources_complete=True missing_exhibit_ids=[] unsourced_exhibit_ids=[]
[PASS] genios_preflight status=200 request_id=example-preflight-001 source_safety.ready_for_generation=True
[PASS] genios_handoff status=200 request_id=example-handoff-001 source_safety.ready_for_generation=True grounding_sources_complete=True
```

Record:

- `request_id=example-handoff-001`
- `source_safety.ready_for_generation=True`
- `grounding_sources_complete=True`
- `missing_exhibit_ids=[]`
- `unsourced_exhibit_ids=[]`
- generated explanation display allowed by backend source-safety gate: no; preflight alone is insufficient without successful review/finalize
- GeniOS consumed backend handoff package: example placeholder, not verified

## Evidence Package Notes

Attach this record to:

- `docs/operator_evidence_package_checklist.md`
- `docs/production_readiness_decision_checklist.md`
- `docs/staging_validation_record.md`
- `docs/genios_handoff_evidence_template.md` when GeniOS generated explanation may be displayed

Do not attach secret values. Keep only command names, endpoint names, request ids, pass/fail summaries, and source-safety fields.

## Stop Conditions

Block or escalate when any output includes:

- `[FAIL] readiness`
- `[FAIL] database_status`
- `[FAIL] operational_alerts`
- `[FAIL] exhibit_source_report`
- `[FAIL] audit_log_stats`
- `[FAIL] visitor_state_integrity`
- `[FAIL] genios_grounding`
- `[FAIL] genios_preflight`
- `[FAIL] genios_handoff`
- `source_safety.ready_for_generation=False`
- `grounding_sources_complete=False`
- non-empty `missing_exhibit_ids`
- non-empty `unsourced_exhibit_ids`
- non-empty `blocking_check_names`

## Boundary Reminder

This example records backend operational evidence only. It does not validate historical interpretation, does not approve source packages, does not define generated explanation wording, and does not certify Web/H5 or GeniOS production readiness outside the backend integration contract.
