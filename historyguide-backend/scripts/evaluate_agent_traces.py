"""Evaluate redacted GeniOS exhibit-answer traces without contacting the platform."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate_trace(trace: dict[str, Any]) -> list[str]:
    events = trace.get("events")
    if not isinstance(events, list) or not all(isinstance(event, dict) for event in events):
        return ["events must be a list of objects"]
    problems: list[str] = []
    prepares = [(index, event) for index, event in enumerate(events) if event.get("type") == "prepare"]
    reviews = [(index, event) for index, event in enumerate(events) if event.get("type") == "review"]
    finalizes = [(index, event) for index, event in enumerate(events) if event.get("type") == "finalize"]
    answers = [(index, event) for index, event in enumerate(events) if event.get("type") == "final_answer"]
    if len(prepares) != 1 or len(finalizes) != 1 or len(answers) != 1 or not reviews:
        return ["expected one prepare, one finalize, one final_answer, and at least one review"]

    prepare_index, prepare = prepares[0]
    finalize_index, finalize = finalizes[0]
    answer_index, answer = answers[0]
    run_id = prepare.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        problems.append("prepare has no run_id")
    if not (prepare_index < reviews[0][0] <= reviews[-1][0] < finalize_index < answer_index):
        problems.append("tool and answer sequence is not prepare -> review -> finalize -> final_answer")
    for _, review in reviews:
        if review.get("run_id") != run_id:
            problems.append("review uses a different run_id")
            break
    if finalize.get("run_id") != run_id:
        problems.append("finalize uses a different run_id")

    final_review = reviews[-1][1]
    decision = final_review.get("decision")
    if decision not in {"pass", "block"}:
        problems.append("final review is not pass or block")
    if finalize.get("decision") != decision:
        problems.append("finalize decision differs from final review")
    if trace.get("expected_decision") is not None and decision != trace["expected_decision"]:
        problems.append("review decision differs from expected_decision")
    safe_answer = final_review.get("safe_answer")
    released_answer = finalize.get("answer")
    visible_answer = answer.get("text")
    if not isinstance(safe_answer, str) or not isinstance(released_answer, str):
        problems.append("review safe_answer or finalize answer is missing")
    elif safe_answer != released_answer:
        problems.append("finalize answer differs from reviewed safe_answer")
    if not isinstance(visible_answer, str) or visible_answer != released_answer:
        problems.append("visible answer differs from finalize answer")
    return problems


def evaluate_jsonl(path: Path) -> tuple[int, int, list[str]]:
    passed = 0
    failed = 0
    failures: list[str] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                trace = json.loads(line)
            except json.JSONDecodeError:
                failed += 1
                failures.append(f"line {line_number}: invalid JSON")
                continue
            if not isinstance(trace, dict):
                failed += 1
                failures.append(f"line {line_number}: trace must be an object")
                continue
            case_id = str(trace.get("case_id") or f"line {line_number}")
            problems = evaluate_trace(trace)
            if problems:
                failed += 1
                failures.append(f"{case_id}: {'; '.join(problems)}")
            else:
                passed += 1
    return passed, failed, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check redacted GeniOS exhibit-answer workflow traces.")
    parser.add_argument("trace_file", type=Path, help="One JSON object per line; do not include API keys.")
    args = parser.parse_args(argv)
    try:
        passed, failed, failures = evaluate_jsonl(args.trace_file)
    except OSError as exc:
        parser.error(str(exc))
    print(f"Agent workflow traces: passed={passed}, failed={failed}")
    for failure in failures:
        print(f"[FAIL] {failure}")
    return 0 if passed > 0 and failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
