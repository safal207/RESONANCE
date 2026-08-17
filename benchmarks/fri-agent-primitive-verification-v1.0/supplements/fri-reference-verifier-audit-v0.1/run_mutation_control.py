#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
FRI_ROOT = HERE.parents[1]
EVALUATOR_PATH = FRI_ROOT / "run_fri_conformance.py"
AUDIT_FIXTURES = HERE / "fixtures.json"


MUTANTS = [
    {
        "id": "MUT-FRI-2-VACUOUS-HEALTH",
        "description": "Remove the no-activity observability guard so 0 reads / 0 observations can look healthy.",
        "needle": '''        if reads <= 0:\n            return "NOT_OBSERVABLE", "No independent instrumented activity exists, so collector liveness cannot be inferred."\n        if observations == 0:\n''',
        "replacement": '''        if observations == 0 and reads > 0:\n''',
        "must_fail_controls": ["FRI-2C"],
    },
    {
        "id": "MUT-FRI-5-NONE-EQUALS-NONE",
        "description": "Remove the missing-evidence guard so None == None can authorize use.",
        "needle": '''        if verified is None or current is None:\n            return "BLOCK_MISSING_VERIFICATION_EVIDENCE", "Verification/current-state binding is incomplete."\n        if verified == current:\n''',
        "replacement": '''        if verified == current:\n''',
        "must_fail_controls": ["FRI-5C"],
    },
]


def load_evaluate(source: str, module_name: str) -> Callable[[str, dict[str, Any]], tuple[str, str]]:
    namespace: dict[str, Any] = {
        "__name__": module_name,
        "__file__": str(EVALUATOR_PATH),
    }
    exec(compile(source, str(EVALUATOR_PATH), "exec"), namespace)
    evaluate = namespace.get("evaluate")
    if not callable(evaluate):
        raise RuntimeError("mutated module does not expose evaluate()")
    return evaluate


def run_controls(evaluate: Callable[[str, dict[str, Any]], tuple[str, str]], controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for control in controls:
        actual, reason = evaluate(control["rule"], control["input"])
        expected = control["expected"]
        results.append(
            {
                "id": control["id"],
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
                "reason": reason,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove that the FRI verifier self-audit kills known bad verifier mutations."
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = EVALUATOR_PATH.read_text(encoding="utf-8")
    spec = json.loads(AUDIT_FIXTURES.read_text(encoding="utf-8"))
    controls = spec["controls"]

    baseline_results = run_controls(load_evaluate(source, "fri_reference_baseline"), controls)
    baseline_failures = [item["id"] for item in baseline_results if not item["pass"]]
    if baseline_failures:
        report = {
            "benchmark": "FRI Verifier Mutation-Kill Control",
            "version": "0.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL_BASELINE_NOT_GREEN",
            "baseline_failures": baseline_failures,
            "mutants": [],
        }
        text = json.dumps(report, indent=2, sort_keys=True)
        print(text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return 1

    mutant_reports = []
    all_killed = True

    for mutant in MUTANTS:
        count = source.count(mutant["needle"])
        if count != 1:
            mutant_reports.append(
                {
                    "id": mutant["id"],
                    "status": "INVALID_MUTATION_TARGET",
                    "needle_matches": count,
                    "must_fail_controls": mutant["must_fail_controls"],
                }
            )
            all_killed = False
            continue

        mutated_source = source.replace(mutant["needle"], mutant["replacement"], 1)
        results = run_controls(load_evaluate(mutated_source, f'fri_mutant_{mutant["id"]}'), controls)
        failing_controls = [item["id"] for item in results if not item["pass"]]
        required = set(mutant["must_fail_controls"])
        killed = required.issubset(failing_controls)
        all_killed = all_killed and killed

        mutant_reports.append(
            {
                "id": mutant["id"],
                "description": mutant["description"],
                "status": "KILLED" if killed else "SURVIVED",
                "must_fail_controls": mutant["must_fail_controls"],
                "observed_failing_controls": failing_controls,
            }
        )

    report = {
        "benchmark": "FRI Verifier Mutation-Kill Control",
        "version": "0.1",
        "scope": "known semantic regressions only; not a claim of complete mutation adequacy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "killed": sum(item.get("status") == "KILLED" for item in mutant_reports),
            "total": len(mutant_reports),
            "status": "PASS" if all_killed else "FAIL",
        },
        "baseline_audit": "PASS",
        "mutants": mutant_reports,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if all_killed else 1


if __name__ == "__main__":
    raise SystemExit(main())
