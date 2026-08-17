#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_external_effect_conformance import DEFAULT_FIXTURES, run

MUTANTS = [
    {
        "id": "EXT-1-NEW-IDEMPOTENCY-KEY-ON-RETRY",
        "mode": "new_key_on_retry",
        "description": "Retry after timeout/not-found uses a fresh idempotency key and breaks logical-operation identity.",
    },
    {
        "id": "EXT-2-TRUST-TIMEOUT-AS-FAILURE",
        "mode": "trust_timeout_as_failure",
        "description": "Timeout is treated as proof that no external effect occurred, so recovery retries before canonical lookup.",
    },
    {
        "id": "EXT-3-BLIND-RESEND-ON-UNKNOWN",
        "mode": "blind_resend_without_lookup",
        "description": "Unknown external outcome triggers resend instead of fail-closed reconciliation.",
    },
    {
        "id": "EXT-4-WEBHOOK-AS-AUTHORITY",
        "mode": "webhook_as_authority",
        "description": "At-least-once notification is treated as canonical settlement state instead of a trigger for lookup.",
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
        "benchmark": "PACC External Exactly-Once Mutation Campaign",
        "version": "0.7",
        "scope": "falsification of external timeout ambiguity, idempotency continuity, canonical lookup, and notification-vs-authority semantics",
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
