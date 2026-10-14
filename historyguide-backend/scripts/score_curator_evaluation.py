"""Gate a manually labeled, evidence-linked NK HistoryGuide staging evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def score_results(catalog: dict[str, Any], results: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["catalog must contain a nonempty cases list"]
    case_checks: dict[str, list[str]] = {}
    for case in cases:
        if not isinstance(case, dict):
            return ["catalog case must be an object"]
        case_id = case.get("case_id")
        checks = case.get("checks")
        if not isinstance(case_id, str) or not case_id or case_id in case_checks:
            return ["catalog case ids must be unique, nonempty strings"]
        if not isinstance(checks, list) or not checks or not all(isinstance(item, str) for item in checks):
            return [f"{case_id}: checks must be a nonempty string list"]
        case_checks[case_id] = checks

    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            problems.append("result must be an object")
            continue
        case_id = result.get("case_id")
        if not isinstance(case_id, str):
            problems.append("result case_id must be a string")
            continue
        if case_id not in case_checks:
            problems.append(f"unknown case_id: {case_id}")
            continue
        if case_id in seen:
            problems.append(f"{case_id}: duplicate result")
            continue
        seen.add(case_id)
        if not isinstance(result.get("reviewer"), str) or not result["reviewer"].strip():
            problems.append(f"{case_id}: reviewer is missing")
        if not isinstance(result.get("trace_ref"), str) or not result["trace_ref"].strip():
            problems.append(f"{case_id}: trace_ref is missing")
        scores = result.get("scores")
        if not isinstance(scores, dict):
            problems.append(f"{case_id}: scores object is missing")
            continue
        for check in case_checks[case_id]:
            if scores.get(check) is not True:
                problems.append(f"{case_id}: {check} is not explicitly true")
    for case_id in case_checks:
        if case_id not in seen:
            problems.append(f"{case_id}: required case was not evaluated")
    return problems


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    results = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                results.append(json.loads(line))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score human-labeled, evidence-linked staging cases.")
    parser.add_argument("results", type=Path, help="JSONL labels without secrets or visitor PII.")
    parser.add_argument(
        "--catalog", type=Path,
        default=Path(__file__).resolve().parents[1] / "evals" / "curator_cases.json",
    )
    args = parser.parse_args(argv)
    try:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        results = load_jsonl(args.results)
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    problems = score_results(catalog, results)
    print(f"Curator evaluation: cases={len(catalog.get('cases', []))}, submitted={len(results)}, failures={len(problems)}")
    for problem in problems:
        print(f"[FAIL] {problem}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
