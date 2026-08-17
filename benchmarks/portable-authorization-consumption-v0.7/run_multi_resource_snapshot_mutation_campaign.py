#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_multi_resource_snapshot_conformance import FIXTURES, evaluate

MUTANTS = [
    {
        "id": "SNAP-MUT-1-INDEPENDENT-RESOURCE-VALIDATION",
        "mode": "independent_resource_validation",
        "description": "Validate A and B independently and ignore whether they form one causal snapshot.",
    },
    {
        "id": "SNAP-MUT-2-IGNORE-A-VERSION-DRIFT",
        "mode": "ignore_a_version",
        "description": "Ignore version drift on resource A while trusting the old joint snapshot.",
    },
    {
        "id": "SNAP-MUT-3-IGNORE-B-LINEAGE-DRIFT",
        "mode": "ignore_b_lineage",
        "description": "Ignore causal lineage/effect drift on resource B when the version still matches.",
    },
    {
        "id": "SNAP-MUT-4-ACCEPT-INCOMPARABLE-CLOCK",
        "mode": "accept_incomparable_clock",
        "description": "Treat causally incomparable resource frontiers as one coherent snapshot.",
    },
    {
        "id": "SNAP-MUT-5-INVENT-MISSING-SNAPSHOT",
        "mode": "invent_missing_snapshot",
        "description": "Reconstruct a missing durable joint snapshot witness from current per-resource state.",
    },
    {
        "id": "SNAP-MUT-6-ACCEPT-MIXED-SNAPSHOT-REFS",
        "mode": "accept_mixed_snapshot_refs",
        "description": "Accept resource witnesses captured under different snapshot identities.",
    },
    {
        "id": "SNAP-MUT-7-SKIP-JOINT-AUTHORITY",
        "mode": "skip_authority",
        "description": "Treat a valid causal snapshot as authority to perform the joint consequential action.",
    },
    {
        "id": "SNAP-MUT-8-DUPLICATE-COMMITTED-REPLAY",
        "mode": "duplicate_committed_replay",
        "description": "Emit another multi-resource write when the same logical joint action was already committed.",
    },
    {
        "id": "SNAP-MUT-9-BLIND-RETRY-UNKNOWN",
        "mode": "blind_retry_unknown",
        "description": "Retry an ambiguous prior joint write instead of reconciling its outcome first.",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output")
    args = parser.parse_args()

    fixture_doc = json.loads(Path(FIXTURES).read_text(encoding="utf-8"))
    controls = fixture_doc["controls"]
    rows = []

    for mutant in MUTANTS:
        failing_controls = []
        for control in controls:
            actual = evaluate(control, mode=mutant["mode"])
            if actual != control["expected"]:
                failing_controls.append(control["id"])
        rows.append({
            **mutant,
            "failing_controls": failing_controls,
            "status": "KILLED" if failing_controls else "SURVIVED",
        })

    killed = sum(1 for row in rows if row["status"] == "KILLED")
    survived = sum(1 for row in rows if row["status"] == "SURVIVED")
    total = len(rows)
    score = killed / total if total else 0.0
    status = "PASS" if survived == 0 and score >= args.required_score else "FAIL"

    report = {
        "benchmark": "PACC Multi-Resource Causal Snapshot Mutation Campaign",
        "version": fixture_doc["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "falsification of write-skew, mixed-snapshot reads, causal incomparability, stale resource evidence, joint authority, idempotency, and ambiguous joint-write recovery",
        "mutants": rows,
        "summary": {
            "status": status,
            "killed": killed,
            "survived": survived,
            "total": total,
            "mutation_score": score,
            "required_score": args.required_score,
        },
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
