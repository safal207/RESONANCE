#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def evaluate(rule, data):
    if rule == "antecedent_reachability":
        if data["writes_accepted"] == 0 and data["assertions_reported_pass"] > 0:
            return "REJECT_VACUOUS_PASS"
        return "VALID_TEST_PATH"

    if rule == "discriminating_input":
        observations = data["observations"]
        if observations and all(
            row["colliding_groups"] == row["keys_lost"] for row in observations
        ):
            return "REJECT_NON_DISCRIMINATING_FIXTURE"
        return "DISCRIMINATING_FIXTURE_PRESENT"

    if rule == "live_impact_remeasurement":
        if data["measured_population_generation"] != data["current_population_generation"]:
            return "REMEASURE_REQUIRED"
        return "MEASUREMENT_CURRENT"

    if rule == "effect_ack_split":
        if (
            data["side_effect_committed"]
            and data["process_exit_code"] != 0
            and data["retry_requested"]
            and not data["reconciliation_evidence"]
        ):
            return "RECONCILE_BEFORE_RETRY"
        return "RETRY_STATE_SAFE_OR_NOT_REQUESTED"

    raise ValueError(f"unknown rule: {rule}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixtures", default=str(Path(__file__).with_name("fixtures.json"))
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    spec = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    results = []
    ok = True

    for fixture in spec["fixtures"]:
        actual = evaluate(fixture["rule"], fixture["input"])
        passed = actual == fixture["expected"]
        ok = ok and passed
        results.append(
            {
                "id": fixture["id"],
                "expected": fixture["expected"],
                "actual": actual,
                "pass": passed,
            }
        )
        print(f'{fixture["id"]}: {actual} {"PASS" if passed else "FAIL"}')

    evidence = {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "all_passed": ok,
        "results": results,
    }

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
