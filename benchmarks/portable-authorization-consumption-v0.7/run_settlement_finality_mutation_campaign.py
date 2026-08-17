#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_settlement_finality_conformance import DEFAULT_FIXTURES, run

MUTANTS = [
    {
        "id": "SET-1-ACCEPTED-AS-FINAL",
        "mode": "accepted_as_final",
        "description": "An accepted external request is treated as final before execution, settlement, and finality evidence exist.",
    },
    {
        "id": "SET-2-EXECUTED-AS-SETTLED",
        "mode": "executed_as_settled",
        "description": "Execution is treated as settlement even though the settlement boundary has not been crossed.",
    },
    {
        "id": "SET-3-NOTIFICATION-AS-FINALITY",
        "mode": "notification_as_finality",
        "description": "A notification/webhook claiming finality overrides the canonical settlement state.",
    },
    {
        "id": "SET-4-REISSUE-ON-SETTLEMENT-TIMEOUT",
        "mode": "reissue_on_settlement_timeout",
        "description": "A settlement-status timeout causes a new external effect instead of reconciliation.",
    },
    {
        "id": "SET-5-IGNORE-SETTLEMENT-BINDING",
        "mode": "ignore_settlement_binding",
        "description": "Finality is accepted even when the settlement receipt does not bind the expected effect.",
    },
    {
        "id": "SET-6-IGNORE-NONFINAL-DOWNGRADE",
        "mode": "ignore_nonfinal_downgrade",
        "description": "A prior non-final settlement observation is treated as monotonic and a later downgrade is ignored.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    baseline = run(args.fixtures, mode="baseline")
    mutants = []
    for mutant in MUTANTS:
        report = run(args.fixtures, mode=mutant["mode"])
        failing = [item["id"] for item in report["results"] if not item["passed"]]
        status = "KILLED" if failing else "SURVIVED"
        mutants.append({**mutant, "status": status, "failing_controls": failing})

    killed = sum(item["status"] == "KILLED" for item in mutants)
    total = len(mutants)
    survived = total - killed
    score = killed / total if total else 1.0
    baseline_ok = baseline["summary"]["status"] == "PASS"
    status = "PASS" if baseline_ok and survived == 0 and score >= args.required_score else "FAIL"

    result = {
        "benchmark": "PACC Settlement and Finality Mutation Campaign",
        "version": "0.7",
        "scope": "falsification of premature finality, settlement-boundary collapse, notification authority, retry after status ambiguity, receipt misbinding, and pre-finality downgrade handling",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": baseline["summary"],
        "mutants": mutants,
        "summary": {
            "killed": killed,
            "survived": survived,
            "total": total,
            "mutation_score": score,
            "required_score": args.required_score,
            "status": status,
        },
    }

    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
