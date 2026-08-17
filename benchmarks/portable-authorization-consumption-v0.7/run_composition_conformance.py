#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "fixtures.json"
DEFAULT_ORDER = ["verify_proof", "check_authority", "consume", "dispatch", "bind_outcome"]


def execute(data: dict[str, Any], order: list[str] | None = None) -> tuple[str, list[str], dict[str, Any]]:
    order = list(order or DEFAULT_ORDER)
    effects: list[str] = []
    state = {
        "proof_verified": False,
        "authority_checked": False,
        "consumed": False,
        "dispatch_ref": None,
        "outcome_bound": False,
    }

    for step in order:
        if step == "verify_proof":
            if not bool(data.get("proof_valid")):
                return "BLOCK_INVALID_PROOF", effects, state
            state["proof_verified"] = True

        elif step == "check_authority":
            if not state["proof_verified"]:
                return "BLOCK_PROOF_NOT_ESTABLISHED", effects, state
            if data.get("authority") != "CURRENT":
                return "BLOCK_NOT_CURRENT", effects, state
            state["authority_checked"] = True

        elif step == "consume":
            if not state["proof_verified"] or not state["authority_checked"]:
                # A mutated order that reaches consumption before prior checks is itself unsafe.
                effects.append("CONSUMED_BEFORE_AUTHORITY")
                return "BLOCK_ORDER_VIOLATION", effects, state
            if data.get("spendability") != "UNSPENT":
                return "BLOCK_ALREADY_CONSUMED", effects, state
            state["consumed"] = True
            effects.append("CONSUMED")

        elif step == "dispatch":
            if not state["consumed"]:
                effects.append("DISPATCHED_BEFORE_CONSUMPTION")
                return "BLOCK_ORDER_VIOLATION", effects, state
            if data.get("dispatch_decision_ref") != data.get("decision_ref") or data.get("dispatch_action_digest") != data.get("action_digest"):
                return "BLOCK_DISPATCH_BINDING", effects, state
            state["dispatch_ref"] = "dispatch-1"
            effects.append("DISPATCHED")

        elif step == "bind_outcome":
            if not state["dispatch_ref"]:
                return "BLOCK_MISSING_DISPATCH", effects, state
            if data.get("outcome_dispatch_ref") != state["dispatch_ref"] or data.get("outcome_decision_ref") != data.get("decision_ref"):
                return "BLOCK_OUTCOME_BINDING", effects, state
            state["outcome_bound"] = True
            effects.append("OUTCOME_BOUND")

        else:
            raise ValueError(f"unknown step: {step}")

    return "COMPLETE", effects, state


def run(fixtures_path: Path) -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual, effects, state = execute(fixture["input"])
        verdict_pass = actual == fixture["expected"]
        effects_pass = effects == fixture.get("expected_effects", [])
        results.append({
            "id": fixture["id"],
            "name": fixture["name"],
            "expected": fixture["expected"],
            "actual": actual,
            "expected_effects": fixture.get("expected_effects", []),
            "actual_effects": effects,
            "passed": verdict_pass and effects_pass,
            "state": state,
        })

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "scope": "deterministic composition semantics; not an external-product certification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"passed": passed, "total": total, "status": "PASS" if passed == total else "FAIL"},
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.fixtures)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
