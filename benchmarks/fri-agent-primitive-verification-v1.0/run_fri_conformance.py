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
        return "ALLOW", "No supersession is declared."

    if rule == "collector_liveness":
        reads = int(data.get("instrumented_reads", 0))
        observations = int(data.get("observation_records", 0))
        if reads > 0 and observations == 0:
            return "LIVENESS_FAILURE", "Independent activity exists while the observation ledger is silent."
        return "HEALTHY", "Observed activity is not inconsistent with collector output."

    if rule == "ownership_epoch":
        authorized = (
            bool(data.get("delivered"))
            and data.get("recipient") == data.get("current_owner")
            and data.get("recipient_epoch") == data.get("current_epoch")
        )
        if authorized:
            return "ALLOW_MUTATION", "Delivery and current authority agree."
        return "BLOCK_STALE_OWNER", "Delivery is transport evidence, not authority-transfer evidence."

    if rule == "dependency_completion":
        if data.get("completion_receipt_ref"):
            return "ALLOW_DEPENDENT_TASK", "Completion evidence is present."
        return "BLOCK_MISSING_COMPLETION_EVIDENCE", "A scheduling label is not consequential completion proof."

    if rule == "verify_to_use":
        if data.get("verified_state_version") == data.get("current_state_version"):
            return "ALLOW", "The witness still binds to the current state version."
        return "REVALIDATE", "Verification is stale at the point of use."

    if rule == "responsibility_lane":
        lane_ok = data.get("recovered_lane") == data.get("current_lane")
        if data.get("memory_recovered") and lane_ok:
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
