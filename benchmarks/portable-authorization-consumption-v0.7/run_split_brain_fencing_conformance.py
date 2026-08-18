#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "split_brain_fencing_fixtures.json"


def result(status, data, *, new_writes=0, coordinator_updates=0):
    return {
        "status": status,
        "new_writes": new_writes,
        "coordinator_updates": coordinator_updates,
        "used_epoch": data.get("presented_epoch"),
        "used_fencing_token": data.get("presented_fencing_token"),
    }


def evaluate(control, mode="baseline"):
    data = control["input"]

    if data.get("prior_recovery_outcome") == "COMMITTED":
        if mode == "duplicate_recovery_replay":
            return result("ALLOW_FENCED_PARTICIPANT_WRITE", data, new_writes=1, coordinator_updates=1)
        return result("IDEMPOTENT_FENCED_RECOVERY_REPLAY", data)

    if not data.get("fencing_evidence_present"):
        if mode == "invent_missing_fence":
            data = dict(data)
            data["presented_fencing_token"] = data.get("current_fencing_token")
            data["fencing_evidence_present"] = True
            data["fencing_binding"] = {
                "operation_id": data.get("operation_id"),
                "commit_set_ref": data.get("commit_set_ref"),
                "coordinator_id": data.get("coordinator_id"),
                "epoch": data.get("presented_epoch"),
            }
        else:
            return result("BLOCK_FENCING_EVIDENCE_MISSING", data)

    binding = data.get("fencing_binding") or {}
    expected_binding = {
        "operation_id": data.get("operation_id"),
        "commit_set_ref": data.get("commit_set_ref"),
        "coordinator_id": data.get("coordinator_id"),
        "epoch": data.get("presented_epoch"),
    }
    if binding != expected_binding and mode != "ignore_fencing_binding":
        return result("BLOCK_FENCING_BINDING", data)

    if data.get("presented_epoch") != data.get("current_epoch") and mode not in {"ignore_epoch", "identity_implies_ownership"}:
        return result("BLOCK_STALE_RECOVERY_EPOCH", data)

    if data.get("coordinator_id") != data.get("current_coordinator_id") and mode != "ignore_coordinator_identity":
        return result("BLOCK_STALE_COORDINATOR", data)

    if data.get("presented_fencing_token") != data.get("current_fencing_token") and mode != "ignore_token":
        return result("BLOCK_FENCING_TOKEN_MISMATCH", data)

    if data.get("recovery_authority") != "CURRENT" and mode != "skip_recovery_authority":
        return result("BLOCK_RECOVERY_NOT_AUTHORIZED", data)

    if data.get("requested_action") == "APPLY_LATE_ACK":
        late_ack = data.get("late_ack") or {}
        stale = (
            late_ack.get("epoch") != data.get("current_epoch")
            or late_ack.get("coordinator_id") != data.get("current_coordinator_id")
            or late_ack.get("fencing_token") != data.get("current_fencing_token")
        )
        if stale and mode != "accept_stale_ack":
            return result("IGNORE_STALE_COORDINATOR_ACK", data)
        return result("APPLIED_COORDINATOR_ACK", data, coordinator_updates=1)

    participant_state = data.get("participant_state")
    if participant_state == "UNKNOWN":
        if mode == "unknown_as_not_committed":
            participant_state = "NOT_COMMITTED"
        else:
            return result("RECONCILE_PARTICIPANT_REQUIRED", data)

    if participant_state == "COMMITTED":
        return result("IDEMPOTENT_PARTICIPANT_REPLAY", data)

    if data.get("joint_world") != "CURRENT" and mode != "skip_world_revalidation":
        return result("REVALIDATE_DISTRIBUTED_TRANSITION", data)

    if participant_state == "NOT_COMMITTED":
        return result("ALLOW_FENCED_PARTICIPANT_WRITE", data, new_writes=1, coordinator_updates=1)

    return result("BLOCK_PARTICIPANT_STATE_UNPROVEN", data)


def run(mode="baseline"):
    fixture_doc = json.loads(FIXTURES.read_text(encoding="utf-8"))
    results = []
    for control in fixture_doc["controls"]:
        actual = evaluate(control, mode=mode)
        expected = control["expected"]
        results.append({
            "id": control["id"],
            "name": control["name"],
            "actual": actual,
            "expected": expected,
            "passed": actual == expected,
        })
    passed = sum(1 for row in results if row["passed"])
    return {
        "benchmark": fixture_doc["benchmark"],
        "version": fixture_doc["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "scope": fixture_doc["scope"],
        "results": results,
        "summary": {
            "status": "PASS" if passed == len(results) else "FAIL",
            "passed": passed,
            "total": len(results),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if report["summary"]["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
