#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_composition_conformance import DEFAULT_ORDER, ROOT, execute

FIXTURES = ROOT / "fixtures.json"

CANDIDATES = [
    {
        "id": "ORDER-1-AUTHORITY-AFTER-CONSUME",
        "description": "Consume before checking current authority.",
        "order": ["verify_proof", "consume", "check_authority", "dispatch", "bind_outcome"],
        "must_kill": ["PACC-2"],
    },
    {
        "id": "ORDER-2-DISPATCH-BEFORE-CONSUME",
        "description": "Dispatch before atomic consumption.",
        "order": ["verify_proof", "check_authority", "dispatch", "consume", "bind_outcome"],
        "must_kill": ["PACC-1", "PACC-3"],
    },
    {
        "id": "ORDER-3-OUTCOME-BEFORE-DISPATCH",
        "description": "Bind outcome before a dispatch exists.",
        "order": ["verify_proof", "check_authority", "consume", "bind_outcome", "dispatch"],
        "must_kill": ["PACC-1"],
    },
    {
        "id": "ORDER-4-AUTHORITY-BEFORE-PROOF",
        "description": "Evaluate authority before proof authenticity is established.",
        "order": ["check_authority", "verify_proof", "consume", "dispatch", "bind_outcome"],
        "must_kill": ["PACC-1", "PACC-6"],
    },
    {
        "id": "EQUIV-1-NONE",
        "description": "Baseline order identity control.",
        "order": DEFAULT_ORDER,
        "equivalent": True,
        "equivalence_basis": "Identity permutation; exact same ordered step sequence as baseline.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required-score", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    spec = json.loads(FIXTURES.read_text(encoding="utf-8"))
    fixtures = spec["fixtures"]
    baseline = {f["id"]: execute(f["input"], DEFAULT_ORDER)[:2] for f in fixtures}
    mutants = []

    for candidate in CANDIDATES:
        differences = []
        invalid = None
        try:
            for f in fixtures:
                observed = execute(f["input"], candidate["order"])[:2]
                if observed != baseline[f["id"]]:
                    differences.append(f["id"])
        except Exception as exc:
            invalid = f"{type(exc).__name__}: {exc}"

        if invalid:
            status = "INVALID"
        elif candidate.get("equivalent"):
            status = "EQUIVALENT" if not differences else "INVALID"
        else:
            must_kill = set(candidate.get("must_kill", []))
            status = "KILLED" if must_kill.issubset(differences) else "SURVIVED"

        item = {
            "id": candidate["id"],
            "description": candidate["description"],
            "order": candidate["order"],
            "status": status,
            "differing_controls": differences,
        }
        if candidate.get("equivalence_basis"):
            item["equivalence_basis"] = candidate["equivalence_basis"]
        if invalid:
            item["error"] = invalid
        mutants.append(item)

    killed = sum(m["status"] == "KILLED" for m in mutants)
    survived = sum(m["status"] == "SURVIVED" for m in mutants)
    equivalent = sum(m["status"] == "EQUIVALENT" for m in mutants)
    invalid = sum(m["status"] == "INVALID" for m in mutants)
    scored_total = killed + survived
    score = killed / scored_total if scored_total else 0.0
    status = "PASS" if score >= args.required_score and survived == 0 and invalid == 0 else "FAIL"

    report = {
        "benchmark": "PACC Order Mutation Campaign",
        "version": "0.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "causal ordering between proof, current authority, atomic consumption, dispatch, and outcome",
        "summary": {
            "killed": killed,
            "survived": survived,
            "equivalent": equivalent,
            "invalid": invalid,
            "scored_total": scored_total,
            "total_candidates": len(mutants),
            "mutation_score": score,
            "required_score": args.required_score,
            "status": status,
        },
        "mutants": mutants,
    }

    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
