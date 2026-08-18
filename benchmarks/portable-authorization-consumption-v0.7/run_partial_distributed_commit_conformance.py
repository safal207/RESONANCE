#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "partial_distributed_commit_fixtures.json"


def result(status, operation_id, *, new_writes=0, new_compensations=0,
           coordinator_updates=0, touched_participants=None):
    return {
        "status": status,
        "new_writes": new_writes,
        "new_compensations": new_compensations,
        "coordinator_updates": coordinator_updates,
        "touched_participants": sorted(touched_participants or []),
        "used_operation_id": operation_id,
    }


def evaluate(control, mode="baseline"):
    data = control["input"]
    operation_id = data.get("operation_id")
    idempotency_key = data.get("idempotency_key")
    commit_set_ref = data.get("commit_set_ref")

    if not operation_id or not idempotency_key:
        if mode == "invent_missing_identity":
            operation_id = operation_id or "invented-recovery-operation"
            idempotency_key = idempotency_key or "invented-recovery-key"
        else:
            return result("BLOCK_MISSING_DISTRIBUTED_IDENTITY", operation_id)

    prior = data.get("prior_recovery_outcome", "NONE")
    if prior == "COMMITTED":
        if mode == "duplicate_recovery_replay":
            return result(
                "RECOVERY_REPLAY_DUPLICATED",
                operation_id,
                new_writes=1,
                touched_participants=["B"],
            )
        return result("IDEMPOTENT_DISTRIBUTED_REPLAY", operation_id)

    if prior == "UNKNOWN":
        return result("RECONCILE_RECOVERY_REQUIRED", operation_id)

    participants = data.get("participants") or {}
    expected_effects = data.get("expected_effects") or {}
    required = {"A", "B"}
    if not required.issubset(participants) or not required.issubset(expected_effects):
        return result("BLOCK_PARTICIPANT_EVIDENCE_INCOMPLETE", operation_id)

    states = {}
    for name in sorted(required):
        participant = participants[name]
        state = participant.get("state")
        states[name] = state

        if state == "COMMITTED" and mode != "ignore_participant_binding":
            participant_operation = participant.get("operation_id")
            if mode == "invent_missing_identity" and participant_operation is None:
                participant_operation = operation_id
            if (
                not participant.get("receipt_ref")
                or participant_operation != operation_id
                or participant.get("commit_set_ref") != commit_set_ref
                or participant.get("effect_ref") != expected_effects[name]
            ):
                return result("BLOCK_PARTICIPANT_BINDING", operation_id)

    if any(state == "UNKNOWN" for state in states.values()):
        if mode == "unknown_as_not_committed":
            states = {
                name: ("NOT_COMMITTED" if state == "UNKNOWN" else state)
                for name, state in states.items()
            }
        else:
            return result("RECONCILE_PARTICIPANT_REQUIRED", operation_id)

    committed = sorted(name for name, state in states.items() if state == "COMMITTED")
    not_committed = sorted(name for name, state in states.items() if state == "NOT_COMMITTED")

    if data.get("coordinator_phase") == "COMMITTED" and not_committed:
        if mode == "trust_coordinator_commit":
            return result("RECOVERED_COMPLETE", operation_id)
        return result("BLOCK_COORDINATOR_EVIDENCE_CONFLICT", operation_id)

    if len(committed) == len(required):
        coordinator_updates = 0 if data.get("coordinator_phase") == "COMMITTED" else 1
        return result(
            "RECOVERED_COMPLETE",
            operation_id,
            coordinator_updates=coordinator_updates,
        )

    if not committed and not_committed:
        return result("NO_PARTICIPANT_COMMITTED", operation_id)

    policy = data.get("recovery_policy")
    if policy == "COMPLETE_FORWARD":
        if not data.get("current_snapshot_valid") and mode != "skip_revalidation":
            return result("REVALIDATE_DISTRIBUTED_TRANSITION", operation_id)
        if data.get("completion_authority") != "CURRENT":
            return result("BLOCK_COMPLETION_NOT_AUTHORIZED", operation_id)

        touched = list(not_committed)
        writes = len(not_committed)
        if mode == "rewrite_committed_participant":
            touched = sorted(set(touched + committed))
            writes += len(committed)
        return result(
            "COMPLETED_FORWARD",
            operation_id,
            new_writes=writes,
            coordinator_updates=1,
            touched_participants=touched,
        )

    if policy == "COMPENSATE_PARTIAL":
        irreversible = sorted(set(committed) & set(data.get("irreversible_participants") or []))
        if irreversible and mode != "compensate_irreversible":
            return result(
                "MANUAL_RECOVERY_REQUIRED",
                operation_id,
                touched_participants=irreversible,
            )
        if data.get("compensation_authority") != "CURRENT" and mode != "skip_compensation_authority":
            return result("BLOCK_COMPENSATION_NOT_AUTHORIZED", operation_id)
        return result(
            "COMPENSATED_PARTIAL",
            operation_id,
            new_compensations=len(committed),
            coordinator_updates=1,
            touched_participants=committed,
        )

    return result("BLOCK_UNKNOWN_RECOVERY_POLICY", operation_id)


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
        "benchmark": "PACC Partial Distributed Commit and Coordinator Recovery",
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
