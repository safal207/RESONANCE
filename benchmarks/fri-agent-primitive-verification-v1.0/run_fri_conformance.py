from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "fixtures.json"


def evaluate(rule: str, data: dict[str, Any]) -> tuple[str, str]:
    if rule == "memory_supersession":
        if data.get("persisted") and data.get("superseded_by"):
            return "BLOCK_CURRENT_AUTHORITY", "Persistence preserves history, not current authority."
        if data.get("persisted"):
            return "ALLOW", "Persisted memory has no declared supersession."
        return "NO_PERSISTED_MEMORY", "No persisted memory record is available to authorize or block."

    if rule == "collector_liveness":
        reads = int(data.get("instrumented_reads", 0))
        observations = int(data.get("observation_records", 0))
        if reads <= 0:
            return "NOT_OBSERVABLE", "No independent instrumented activity exists, so collector liveness cannot be inferred."
        if observations == 0:
            return "LIVENESS_FAILURE", "Independent activity exists while the observation ledger is silent."
        return "HEALTHY", "Independent activity and collector output are both observable."

    if rule == "ownership_epoch":
        if not bool(data.get("delivered")):
            return "BLOCK_NO_DELIVERY", "No delivery occurrence exists to bind to mutation authority."

        required = ("recipient", "recipient_epoch", "current_owner", "current_epoch")
        if any(data.get(key) is None for key in required):
            return "BLOCK_AUTHORITY_UNPROVEN", "Current ownership evidence is incomplete."

        authorized = (
            data.get("recipient") == data.get("current_owner")
            and data.get("recipient_epoch") == data.get("current_epoch")
        )
        if authorized:
            return "ALLOW_MUTATION", "Delivery and current authority agree."
        return "BLOCK_STALE_OWNER", "Delivery is transport evidence, not authority-transfer evidence."

    if rule == "dependency_completion":
        if data.get("label") != "done":
            return "BLOCK_DEPENDENCY_NOT_COMPLETE", "The dependency is not declared complete."
        if data.get("completion_receipt_ref"):
            return "ALLOW_DEPENDENT_TASK", "Completion evidence is present."
        return "BLOCK_MISSING_COMPLETION_EVIDENCE", "A scheduling label is not consequential completion proof."

    if rule == "verify_to_use":
        verified = data.get("verified_state_version")
        current = data.get("current_state_version")
        if verified is None or current is None:
            return "BLOCK_MISSING_VERIFICATION_EVIDENCE", "Verification/current-state binding is incomplete."
        if verified == current:
            return "ALLOW", "The witness still binds to the current state version."
        return "REVALIDATE", "Verification is stale at the point of use."

    if rule == "responsibility_lane":
        if not data.get("memory_recovered"):
            return "BLOCK_NO_RECOVERED_STATE", "No recovered state exists to authorize continuity."
        if data.get("recovered_lane") is None or data.get("current_lane") is None:
            return "BLOCK_LANE_UNPROVEN", "Responsibility-lane evidence is incomplete."
        if data.get("recovered_lane") == data.get("current_lane"):
            return "ALLOW_MATERIAL_ACTION", "State and responsibility continuity both hold."
        return "BLOCK_LANE_MISMATCH", "State continuity and responsibility continuity are independent claims."

    raise ValueError(f"unknown rule: {rule}")


def run(fixtures_path: Path) -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual, reason = evaluate(fixture["rule"], fixture["input"])
        expected = fixture["expected"]
        results.append(
            {
                "scenario_id": fixture["id"],
                "name": fixture["name"],
                "rule": fixture["rule"],
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
                "reason": reason,
                "evidence": fixture["input"],
            }
        )

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "article": spec["article"],
        "scope": "deterministic reference semantics; not a Claude Code certification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "total": total,
            "status": "PASS" if passed == total else "FAIL",
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the RESONANCE FRI-1..FRI-6 conformance fixtures.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output", type=Path, help="Write the JSON evidence artifact.")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    report = run(args.fixtures)
    text = json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2, sort_keys=True)
    print(text)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
