#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_compensation_conformance import DEFAULT_FIXTURES, run

MUTANTS = [
    {
        "id": "COMP-1-COMPENSATE-WITHOUT-TRIGGER",
        "mode": "compensate_without_trigger",
        "description": "A compensation side effect is emitted even though no reversal/settlement-failure trigger exists.",
    },
    {
        "id": "COMP-2-SKIP-COMPENSATION-AUTHORITY",
        "mode": "skip_compensation_authority",
        "description": "Compensation proceeds without current authorization for the reversal action.",
    },
    {
        "id": "COMP-3-IGNORE-COMPENSATION-BINDING",
        "mode": "ignore_compensation_binding",
        "description": "Compensation may target a different original effect than the effect being reversed.",
    },
    {
        "id": "COMP-4-NEW-COMPENSATION-KEY-ON-RETRY",
        "mode": "new_compensation_key_on_retry",
        "description": "A compensation retry changes idempotency identity and can create a second logical reversal.",
    },
    {
        "id": "COMP-5-DUPLICATE-COMPENSATION-AFTER-TIMEOUT",
        "mode": "duplicate_compensation_after_timeout",
        "description": "A committed compensation with lost acknowledgement is emitted again instead of replaying durable evidence.",
    },
    {
        "id": "COMP-6-BLIND-COMPENSATION-ON-UNKNOWN",
        "mode": "blind_compensation_on_unknown",
        "description": "Unknown compensation outcome causes a blind retry instead of reconciliation.",
    },
    {
        "id": "COMP-7-REPLAY-EMITS-DUPLICATE-COMPENSATION",
        "mode": "replay_emits_duplicate_compensation",
        "description": "Same-operation replay emits another compensation side effect instead of returning the prior receipt.",
    },
    {
        "id": "COMP-8-ALLOW-MISSING-COMPENSATION-KEY",
        "mode": "allow_missing_compensation_key",
        "description": "Recovery invents a new compensation identity when the durable idempotency key is missing.",
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
        "benchmark": "PACC Compensation and Reversal Mutation Campaign",
        "version": "0.7",
        "scope": "falsification of unauthorized, unbound, duplicated, and ambiguous compensating actions",
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
