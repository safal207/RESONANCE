#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from run_aba_lineage_conformance import run

MUTANTS = [
    ("ABA-MUT-1-VALUE-EQUALITY-RESTORES-OWNERSHIP", "value_equality_restores_ownership", "Treat a returned value as proof that the old causal owner is current again."),
    ("ABA-MUT-2-VERSION-EQUALITY-RESTORES-OWNERSHIP", "version_equality_restores_ownership", "Treat a reused version number as proof that the old causal owner is current again."),
    ("ABA-MUT-3-TRUST-STALE-LINEAGE-WITNESS", "trust_stale_lineage_witness", "Use an older lineage witness instead of revalidating at compensation use time."),
    ("ABA-MUT-4-IGNORE-CURRENT-EFFECT-BINDING", "ignore_current_effect_binding", "Accept lineage identity while ignoring the exact effect that currently owns the state."),
    ("ABA-MUT-5-INVENT-MISSING-LINEAGE-WITNESS", "invent_missing_lineage_witness", "Invent current lineage evidence when the durable witness is missing."),
    ("ABA-MUT-6-DUPLICATE-COMMITTED-COMPENSATION", "duplicate_committed_compensation", "Emit another compensation after a committed compensation already exists."),
    ("ABA-MUT-7-BLIND-RETRY-UNKNOWN", "blind_retry_unknown_compensation", "Retry a compensation whose prior outcome is unknown instead of reconciling."),
    ("ABA-MUT-8-INVENT-CURRENT-LINEAGE", "invent_current_lineage_from_value_version", "Reconstruct missing current lineage from matching value/version metadata."),
    ("ABA-MUT-9-SKIP-COMPENSATION-AUTHORITY", "skip_compensation_authority", "Treat lineage ownership as current authority to compensate."),
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(Path(__file__).with_name("aba_lineage_fixtures.json")))
    p.add_argument("--output")
    p.add_argument("--required-score", type=float, default=1.0)
    a = p.parse_args()

    baseline = run(a.fixtures, "baseline")
    rows = []
    for mid, mode, description in MUTANTS:
        report = run(a.fixtures, mode)
        failing = [r["id"] for r in report["results"] if not r["passed"]]
        rows.append({"id": mid, "mode": mode, "description": description, "failing_controls": failing, "status": "KILLED" if failing else "SURVIVED"})

    killed = sum(r["status"] == "KILLED" for r in rows)
    survived = len(rows) - killed
    score = killed / len(rows) if rows else 0.0
    status = "PASS" if baseline["summary"]["status"] == "PASS" and survived == 0 and score >= a.required_score else "FAIL"
    out = {
        "benchmark": "PACC ABA Lineage Mutation Campaign",
        "version": "0.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": baseline["summary"],
        "mutants": rows,
        "scope": "falsification of ABA value/version aliasing, stale lineage evidence, effect binding, authority, replay, reconciliation, and lineage reconstruction",
        "summary": {"status": status, "killed": killed, "survived": survived, "total": len(rows), "mutation_score": score, "required_score": a.required_score},
    }
    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if status == "PASS" else 1)

if __name__ == "__main__":
    main()
