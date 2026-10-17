# Paired Agent Evaluation

This protocol compares the current single-Agent baseline with an optional independent review-Agent candidate. It does not assume a second Agent is better, and it cannot replace curator approval or an enforced answer-release gateway.

## Run protocol

1. Freeze one approved source-corpus revision, backend revision, model ID, and maximum output-token budget. Record them consistently for every run. Use the same visitor state and tool availability for each matched pair.
2. Run every `evals/curator_cases.json` case in both `canonical` and `paraphrase` variants, three independent repetitions per variant and mode. With eight current cases this requires 96 labeled traces. Randomize the order of the two modes; do not let one mode read the other's answer.
3. Save the authentic, redacted platform trace for every run. A curator checks the visible answer, supporting original source passages, citations and release sequence. Use distinct `trace_ref` values. Do not include API keys, visitor personal data or full answer text in label files.
4. Run the release-trace checker on the underlying trace export. Then compare the human labels with `python scripts/compare_agent_modes.py labels.jsonl`. Missing pairs, repeated trace references, missing labels, and different model/corpus/backend/budget metadata fail validation. A false score is counted as a failed run; it is not silently discarded.
5. Have the museum and project owner sign the acceptance thresholds **before** examining the result. Report per-mode failed runs, median latency, total input/output tokens, and the full individual curator rubric. Only add a second Agent if it meaningfully reduces unsupported answers at acceptable cost and latency. Keep deterministic source/version gates in either architecture.

Each JSONL label is one run. Example shape (illustrative, not an actual evaluation):

```json
{"case_id":"founding_dates","variant_id":"canonical","repetition":1,"mode":"single_agent","model_id":"model-version","corpus_revision":"approved-corpus-v1","backend_revision":"commit-id","max_output_tokens":500,"reviewer":"curator-id","trace_ref":"redacted-trace-001","scores":{"factual_support":true,"citation_support":true,"workflow_compliance":true},"latency_ms":1900,"input_tokens":850,"output_tokens":120}
```

Use `mode="review_agent"` for the matched candidate run. Each required score must be an explicit Boolean. Repetitions are numbered 1 to 3 separately for each variant and mode. The checker verifies label completeness and comparability, not whether a trace was truly exported from Coze or the curator's judgment is correct. Attach the real trace evidence and signed review separately. The existing `score_curator_evaluation.py` remains a simple one-result-per-case release checklist; it is not the paired comparison tool.
