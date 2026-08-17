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
REQUIRED_RULES = {f"FRI-{i}" for i in range(1, 7)}


MUTANTS = [
    {
        "id": "MUT-FRI-1-IGNORE-SUPERSESSION",
        "rule": "FRI-1",
        "description": "Ignore supersession and treat any persisted memory as current authority.",
        "needle": '''        if data.get("persisted") and data.get("superseded_by"):\n            return "BLOCK_CURRENT_AUTHORITY", "Persistence preserves history, not current authority."\n        if data.get("persisted"):\n''',
        "replacement": '''        if data.get("persisted"):\n''',
        "must_fail_controls": ["FRI-1A"],
    },
    {
        "id": "MUT-FRI-2-VACUOUS-HEALTH",
        "rule": "FRI-2",
        "description": "Remove the no-activity observability guard so 0 reads / 0 observations can look healthy.",
        "needle": '''        if reads <= 0:\n            return "NOT_OBSERVABLE", "No independent instrumented activity exists, so collector liveness cannot be inferred."\n        if observations == 0:\n''',
        "replacement": '''        if observations == 0 and reads > 0:\n''',
        "must_fail_controls": ["FRI-2C"],
    },
    {
        "id": "MUT-FRI-3-IGNORE-EPOCH",
        "rule": "FRI-3",
        "description": "Authorize by owner identity alone and ignore ownership epoch drift.",
        "needle": '''        authorized = (\n            data.get("recipient") == data.get("current_owner")\n            and data.get("recipient_epoch") == data.get("current_epoch")\n        )\n''',
        "replacement": '''        authorized = data.get("recipient") == data.get("current_owner")\n''',
        "must_fail_controls": ["FRI-3E"],
    },
    {
        "id": "MUT-FRI-4-RECEIPT-OVERRIDES-LABEL",
        "rule": "FRI-4",
        "description": "Let a receipt authorize a dependent task even when the dependency label is not done.",
        "needle": '''        if data.get("label") != "done":\n            return "BLOCK_DEPENDENCY_NOT_COMPLETE", "The dependency is not declared complete."\n        if data.get("completion_receipt_ref"):\n''',
        "replacement": '''        if data.get("label") != "done" and not data.get("completion_receipt_ref"):\n            return "BLOCK_DEPENDENCY_NOT_COMPLETE", "The dependency is not declared complete."\n        if data.get("completion_receipt_ref"):\n''',
        "must_fail_controls": ["FRI-4D"],
    },
    {
        "id": "MUT-FRI-5-NONE-EQUALS-NONE",
        "rule": "FRI-5",
        "description": "Remove the missing-evidence guard so None == None can authorize use.",
        "needle": '''        if verified is None or current is None:\n            return "BLOCK_MISSING_VERIFICATION_EVIDENCE", "Verification/current-state binding is incomplete."\n        if verified == current:\n''',
        "replacement": '''        if verified == current:\n''',
        "must_fail_controls": ["FRI-5C"],
    },
    {
        "id": "MUT-FRI-6-IGNORE-RECOVERY-PRESENCE",
        "rule": "FRI-6",
        "description": "Allow lane equality to authorize action even when no recovered state exists.",
        "needle": '''        if not data.get("memory_recovered"):\n            return "BLOCK_NO_RECOVERED_STATE", "No recovered state exists to authorize continuity."\n        if data.get("recovered_lane") is None or data.get("current_lane") is None:\n''',
        "replacement": '''        if data.get("recovered_lane") is None or data.get("current_lane") is None:\n''',
        "must_fail_controls": ["FRI-6C"],
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
        description="Prove that the FRI verifier self-audit kills one mandatory semantic mutant per FRI rule."
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
            "benchmark": "FRI Verifier Mutation Matrix",
            "version": "0.2",
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

    covered_rules = {mutant["rule"] for mutant in MUTANTS}
    coverage_complete = covered_rules == REQUIRED_RULES
    mutant_reports = []
    all_killed = coverage_complete

    for mutant in MUTANTS:
        count = source.count(mutant["needle"])
        if count != 1:
            mutant_reports.append(
                {
                    "id": mutant["id"],
                    "rule": mutant["rule"],
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
                "rule": mutant["rule"],
                "description": mutant["description"],
                "status": "KILLED" if killed else "SURVIVED",
                "must_fail_controls": mutant["must_fail_controls"],
                "observed_failing_controls": failing_controls,
            }
        )

    killed_count = sum(item.get("status") == "KILLED" for item in mutant_reports)
    total = len(mutant_reports)
    mutation_score = killed_count / total if total else 0.0
    report = {
        "benchmark": "FRI Verifier Mutation Matrix",
        "version": "0.2",
        "scope": "six mandatory semantic mutants, one per FRI rule; not a claim of complete mutation adequacy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "killed": killed_count,
            "total": total,
            "mutation_score": mutation_score,
            "required_score": 1.0,
            "rule_coverage": sorted(covered_rules),
            "coverage_complete": coverage_complete,
            "status": "PASS" if all_killed and mutation_score == 1.0 else "FAIL",
        },
        "baseline_audit": "PASS",
        "mutants": mutant_reports,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
