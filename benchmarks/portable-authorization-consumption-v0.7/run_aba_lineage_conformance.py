#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def out(status, lineage, new=0, blocked=True):
    return {"status": status, "new_compensations": new, "blocked_overwrite": blocked, "used_lineage_ref": lineage}

def evaluate_case(c, mode="baseline"):
    witness = c.get("state_witness_lineage_ref")
    current = c.get("current_lineage_ref")
    owned = c.get("owned_lineage_ref")

    if c.get("trigger") != "REVERSAL_REQUIRED":
        return out("NO_COMPENSATION_REQUIRED", witness, 0, False)

    if current is None:
        if mode == "invent_current_lineage_from_value_version":
            current = owned
        else:
            return out("BLOCK_CURRENT_LINEAGE_UNPROVEN", witness)

    if witness is None:
        if mode == "invent_missing_lineage_witness":
            witness = current
        else:
            return out("BLOCK_MISSING_LINEAGE_WITNESS", None)

    if witness != current and mode != "trust_stale_lineage_witness":
        return out("REVALIDATE_CURRENT_LINEAGE", witness)

    lineage_changed = current != owned
    if lineage_changed:
        if mode == "value_equality_restores_ownership" and c.get("current_value_digest") == c.get("owned_value_digest"):
            pass
        elif mode == "version_equality_restores_ownership" and c.get("current_resource_version") == c.get("owned_resource_version"):
            pass
        else:
            return out("BLOCK_LINEAGE_CHANGED", witness)

    if c.get("current_effect_ref") != c.get("original_effect_ref") and mode != "ignore_current_effect_binding":
        return out("BLOCK_CURRENT_EFFECT_BINDING", witness)

    if not c.get("compensation_authorized", False) and mode != "skip_compensation_authority":
        return out("BLOCK_COMPENSATION_NOT_AUTHORIZED", witness)

    state = c.get("compensation_state", "NOT_SENT")
    if state == "COMMITTED":
        return out("COMPENSATED", witness, 1, False) if mode == "duplicate_committed_compensation" else out("IDEMPOTENT_COMPENSATION_REPLAY", witness, 0, False)
    if state == "UNKNOWN":
        return out("COMPENSATED", witness, 1, False) if mode == "blind_retry_unknown_compensation" else out("RECONCILE_COMPENSATION_REQUIRED", witness)

    return out("COMPENSATED", witness, 1, False)

def run(path, mode="baseline"):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    results = []
    for case in payload["cases"]:
        actual = evaluate_case(case, mode)
        expected = case["expected"]
        results.append({"id": case["id"], "name": case["name"], "actual": actual, "expected": expected, "passed": actual == expected})
    passed = sum(r["passed"] for r in results)
    return {
        "benchmark": "PACC ABA Lineage Integrity",
        "version": "0.7",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "results": results,
        "scope": "deterministic ABA/causal-lineage semantics for compensation; not an external-product certification",
        "summary": {"status": "PASS" if passed == len(results) else "FAIL", "passed": passed, "total": len(results)},
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(Path(__file__).with_name("aba_lineage_fixtures.json")))
    p.add_argument("--output")
    p.add_argument("--mode", default="baseline")
    a = p.parse_args()
    report = run(a.fixtures, a.mode)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if report["summary"]["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
