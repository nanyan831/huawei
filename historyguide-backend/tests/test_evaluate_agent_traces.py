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


def _single_call_trace() -> dict:
    return {
        "case_id": "approved-history",
        "expected_decision": "pass",
        "events": [
            {
                "type": "answer_tool",
                "endpoint": "/api/genios/answers/history",
                "status_code": 200,
                "run_id": "run-2",
                "decision": "pass",
                "answer": "Reviewed history answer.",
            },
            {"type": "final_answer", "text": "Reviewed history answer."},
        ],
    }


def test_trace_evaluator_accepts_verified_release() -> None:
    assert evaluate_trace(_trace()) == []


def test_trace_evaluator_accepts_single_call_release_and_block() -> None:
    trace = _single_call_trace()
    assert evaluate_trace(trace) == []
    trace["expected_decision"] = "block"
    trace["events"][0]["decision"] = "block"
    trace["events"][0]["answer"] = "Unable to answer safely."
    trace["events"][1]["text"] = "Unable to answer safely."
    assert evaluate_trace(trace) == []


def test_trace_evaluator_rejects_single_call_bypass_and_tool_failure() -> None:
    trace = _single_call_trace()
    trace["events"][0]["status_code"] = 401
    assert "answer_tool did not return HTTP 200" in evaluate_trace(trace)
    trace["events"][0]["status_code"] = 200
    trace["events"][1]["text"] = "Model wrote its own answer."
    assert "visible answer differs from answer_tool answer" in evaluate_trace(trace)
    trace["events"][1]["text"] = trace["events"][0]["answer"]
    trace["events"].insert(0, {"type": "final_answer", "text": "Unreviewed draft."})
    assert "expected one successful answer_tool followed by one final_answer" in evaluate_trace(trace)


def test_trace_evaluator_accepts_explicit_failure_without_visible_answer() -> None:
    trace = {
        "case_id": "revise-no-release",
        "expected_status_code": 409,
        "events": [
            {
                "type": "answer_tool",
                "endpoint": "/api/genios/answers/history",
                "status_code": 409,
            }
        ],
    }
    assert evaluate_trace(trace) == []
    trace["events"].append({"type": "final_answer", "text": "Unsupported draft."})
    assert "failed answer_tool must not have a visible final_answer" in evaluate_trace(trace)
    trace["events"].pop()
    trace["events"][0]["answer"] = "Unsupported draft."
    assert "failed answer_tool must not release an answer" in evaluate_trace(trace)


def test_trace_evaluator_rejects_non_release_tool_and_mixed_flow() -> None:
    trace = _single_call_trace()
    trace["events"][0]["endpoint"] = "/api/genios/handoff-flat"
    assert "answer_tool endpoint is not a reviewed release endpoint" in evaluate_trace(trace)
    trace = _trace()
    trace["events"].insert(2, _single_call_trace()["events"][0])
    assert "expected one successful answer_tool followed by one final_answer" in evaluate_trace(trace)


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
