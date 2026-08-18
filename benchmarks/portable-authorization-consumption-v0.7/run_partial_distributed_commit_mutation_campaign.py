#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_partial_distributed_commit_conformance import FIXTURES, evaluate

MUTANTS = [
    {
        "id": "PDC-MUT-1-COORDINATOR-MARKER-IMPLIES-ALL-COMMITTED",
        "mode": "trust_coordinator_commit",
        "description": "Treat coordinator COMMITTED as proof that every participant committed despite contradictory participant evidence.",
    },
    {
        "id": "PDC-MUT-2-UNKNOWN-PARTICIPANT-MEANS-NOT-COMMITTED",
        "mode": "unknown_as_not_committed",
        "description": "Collapse an unknown participant outcome into NOT_COMMITTED and continue recovery without reconciliation.",
    },
    {
        "id": "PDC-MUT-3-SKIP-RECOVERY-REVALIDATION",
        "mode": "skip_revalidation",
        "description": "Complete a missing participant write against a stale joint world without verify-at-use revalidation.",
    },
    {
        "id": "PDC-MUT-4-REWRITE-ALREADY-COMMITTED-PARTICIPANT",
        "mode": "rewrite_committed_participant",
        "description": "Recovery re-emits a write to participant A even though A already has a durable committed receipt.",
    },
    {
        "id": "PDC-MUT-5-IGNORE-PARTICIPANT-RECEIPT-BINDING",
        "mode": "ignore_participant_binding",
        "description": "Accept a committed participant receipt bound to another operation, commit set, or effect.",
    },
    {
        "id": "PDC-MUT-6-INVENT-MISSING-DISTRIBUTED-IDENTITY",
        "mode": "invent_missing_identity",
        "description": "Invent a new operation/idempotency identity after recovery lost the durable distributed identity.",
    },
    {
        "id": "PDC-MUT-7-SKIP-COMPENSATION-AUTHORITY",
        "mode": "skip_compensation_authority",
        "description": "Compensate a partially committed participant without current compensation authority.",
    },
    {
        "id": "PDC-MUT-8-AUTO-COMPENSATE-IRREVERSIBLE",
        "mode": "compensate_irreversible",
        "description": "Pretend an irreversible committed participant can be automatically compensated during coordinator recovery.",
    },
    {
        "id": "PDC-MUT-9-DUPLICATE-RECOVERY-REPLAY",
        "mode": "duplicate_recovery_replay",
        "description": "An already recovered distributed operation emits another participant write instead of replaying the durable outcome.",
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
        "benchmark": "PACC Partial Distributed Commit Mutation Campaign",
        "version": fixture_doc["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "falsification of coordinator/participant evidence collapse, ambiguous participant state, stale recovery, duplicate writes, binding, authority, irreversibility, identity continuity, and replay",
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
