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


CANDIDATES = [
    {
        "id": "ORDER-FRI-1-SUPERSESSION-BEFORE-PERSISTENCE",
        "rule": "FRI-1",
        "kind": "guard_precedence",
        "description": "Swap supersession rejection behind generic persisted-memory allow.",
        "needle": '''        if data.get("persisted") and data.get("superseded_by"):\n            return "BLOCK_CURRENT_AUTHORITY", "Persistence preserves history, not current authority."\n        if data.get("persisted"):\n            return "ALLOW", "Persisted memory has no declared supersession."\n''',
        "replacement": '''        if data.get("persisted"):\n            return "ALLOW", "Persisted memory has no declared supersession."\n        if data.get("persisted") and data.get("superseded_by"):\n            return "BLOCK_CURRENT_AUTHORITY", "Persistence preserves history, not current authority."\n''',
    },
    {
        "id": "ORDER-FRI-2-OBSERVATION-BEFORE-REACHABILITY",
        "rule": "FRI-2",
        "kind": "guard_precedence",
        "description": "Check zero observations before proving any instrumented activity occurred.",
        "needle": '''        if reads <= 0:\n            return "NOT_OBSERVABLE", "No independent instrumented activity exists, so collector liveness cannot be inferred."\n        if observations == 0:\n            return "LIVENESS_FAILURE", "Independent activity exists while the observation ledger is silent."\n''',
        "replacement": '''        if observations == 0:\n            return "LIVENESS_FAILURE", "Independent activity exists while the observation ledger is silent."\n        if reads <= 0:\n            return "NOT_OBSERVABLE", "No independent instrumented activity exists, so collector liveness cannot be inferred."\n''',
    },
    {
        "id": "ORDER-FRI-3-AUTHORITY-BEFORE-DELIVERY",
        "rule": "FRI-3",
        "kind": "guard_precedence",
        "description": "Check authority completeness before establishing that a delivery occurrence exists.",
        "needle": '''        if not bool(data.get("delivered")):\n            return "BLOCK_NO_DELIVERY", "No delivery occurrence exists to bind to mutation authority."\n\n        required = ("recipient", "recipient_epoch", "current_owner", "current_epoch")\n        if any(data.get(key) is None for key in required):\n            return "BLOCK_AUTHORITY_UNPROVEN", "Current ownership evidence is incomplete."\n''',
        "replacement": '''        required = ("recipient", "recipient_epoch", "current_owner", "current_epoch")\n        if any(data.get(key) is None for key in required):\n            return "BLOCK_AUTHORITY_UNPROVEN", "Current ownership evidence is incomplete."\n\n        if not bool(data.get("delivered")):\n            return "BLOCK_NO_DELIVERY", "No delivery occurrence exists to bind to mutation authority."\n''',
    },
    {
        "id": "ORDER-FRI-4-RECEIPT-BEFORE-COMPLETION",
        "rule": "FRI-4",
        "kind": "guard_precedence",
        "description": "Allow a completion receipt before proving the dependency is actually declared done.",
        "needle": '''        if data.get("label") != "done":\n            return "BLOCK_DEPENDENCY_NOT_COMPLETE", "The dependency is not declared complete."\n        if data.get("completion_receipt_ref"):\n            return "ALLOW_DEPENDENT_TASK", "Completion evidence is present."\n''',
        "replacement": '''        if data.get("completion_receipt_ref"):\n            return "ALLOW_DEPENDENT_TASK", "Completion evidence is present."\n        if data.get("label") != "done":\n            return "BLOCK_DEPENDENCY_NOT_COMPLETE", "The dependency is not declared complete."\n''',
    },
    {
        "id": "ORDER-FRI-5-EQUALITY-BEFORE-EVIDENCE",
        "rule": "FRI-5",
        "kind": "guard_precedence",
        "description": "Compare versions before proving that both version witnesses exist.",
        "needle": '''        if verified is None or current is None:\n            return "BLOCK_MISSING_VERIFICATION_EVIDENCE", "Verification/current-state binding is incomplete."\n        if verified == current:\n            return "ALLOW", "The witness still binds to the current state version."\n''',
        "replacement": '''        if verified == current:\n            return "ALLOW", "The witness still binds to the current state version."\n        if verified is None or current is None:\n            return "BLOCK_MISSING_VERIFICATION_EVIDENCE", "Verification/current-state binding is incomplete."\n''',
    },
    {
        "id": "ORDER-FRI-6-LANE-EVIDENCE-BEFORE-RECOVERY",
        "rule": "FRI-6",
        "kind": "guard_precedence",
        "description": "Check lane evidence before proving that any recovered state exists.",
        "needle": '''        if not data.get("memory_recovered"):\n            return "BLOCK_NO_RECOVERED_STATE", "No recovered state exists to authorize continuity."\n        if data.get("recovered_lane") is None or data.get("current_lane") is None:\n            return "BLOCK_LANE_UNPROVEN", "Responsibility-lane evidence is incomplete."\n''',
        "replacement": '''        if data.get("recovered_lane") is None or data.get("current_lane") is None:\n            return "BLOCK_LANE_UNPROVEN", "Responsibility-lane evidence is incomplete."\n        if not data.get("memory_recovered"):\n            return "BLOCK_NO_RECOVERED_STATE", "No recovered state exists to authorize continuity."\n''',
    },
    {
        "id": "EQUIV-FRI-3-AUTHORIZED-AND-OPERANDS",
        "rule": "FRI-3",
        "kind": "pure_commutative_boolean",
        "description": "Swap two pure equality operands inside the authorization conjunction.",
        "needle": '''        authorized = (\n            data.get("recipient") == data.get("current_owner")\n            and data.get("recipient_epoch") == data.get("current_epoch")\n        )\n''',
        "replacement": '''        authorized = (\n            data.get("recipient_epoch") == data.get("current_epoch")\n            and data.get("recipient") == data.get("current_owner")\n        )\n''',
        "equivalence_basis": "Commutative AND over pure dict.get equality predicates; operand order has no semantic side effect.",
    },
    {
        "id": "EQUIV-FRI-5-MISSING-OR-OPERANDS",
        "rule": "FRI-5",
        "kind": "pure_commutative_boolean",
        "description": "Swap two pure None checks inside the missing-evidence disjunction.",
        "needle": '''        if verified is None or current is None:\n''',
        "replacement": '''        if current is None or verified is None:\n''',
        "equivalence_basis": "Commutative OR over pure local-variable None checks; operand order has no semantic side effect.",
    },
    {
        "id": "EQUIV-FRI-6-MISSING-OR-OPERANDS",
        "rule": "FRI-6",
        "kind": "pure_commutative_boolean",
        "description": "Swap two pure lane None checks inside the missing-evidence disjunction.",
        "needle": '''        if data.get("recovered_lane") is None or data.get("current_lane") is None:\n''',
        "replacement": '''        if data.get("current_lane") is None or data.get("recovered_lane") is None:\n''',
        "equivalence_basis": "Commutative OR over pure dict.get None predicates; operand order has no semantic side effect.",
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


def run_controls(
    evaluate: Callable[[str, dict[str, Any]], tuple[str, str]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for control in controls:
        actual, reason = evaluate(control["rule"], control["input"])
        expected = control["expected"]
        results.append(
            {
                "id": control["id"],
                "rule": control["rule"],
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
                "reason": reason,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run equivalence-aware order-inversion mutations against the FRI reference verifier."
    )
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = EVALUATOR_PATH.read_text(encoding="utf-8")
    spec = json.loads(AUDIT_FIXTURES.read_text(encoding="utf-8"))
    controls = spec["controls"]

    baseline = run_controls(load_evaluate(source, "fri_order_baseline"), controls)
    baseline_failures = [item["id"] for item in baseline if not item["pass"]]
    if baseline_failures:
        report = {
            "benchmark": "FRI Order-Inversion Mutation Campaign",
            "version": "0.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "status": "FAIL_BASELINE_NOT_GREEN",
                "baseline_failures": baseline_failures,
            },
            "mutants": [],
        }
        text = json.dumps(report, indent=2, sort_keys=True)
        print(text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return 1

    reports = []
    for candidate in CANDIDATES:
        count = source.count(candidate["needle"])
        if count != 1:
            reports.append(
                {
                    "id": candidate["id"],
                    "rule": candidate["rule"],
                    "kind": candidate["kind"],
                    "status": "INVALID",
                    "needle_matches": count,
                    "description": candidate["description"],
                }
            )
            continue

        mutated_source = source.replace(candidate["needle"], candidate["replacement"], 1)
        try:
            mutated_evaluate = load_evaluate(mutated_source, f'fri_order_{candidate["id"]}')
            results = run_controls(mutated_evaluate, controls)
        except Exception as exc:  # fail closed: malformed mutations are not counted as kills
            reports.append(
                {
                    "id": candidate["id"],
                    "rule": candidate["rule"],
                    "kind": candidate["kind"],
                    "status": "INVALID",
                    "description": candidate["description"],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        failing_controls = [item["id"] for item in results if not item["pass"]]
        if failing_controls:
            status = "KILLED"
        elif candidate.get("equivalence_basis"):
            status = "EQUIVALENT"
        else:
            status = "SURVIVED"

        item = {
            "id": candidate["id"],
            "rule": candidate["rule"],
            "kind": candidate["kind"],
            "description": candidate["description"],
            "status": status,
            "failing_controls": failing_controls,
        }
        if candidate.get("equivalence_basis"):
            item["equivalence_basis"] = candidate["equivalence_basis"]
            item["equivalence_scope"] = (
                "Declared pure commutative expression plus agreement across the complete audit fixture domain; "
                "not a theorem for arbitrary side-effecting expressions."
            )
        reports.append(item)

    counts = {state: sum(item["status"] == state for item in reports) for state in ("KILLED", "EQUIVALENT", "SURVIVED", "INVALID")}
    scored_total = counts["KILLED"] + counts["SURVIVED"]
    mutation_score = counts["KILLED"] / scored_total if scored_total else 0.0
    all_rules_with_causal_mutants = sorted({item["rule"] for item in reports if item["status"] in {"KILLED", "SURVIVED"}})

    passed = (
        counts["INVALID"] == 0
        and counts["SURVIVED"] == 0
        and scored_total > 0
        and mutation_score >= args.required_score
    )

    report = {
        "benchmark": "FRI Order-Inversion Mutation Campaign",
        "version": "0.1",
        "scope": (
            "Explicit adjacent-guard precedence inversions plus declared pure commutative reorderings. "
            "EQUIVALENT mutants are excluded from mutation score; unproven no-difference mutants are SURVIVED."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_audit": "PASS",
        "summary": {
            "status": "PASS" if passed else "FAIL",
            "killed": counts["KILLED"],
            "equivalent": counts["EQUIVALENT"],
            "survived": counts["SURVIVED"],
            "invalid": counts["INVALID"],
            "scored_total": scored_total,
            "total_candidates": len(reports),
            "mutation_score": mutation_score,
            "required_score": args.required_score,
            "causal_rule_coverage": all_rules_with_causal_mutants,
        },
        "mutants": reports,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
