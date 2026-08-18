#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_split_brain_fencing_conformance import run

MUTANTS = [
    {
        "id": "SBF-MUT-1-IGNORE-RECOVERY-EPOCH",
        "mode": "ignore_epoch",
        "description": "Allow a coordinator from an older recovery epoch to perform a new participant write after takeover.",
    },
    {
        "id": "SBF-MUT-2-IGNORE-FENCING-TOKEN",
        "mode": "ignore_token",
        "description": "Treat epoch equality as sufficient and ignore the fencing token presented at consequential use.",
    },
    {
        "id": "SBF-MUT-3-IDENTITY-IMPLIES-OWNERSHIP",
        "mode": "identity_implies_ownership",
        "description": "Treat the same coordinator identity as current ownership even when its recovery session epoch is stale.",
    },
    {
        "id": "SBF-MUT-4-IGNORE-CURRENT-COORDINATOR-IDENTITY",
        "mode": "ignore_coordinator_identity",
        "description": "Allow a different coordinator identity to act using another coordinator's current fencing token.",
    },
    {
        "id": "SBF-MUT-5-INVENT-MISSING-FENCE",
        "mode": "invent_missing_fence",
        "description": "Invent fencing evidence from current metadata when durable recovery fencing evidence is missing.",
    },
    {
        "id": "SBF-MUT-6-IGNORE-FENCING-BINDING",
        "mode": "ignore_fencing_binding",
        "description": "Accept a fencing token bound to another distributed operation, commit set, coordinator, or epoch.",
    },
    {
        "id": "SBF-MUT-7-SKIP-RECOVERY-AUTHORITY",
        "mode": "skip_recovery_authority",
        "description": "Treat a current fencing token as sufficient even when current recovery authority was revoked.",
    },
    {
        "id": "SBF-MUT-8-UNKNOWN-PARTICIPANT-MEANS-NOT-COMMITTED",
        "mode": "unknown_as_not_committed",
        "description": "Collapse an UNKNOWN participant outcome into NOT_COMMITTED and write without reconciliation.",
    },
    {
        "id": "SBF-MUT-9-DUPLICATE-RECOVERY-REPLAY",
        "mode": "duplicate_recovery_replay",
        "description": "Emit another participant write when the distributed recovery outcome is already durably committed.",
    },
    {
        "id": "SBF-MUT-10-ACCEPT-STALE-COORDINATOR-ACK",
        "mode": "accept_stale_ack",
        "description": "Apply a late acknowledgement from a fenced coordinator and allow it to mutate current coordinator state.",
    },
    {
        "id": "SBF-MUT-11-SKIP-JOINT-WORLD-REVALIDATION",
        "mode": "skip_world_revalidation",
        "description": "Use a current fence to write into a stale joint world without verify-at-use revalidation.",
    },
]


def campaign(required_score=1.0):
    baseline = run()
    rows = []
    killed = 0
    for mutant in MUTANTS:
        mutated = run(mode=mutant["mode"])
        failing = [row["id"] for row in mutated["results"] if not row["passed"]]
        status = "KILLED" if failing else "SURVIVED"
        if status == "KILLED":
            killed += 1
        rows.append({
            **mutant,
            "status": status,
            "failing_controls": failing,
        })
    total = len(rows)
    score = killed / total if total else 0.0
    survived = total - killed
    passed = baseline["summary"]["status"] == "PASS" and score >= required_score and survived == 0
    return {
        "benchmark": "PACC Coordinator Failover and Split-Brain Fencing Mutation Campaign",
        "version": "0.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "falsification of stale recovery ownership, fencing token use, coordinator identity, binding, authority, ambiguous participant outcome, replay, late acknowledgement, and stale-world writes",
        "baseline": baseline["summary"],
        "mutants": rows,
        "summary": {
            "status": "PASS" if passed else "FAIL",
            "killed": killed,
            "survived": survived,
            "total": total,
            "mutation_score": score,
            "required_score": required_score,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output")
    args = parser.parse_args()
    report = campaign(args.required_score)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if report["summary"]["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
