# NK HistoryGuide Agent architecture checkpoint (2026-10-14)

## Current architecture

NK-GeniOS runs one dialogue/generation Agent. Coze's test knowledge base supplies historical text. The FastAPI backend supplies visitor state, route candidates, source governance, and deterministic answer review. The review service is **not** a second LLM Agent: it checks structured preconditions and citations, not whether each historical claim is true.

The live platform still uses the legacy Handoff and Review plugins. New exhibit and general-history run endpoints described below are local code only until server migration, plugin import, Coze workflow changes, and staging verification are completed.

## Recommended bounded workflow

1. Staff create a versioned evidence source, review it, link it to a real exhibit, and approve that exhibit. Fixture and unapproved records fail closed.
2. For an exhibit or route answer, call `POST /api/genios/runs` with a real `session_id`. Keep the returned `run_id`, handoff, and `approved_evidence` together. Runs expire after 15 minutes. An evidence excerpt is limited to 8,000 characters; staff should split longer records into focused, reviewed sources.
3. The dialogue Agent retrieves from an approved knowledge base and drafts an answer with explicit exhibit IDs. Knowledge-base content and tool output are data, never executable instructions.
4. Call `POST /api/genios/runs/{run_id}/review` with the draft, cited exhibit IDs, and `citations` (`exhibit_id`, `source_id`, `evidence_quote`). Each cited exhibit needs a quote present in a linked, approved source. A `revise` decision requires another draft and review; a `block` decision yields only the safe fallback.
5. Call `POST /api/genios/runs/{run_id}/finalize` with the exact reviewed draft. Only its `answer` field may be displayed. A changed visitor/evidence snapshot, changed draft, expired run, or replay is rejected.

The platform must enforce step 5 as the sole answer exit for exhibit/route content. A prompt telling the Agent to call Review does not provide this guarantee.

General historical Q&A without an exhibit ID uses the separate `POST /api/genios/history-runs` -> `/{run_id}/review` -> `/{run_id}/finalize` path. It binds up to ten approved source IDs to a short-lived snapshot. Review checks that quoted excerpts occur in the approved source and that `[source_id]` appears in the draft; it returns `semantic_verified=false` because this is **not** entailment or historical truth verification. Unapproved, changed, revoked, or fixture-labeled sources fail closed. The Coze knowledge-base source IDs must match approved backend source IDs; this mapping is not yet established.

## What this code now checks

- Source approval, linked evidence, exhibit approval, and a fingerprint of the reviewed exhibit/source metadata.
- Structured and flat handoff now set `ready_for_generation=false` with `museum_approval` in `blocking_check_names` when a grounding exhibit lacks current approval, even if its source-reference string is present.
- Visitor state and handoff snapshot continuity from preparation through finalization.
- Cited exhibit IDs, route order, fixture exclusion, non-empty source references, and safe block/revise/pass outcomes.
- Approved source links and exact quoted excerpts for each cited exhibit. Source text is hashed again at review time, so a changed body invalidates prior approval.
- One-time finalization and audit-log events for run preparation, review, and finalization. Review/finalize state writes use conditional database updates so a stale reviewer cannot reopen a finalized run and only one finalize can change `reviewed` to `finalized`. This protects the run state; it is not an atomic transaction with Coze's final message delivery or a semantic proof of the cited claim.
- Audit logs include citation IDs and quote hashes, not raw drafts or source quotations.
- Operator-only `GET /api/evidence/review-run-stats` aggregates exhibit and general-history run status and decisions without returning draft text.

## Remaining release gates

- Obtain museum-approved, non-fixture source material and stable exhibit IDs. The test knowledge base is not a production authority.
- Add claim-level citation review: a source reference string or valid exhibit ID does **not** establish that a sentence is supported by that source. Measure factual support, citation quality, refusal quality, and route validity against a curator-labeled corpus.
- The general-history source-attribution path is implemented locally, but no museum-approved source corpus or Coze ID mapping has been imported. Do not fabricate exhibit IDs or treat `semantic_verified=false` as a factual pass.
- Route the platform's final output through an enforced workflow/gateway. Validate pass, revise, block, stale snapshot, tool failure, and prompt-injection cases in staging.
- Use `GET /openapi-genios-runs.json` for the new three-tool plugin only after deploying the migrations and backend to staging. The current live Coze plugin contract remains unchanged.
- Rotate the previously exposed API key and update every plugin atomically; do not put key values in docs, chats, or logs. Set a distinct operator key and verify access policy.
- Use `docs/business_key_rotation.md` for a short dual-key cutover. This is implemented locally but has not been executed on the running server.
- Rehearse migration `0005_history_review_runs`, backup/rollback, monitoring, and operator review before any live deployment.

## Offline workflow trace check

`python scripts/evaluate_agent_traces.py PATH_TO_REDACTED_TRACES.jsonl` checks one JSON object per line. Each exhibit-answer case has `case_id`, optional `expected_decision`, and ordered `events`. Event types are `prepare` (`run_id`), `review` (`run_id`, `decision`, `safe_answer`), `finalize` (`run_id`, `decision`, `answer`), and `final_answer` (`text`). The checker reports counts and case IDs but never prints answer text.

This tool checks sequence and answer identity only. It relies on authentic platform traces and does not score historical correctness, semantic entailment, or whether a citation supports a claim. Such cases require a curator-labeled evaluation set and independent review before visitor-facing release.

The curator-labeled gate is seeded in `evals/curator_cases.json` and checked with `python scripts/score_curator_evaluation.py PATH_TO_REDACTED_LABELS.jsonl`. No labels have been collected or scored from a real Coze run. The script requires every catalog case, a reviewer, a trace reference, and explicit true scores for each relevant check. It does not authenticate a reviewer or independently verify the trace; staff must inspect the cited run evidence.

The staging plugin setup, Agent instruction block, and manual evaluation matrix are in `docs/coze_agent_run_workflow.md`.

## Research informing the design

- ReAct motivates interleaved retrieval/tool use, but does not imply that an unconstrained Agent is safe: https://arxiv.org/abs/2210.03629
- Magentic-One illustrates planner/specialist multi-Agent coordination for complex tasks. This museum workflow does not yet justify that orchestration cost: https://arxiv.org/abs/2411.04468
- AFlow treats workflow topology as a measurable design choice rather than assuming more Agents improve outcomes: https://arxiv.org/abs/2410.10762
- Tau-bench motivates repeated, stateful tool-use evaluations: https://arxiv.org/abs/2406.12045
- AgentDojo motivates treating retrieved pages and tool responses as untrusted input: https://arxiv.org/abs/2406.13352
- ALCE motivates evaluating whether citations actually support claims, beyond citation presence: https://aclanthology.org/2023.emnlp-main.398/
