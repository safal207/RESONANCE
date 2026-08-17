#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_concurrency_conformance import DEFAULT_FIXTURES, run

MUTANTS = [
    {
        "id": "CONC-1-NON-ATOMIC-CHECK-THEN-SET",
        "mode": "non_atomic_check_then_set",
        "description": "Both workers trust the same stale UNSPENT pre-read and each performs a consume/dispatch side effect.",
    },
    {
        "id": "CONC-2-DUPLICATE-DISPATCH-ON-REPLAY",
        "mode": "duplicate_dispatch_on_replay",
        "description": "Idempotent replay returns the prior result but incorrectly emits another dispatch side effect.",
    },
    {
        "id": "CONC-3-IDEMPOTENCY-KEY-OMISSION",
        "mode": "idempotency_key_omission",
        "description": "Logical operation identity is discarded, so a same-operation retry cannot replay the committed result.",
    },
    {
        "id": "CONC-4-LOSER-DISPATCH",
        "mode": "loser_dispatch",
        "description": "A losing consume attempt is allowed to dispatch despite receiving ALREADY_CONSUMED.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    baseline = run(args.fixtures, mode="baseline")
    if baseline["summary"]["status"] != "PASS":
        report = {
            "benchmark": "PACC Concurrency Mutation Campaign",
            "version": "0.7",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {"status": "FAIL_BASELINE_NOT_GREEN"},
            "mutants": [],
        }
        text = json.dumps(report, indent=2, sort_keys=True)
        print(text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return 1

    mutants = []
    for mutant in MUTANTS:
        result = run(args.fixtures, mode=mutant["mode"])
        failing = [item["id"] for item in result["results"] if not item["passed"]]
        mutants.append(
            {
                **mutant,
                "status": "KILLED" if failing else "SURVIVED",
                "failing_controls": failing,
            }
        )

    killed = sum(item["status"] == "KILLED" for item in mutants)
    survived = len(mutants) - killed
    score = killed / len(mutants) if mutants else 0.0
    status = "PASS" if survived == 0 and score >= args.required_score else "FAIL"

    report = {
        "benchmark": "PACC Concurrency Mutation Campaign",
        "version": "0.7",
        "scope": "deterministic race falsification for atomic consume, logical-operation idempotency, and winner-only dispatch",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "killed": killed,
            "survived": survived,
            "total": len(mutants),
            "mutation_score": score,
            "required_score": args.required_score,
            "status": status,
        },
        "baseline": baseline["summary"],
        "mutants": mutants,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
