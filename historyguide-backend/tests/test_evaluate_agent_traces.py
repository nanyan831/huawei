import json

from scripts.evaluate_agent_traces import evaluate_jsonl, evaluate_trace, main


def _trace() -> dict:
    return {
        "case_id": "approved-exhibit",
        "expected_decision": "pass",
        "events": [
            {"type": "prepare", "run_id": "run-1"},
            {"type": "review", "run_id": "run-1", "decision": "pass", "safe_answer": "Reviewed answer."},
            {"type": "finalize", "run_id": "run-1", "decision": "pass", "answer": "Reviewed answer."},
            {"type": "final_answer", "text": "Reviewed answer."},
        ],
    }


def test_trace_evaluator_accepts_verified_release() -> None:
    assert evaluate_trace(_trace()) == []


def test_trace_evaluator_accepts_revision_then_reviewed_release() -> None:
    trace = _trace()
    trace["events"].insert(
        1, {"type": "review", "run_id": "run-1", "decision": "revise", "safe_answer": "Revise."}
    )
    assert evaluate_trace(trace) == []


def test_trace_evaluator_rejects_bypass_and_modified_output() -> None:
    trace = _trace()
    trace["events"][-1]["text"] = "Unreviewed answer."
    assert "visible answer differs from finalize answer" in evaluate_trace(trace)
    trace["events"].pop(2)
    assert "expected one prepare, one finalize" in evaluate_trace(trace)[0]


def test_trace_evaluator_rejects_wrong_run_and_unresolved_revision() -> None:
    trace = _trace()
    trace["events"][1]["run_id"] = "run-2"
    trace["events"][1]["decision"] = "revise"
    problems = evaluate_trace(trace)
    assert "review uses a different run_id" in problems
    assert "final review is not pass or block" in problems


def test_trace_evaluator_cli_reports_aggregate_without_answer_text(tmp_path, capsys) -> None:
    path = tmp_path / "traces.jsonl"
    good = _trace()
    bad = _trace()
    bad["case_id"] = "bypass"
    bad["events"][-1]["text"] = "Unreviewed answer."
    path.write_text(json.dumps(good) + "\n" + json.dumps(bad) + "\n", encoding="utf-8")

    assert evaluate_jsonl(path)[:2] == (1, 1)
    assert main([str(path)]) == 1
    output = capsys.readouterr().out
    assert "passed=1, failed=1" in output
    assert "Unreviewed answer." not in output
