import json
from pathlib import Path

from scripts.compare_agent_modes import compare_runs, main


CATALOG = {
    "cases": [
        {
            "case_id": "source_check",
            "checks": ["factual_support", "workflow_compliance"],
            "variants": [
                {"id": "canonical", "prompt": "Check this source."},
                {"id": "paraphrase", "prompt": "Verify this citation."},
            ],
        }
    ]
}


def _records():
    records = []
    for variant in ("canonical", "paraphrase"):
        for repetition in (1, 2):
            for mode in ("single_agent", "review_agent"):
                records.append({
                    "case_id": "source_check", "variant_id": variant,
                    "repetition": repetition, "mode": mode,
                    "model_id": "same-model", "corpus_revision": "approved-v1",
                    "backend_revision": "abc123", "max_output_tokens": 500,
                    "reviewer": "curator-a",
                    "trace_ref": f"{variant}-{repetition}-{mode}",
                    "scores": {"factual_support": mode == "review_agent", "workflow_compliance": True},
                    "latency_ms": 200 if mode == "single_agent" else 300,
                    "input_tokens": 100, "output_tokens": 50,
                })
    return records


def test_paired_comparison_reports_failure_rate_and_cost_without_claiming_a_gate() -> None:
    problems, summary = compare_runs(CATALOG, _records(), repetitions=2)
    assert problems == []
    assert summary["single_agent"]["failed_runs"] == 4
    assert summary["review_agent"]["all_checks_passed"] == 4
    assert summary["review_agent"]["median_latency_ms"] == 300
    assert summary["review_agent"]["input_tokens"] == 400


def test_paired_comparison_requires_every_matched_repeated_run() -> None:
    records = _records()[:-1]
    problems, summary = compare_runs(CATALOG, records, repetitions=2)
    assert any("required run is missing" in problem for problem in problems)
    assert summary == {}


def test_paired_comparison_rejects_budget_mismatch_unscored_and_duplicate_trace() -> None:
    records = _records()
    records[1]["max_output_tokens"] = 1000
    records[2]["scores"].pop("factual_support")
    records[3]["trace_ref"] = records[0]["trace_ref"]
    problems, _ = compare_runs(CATALOG, records, repetitions=2)
    assert any("max_output_tokens differs between modes" in problem for problem in problems)
    assert any("factual_support must be explicitly true or false" in problem for problem in problems)
    assert any("duplicate trace_ref" in problem for problem in problems)


def test_paired_comparison_requires_one_corpus_and_model_across_cases() -> None:
    records = _records()
    records[2]["corpus_revision"] = "other-corpus"
    records[3]["corpus_revision"] = "other-corpus"
    problems, _ = compare_runs(CATALOG, records, repetitions=2)
    assert any("corpus_revision differs across evaluation runs" in problem for problem in problems)


def test_paired_comparison_rejects_nonfinite_latency() -> None:
    records = _records()
    records[0]["latency_ms"] = float("nan")
    problems, _ = compare_runs(CATALOG, records, repetitions=2)
    assert any("latency_ms must be nonnegative" in problem for problem in problems)


def test_paired_comparison_cli_does_not_print_answers(tmp_path, capsys) -> None:
    catalog_path = tmp_path / "catalog.json"
    results_path = tmp_path / "labels.jsonl"
    catalog_path.write_text(json.dumps(CATALOG), encoding="utf-8")
    records = _records()
    records[0]["answer"] = "Sensitive answer text"
    results_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
    assert main([str(results_path), "--catalog", str(catalog_path), "--repetitions", "2"]) == 0
    output = capsys.readouterr().out
    assert "single_agent" in output
    assert "review_agent" in output
    assert "Sensitive answer text" not in output


def test_real_catalog_requires_all_96_labeled_traces() -> None:
    catalog_path = Path(__file__).resolve().parents[1] / "evals" / "curator_cases.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    problems, summary = compare_runs(catalog, [], repetitions=3)
    assert len(problems) == 96
    assert summary == {}
