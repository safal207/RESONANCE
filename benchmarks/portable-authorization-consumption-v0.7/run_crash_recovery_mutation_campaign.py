#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_crash_recovery_conformance import DEFAULT_FIXTURES, run

MUTANTS = [
    {
        "id": "RECOVERY-1-RECONSUME-AFTER-CRASH",
        "mode": "reconsume_after_crash",
        "description": "Retry creates a second consumption even though the durable consumption receipt already exists.",
    },
    {
        "id": "RECOVERY-2-DUPLICATE-DISPATCH-AFTER-ACK-FAILURE",
        "mode": "duplicate_dispatch_after_ack_failure",
        "description": "A committed dispatch is repeated because acknowledgement delivery failed.",
    },
    {
        "id": "RECOVERY-3-GUESS-THROUGH-LOST-CONSUMPTION-RECEIPT",
        "mode": "guess_through_lost_consumption_receipt",
        "description": "Recovery guesses missing consumption evidence from a dispatch receipt instead of failing closed.",
    },
    {
        "id": "RECOVERY-4-BLIND-DISPATCH-ON-UNKNOWN",
        "mode": "blind_dispatch_on_unknown",
        "description": "Recovery dispatches again when the previous dispatch outcome is unknown instead of reconciling first.",
    },
]


def campaign(fixtures: Path, required_score: float) -> dict[str, Any]:
    baseline = run(fixtures, mode="baseline")
    mutants = []
    killed = 0

    for mutant in MUTANTS:
        report = run(fixtures, mode=mutant["mode"])
        failing_controls = [item["id"] for item in report["results"] if not item["passed"]]
        status = "KILLED" if failing_controls else "SURVIVED"
        killed += int(status == "KILLED")
        mutants.append({
            **mutant,
            "status": status,
            "failing_controls": failing_controls,
        })

    total = len(mutants)
    score = killed / total if total else 1.0
    survived = total - killed
    status = "PASS" if baseline["summary"]["status"] == "PASS" and score >= required_score and survived == 0 else "FAIL"

    return {
        "benchmark": "PACC Crash Recovery Mutation Campaign",
        "version": "0.7",
        "scope": "falsification of crash-after-consume recovery, acknowledgement ambiguity, evidence loss, and unknown dispatch outcome",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": baseline["summary"],
        "summary": {
            "killed": killed,
            "total": total,
            "survived": survived,
            "mutation_score": score,
            "required_score": required_score,
            "status": status,
        },
        "mutants": mutants,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = campaign(args.fixtures, args.required_score)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
