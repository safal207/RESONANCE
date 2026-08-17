#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "multi_resource_snapshot_fixtures.json"


def result(status, snapshot_ref, *, new_writes=0, blocked_write=True):
    return {
        "status": status,
        "new_writes": new_writes,
        "blocked_write": blocked_write,
        "used_snapshot_ref": snapshot_ref,
    }


def evaluate(control, mode="baseline"):
    data = control["input"]
    snapshot_ref = data.get("snapshot_ref")
    prior = data.get("prior_action_outcome", "NONE")

    if prior == "COMMITTED":
        if mode == "duplicate_committed_replay":
            return result("JOINT_SNAPSHOT_VALID", snapshot_ref, new_writes=1, blocked_write=False)
        return result("IDEMPOTENT_JOINT_REPLAY", snapshot_ref, new_writes=0, blocked_write=False)

    if prior == "UNKNOWN":
        if mode == "blind_retry_unknown":
            return result("JOINT_SNAPSHOT_VALID", snapshot_ref, new_writes=1, blocked_write=False)
        return result("RECONCILE_JOINT_ACTION_REQUIRED", snapshot_ref)

    if data.get("authority") != "CURRENT" and mode != "skip_authority":
        return result("BLOCK_JOINT_ACTION_NOT_AUTHORIZED", snapshot_ref)

    witness_present = bool(data.get("witness_present"))
    witnesses = data.get("resource_witnesses") or {}
    if not witness_present:
        if mode == "invent_missing_snapshot":
            witnesses = {
                key: {
                    "snapshot_ref": "invented-current-snapshot",
                    "version": value.get("version"),
                    "lineage_ref": value.get("lineage_ref"),
                    "effect_ref": value.get("effect_ref"),
                }
                for key, value in (data.get("current") or {}).items()
            }
            snapshot_ref = "invented-current-snapshot"
        else:
            return result("BLOCK_MISSING_CAUSAL_SNAPSHOT", snapshot_ref)

    current = data.get("current") or {}
    required_resources = {"A", "B"}
    if not required_resources.issubset(witnesses) or not required_resources.issubset(current):
        return result("BLOCK_MISSING_CAUSAL_SNAPSHOT", snapshot_ref)

    witness_snapshot_refs = {witnesses[r].get("snapshot_ref") for r in sorted(required_resources)}
    coherent = len(witness_snapshot_refs) == 1 and snapshot_ref in witness_snapshot_refs
    if not coherent and mode not in {"independent_resource_validation", "accept_mixed_snapshot_refs"}:
        return result("BLOCK_NON_COHERENT_SNAPSHOT", snapshot_ref)

    vector_relation = data.get("vector_relation")
    if vector_relation == "INCOMPARABLE" and mode not in {"independent_resource_validation", "accept_incomparable_clock"}:
        return result("BLOCK_CAUSALLY_INCOMPARABLE", snapshot_ref)

    for resource in sorted(required_resources):
        witness = witnesses[resource]
        now = current[resource]
        version_changed = witness.get("version") != now.get("version")
        if version_changed and not (mode == "ignore_a_version" and resource == "A"):
            return result("REVALIDATE_JOINT_SNAPSHOT", snapshot_ref)

        lineage_changed = witness.get("lineage_ref") != now.get("lineage_ref")
        effect_changed = witness.get("effect_ref") != now.get("effect_ref")
        if (lineage_changed or effect_changed) and not (mode == "ignore_b_lineage" and resource == "B"):
            return result("BLOCK_JOINT_LINEAGE_CHANGED", snapshot_ref)

    if vector_relation not in {"EXACT", "INCOMPARABLE"} and mode != "independent_resource_validation":
        return result("REVALIDATE_JOINT_SNAPSHOT", snapshot_ref)

    return result("JOINT_SNAPSHOT_VALID", snapshot_ref, new_writes=1, blocked_write=False)


def run(mode="baseline"):
    fixture_doc = json.loads(FIXTURES.read_text(encoding="utf-8"))
    results = []
    for control in fixture_doc["controls"]:
        actual = evaluate(control, mode=mode)
        expected = control["expected"]
        results.append({
            "id": control["id"],
            "name": control["name"],
            "actual": actual,
            "expected": expected,
            "passed": actual == expected,
        })
    passed = sum(1 for row in results if row["passed"])
    return {
        "benchmark": "PACC Multi-Resource Causal Snapshot Integrity",
        "version": fixture_doc["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "scope": fixture_doc["scope"],
        "results": results,
        "summary": {
            "status": "PASS" if passed == len(results) else "FAIL",
            "passed": passed,
            "total": len(results),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if report["summary"]["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
