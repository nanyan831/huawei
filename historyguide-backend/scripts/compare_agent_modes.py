"""Compare paired, curator-labeled single-Agent and review-Agent runs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median
from typing import Any


MODES = ("single_agent", "review_agent")
PAIR_FIELDS = ("model_id", "corpus_revision", "backend_revision", "max_output_tokens")


def compare_runs(
    catalog: dict[str, Any], records: list[dict[str, Any]], *, repetitions: int = 3
) -> tuple[list[str], dict[str, dict[str, int | float]]]:
    problems: list[str] = []
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases or repetitions < 1:
        return ["catalog and repetitions must be valid"], {}
    required: dict[tuple[str, str], list[str]] = {}
    for case in cases:
        if not isinstance(case, dict):
            return ["catalog case must be an object"], {}
        case_id, checks, variants = case.get("case_id"), case.get("checks"), case.get("variants")
        if not isinstance(case_id, str) or not case_id or not isinstance(checks, list) or not checks:
            return ["catalog case id and checks must be nonempty"], {}
        if not all(isinstance(check, str) and check for check in checks):
            return [f"{case_id}: invalid checks"], {}
        if not isinstance(variants, list) or not variants:
            return [f"{case_id}: variants are required for paired evaluation"], {}
        for variant in variants:
            if not isinstance(variant, dict):
                return [f"{case_id}: variant must be an object"], {}
            variant_id, prompt = variant.get("id"), variant.get("prompt")
            if not isinstance(variant_id, str) or not variant_id or not isinstance(prompt, str) or not prompt:
                return [f"{case_id}: variant id and prompt are required"], {}
            key = (case_id, variant_id)
            if key in required:
                return [f"{case_id}/{variant_id}: duplicate catalog variant"], {}
            required[key] = checks

    indexed: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    trace_refs: set[str] = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            problems.append(f"record {index}: must be an object")
            continue
        case_id, variant_id = record.get("case_id"), record.get("variant_id")
        repetition, mode = record.get("repetition"), record.get("mode")
        if (
            not isinstance(case_id, str)
            or not isinstance(variant_id, str)
            or (case_id, variant_id) not in required
            or not isinstance(repetition, int)
            or isinstance(repetition, bool)
            or not 1 <= repetition <= repetitions
            or mode not in MODES
        ):
            problems.append(f"record {index}: unknown case, variant, repetition or mode")
            continue
        key = (case_id, variant_id, repetition, mode)
        if key in indexed:
            problems.append(f"{key}: duplicate run")
            continue
        indexed[key] = record
        for field in ("reviewer", "trace_ref", "model_id", "corpus_revision", "backend_revision"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                problems.append(f"{key}: {field} is missing")
        trace_ref = record.get("trace_ref")
        if isinstance(trace_ref, str) and trace_ref.strip():
            if trace_ref in trace_refs:
                problems.append(f"{key}: duplicate trace_ref")
            trace_refs.add(trace_ref)
        for field in ("max_output_tokens", "input_tokens", "output_tokens"):
            value = record.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < (1 if field == "max_output_tokens" else 0):
                problems.append(f"{key}: {field} must be a nonnegative integer")
        latency = record.get("latency_ms")
        if (
            not isinstance(latency, (int, float))
            or isinstance(latency, bool)
            or not math.isfinite(latency)
            or latency < 0
        ):
            problems.append(f"{key}: latency_ms must be nonnegative")
        scores = record.get("scores")
        if not isinstance(scores, dict):
            problems.append(f"{key}: scores object is missing")
        else:
            for check in required[(case_id, variant_id)]:
                if not isinstance(scores.get(check), bool):
                    problems.append(f"{key}: {check} must be explicitly true or false")

    for case_id, variant_id in required:
        for repetition in range(1, repetitions + 1):
            pair = [(case_id, variant_id, repetition, mode) for mode in MODES]
            for key in pair:
                if key not in indexed:
                    problems.append(f"{key}: required run is missing")
            if all(key in indexed for key in pair):
                left, right = (indexed[key] for key in pair)
                for field in PAIR_FIELDS:
                    if left.get(field) != right.get(field):
                        problems.append(f"{case_id}/{variant_id}/{repetition}: {field} differs between modes")
    if indexed:
        reference = next(iter(indexed.values()))
        for key, record in indexed.items():
            for field in PAIR_FIELDS:
                if record.get(field) != reference.get(field):
                    problems.append(f"{key}: {field} differs across evaluation runs")
    if problems:
        return problems, {}

    summary: dict[str, dict[str, int | float]] = {}
    for mode in MODES:
        mode_runs = [record for key, record in indexed.items() if key[-1] == mode]
        passing = sum(
            all(record["scores"][check] for check in required[(record["case_id"], record["variant_id"])])
            for record in mode_runs
        )
        summary[mode] = {
            "runs": len(mode_runs),
            "all_checks_passed": passing,
            "failed_runs": len(mode_runs) - passing,
            "median_latency_ms": median(record["latency_ms"] for record in mode_runs),
            "input_tokens": sum(record["input_tokens"] for record in mode_runs),
            "output_tokens": sum(record["output_tokens"] for record in mode_runs),
        }
    return [], summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare paired human-labeled Agent runs; not a release gate.")
    parser.add_argument("results", type=Path, help="Redacted JSONL labels, one run per line.")
    parser.add_argument(
        "--catalog", type=Path,
        default=Path(__file__).resolve().parents[1] / "evals" / "curator_cases.json",
    )
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        records = [json.loads(line) for line in args.results.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    problems, summary = compare_runs(catalog, records, repetitions=args.repetitions)
    for problem in problems:
        print(f"[FAIL] {problem}")
    if problems:
        print(f"Paired comparison incomplete: failures={len(problems)}")
        return 1
    for mode, values in summary.items():
        print(f"{mode}: {json.dumps(values, ensure_ascii=True, sort_keys=True)}")
    print("Comparison is descriptive only; curator-approved release thresholds are still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
