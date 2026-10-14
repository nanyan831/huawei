import json

from scripts.score_curator_evaluation import main, score_results


CATALOG = {"cases": [
    {"case_id": "facts", "checks": ["factual_support", "citation_support"]},
    {"case_id": "refusal", "checks": ["safe_behavior"]},
]}


def _results():
    return [
        {
            "case_id": "facts", "reviewer": "curator-a", "trace_ref": "trace-1",
            "scores": {"factual_support": True, "citation_support": True},
        },
        {
            "case_id": "refusal", "reviewer": "curator-a", "trace_ref": "trace-2",
            "scores": {"safe_behavior": True},
        },
    ]


def test_curator_gate_requires_every_case_and_explicit_labels() -> None:
    assert score_results(CATALOG, _results()) == []
    assert "refusal: required case was not evaluated" in score_results(CATALOG, _results()[:1])
    results = _results()
    results[0]["scores"]["citation_support"] = False
    assert "facts: citation_support is not explicitly true" in score_results(CATALOG, results)


def test_curator_gate_requires_reviewer_trace_and_unique_ids() -> None:
    results = _results()
    results[0]["reviewer"] = ""
    results[1]["trace_ref"] = ""
    results.append(results[0])
    problems = score_results(CATALOG, results)
    assert "facts: reviewer is missing" in problems
    assert "refusal: trace_ref is missing" in problems
    assert "facts: duplicate result" in problems
    assert "result case_id must be a string" in score_results(
        CATALOG, [{"case_id": ["facts"]}]
    )


def test_curator_gate_cli_reports_failure_without_answer_content(tmp_path, capsys) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(CATALOG), encoding="utf-8")
    results_path = tmp_path / "labels.jsonl"
    results_path.write_text(json.dumps(_results()[0]), encoding="utf-8")

    assert main([str(results_path), "--catalog", str(catalog_path)]) == 1
    output = capsys.readouterr().out
    assert "required case was not evaluated" in output
    assert "cases=2, submitted=1" in output
