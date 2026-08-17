#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "crash_recovery_fixtures.json"


def simulate(data: dict[str, Any], mode: str = "baseline") -> dict[str, Any]:
    initial_consumption = data.get("initial_consumption")
    durable_dispatch = data.get("durable_dispatch")
    dispatch_state = data.get("dispatch_state")
    ack_received = bool(data.get("ack_received"))
    retry = data.get("retry") or {}
    worker = retry.get("worker", "W-retry")
    operation_id = retry.get("operation_id")

    consumption = dict(initial_consumption) if initial_consumption else None
    dispatch = dict(durable_dispatch) if durable_dispatch else None
    consume_events: list[dict[str, Any]] = []
    dispatch_events: list[dict[str, Any]] = []

    if mode == "guess_through_lost_consumption_receipt" and consumption is None and dispatch is not None:
        consumption = {
            "operation_id": dispatch.get("operation_id"),
            "consumption_ref": dispatch.get("consumption_ref"),
            "guessed": True,
        }

    if dispatch is not None and consumption is None:
        status = "BLOCK_RECOVERY_EVIDENCE_INCOMPLETE"
    elif dispatch is not None and consumption is not None and (
        dispatch.get("operation_id") != consumption.get("operation_id")
        or dispatch.get("consumption_ref") != consumption.get("consumption_ref")
    ):
        status = "BLOCK_RECOVERY_BINDING_MISMATCH"
    elif consumption is not None and consumption.get("operation_id") != operation_id:
        status = "ALREADY_CONSUMED"
    elif consumption is not None and dispatch is not None:
        if mode == "duplicate_dispatch_after_ack_failure" and not ack_received:
            duplicate_ref = f"dispatch-{operation_id}-duplicate-{worker}"
            dispatch_events.append({
                "worker": worker,
                "operation_id": operation_id,
                "consumption_ref": consumption.get("consumption_ref"),
                "dispatch_ref": duplicate_ref,
            })
        status = "IDEMPOTENT_REPLAY"
    elif consumption is not None and dispatch is None:
        if dispatch_state == "UNKNOWN":
            if mode == "blind_dispatch_on_unknown":
                new_dispatch_ref = f"dispatch-{operation_id}-blind-{worker}"
                dispatch_events.append({
                    "worker": worker,
                    "operation_id": operation_id,
                    "consumption_ref": consumption.get("consumption_ref"),
                    "dispatch_ref": new_dispatch_ref,
                })
                dispatch = {
                    "operation_id": operation_id,
                    "consumption_ref": consumption.get("consumption_ref"),
                    "dispatch_ref": new_dispatch_ref,
                }
                status = "RECOVERED_DISPATCH"
            else:
                status = "RECONCILE_REQUIRED"
        elif dispatch_state == "NOT_SENT":
            if mode == "reconsume_after_crash":
                duplicate_consumption_ref = f"consume-{operation_id}-duplicate-{worker}"
                consume_events.append({
                    "worker": worker,
                    "operation_id": operation_id,
                    "consumption_ref": duplicate_consumption_ref,
                })
                consumption = {
                    "operation_id": operation_id,
                    "consumption_ref": duplicate_consumption_ref,
                }
            new_dispatch_ref = f"dispatch-{operation_id}-recovery-{worker}"
            dispatch_events.append({
                "worker": worker,
                "operation_id": operation_id,
                "consumption_ref": consumption.get("consumption_ref"),
                "dispatch_ref": new_dispatch_ref,
            })
            dispatch = {
                "operation_id": operation_id,
                "consumption_ref": consumption.get("consumption_ref"),
                "dispatch_ref": new_dispatch_ref,
            }
            status = "RECOVERED_DISPATCH"
        else:
            status = "BLOCK_RECOVERY_STATE_UNKNOWN"
    else:
        status = "BLOCK_RECOVERY_EVIDENCE_INCOMPLETE"

    return {
        "status": status,
        "new_consumptions": len(consume_events),
        "new_dispatches": len(dispatch_events),
        "final_consumed_by_operation": consumption.get("operation_id") if consumption else None,
        "final_dispatch_ref": dispatch.get("dispatch_ref") if dispatch else None,
        "consume_events": consume_events,
        "dispatch_events": dispatch_events,
    }


def project(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result["status"],
        "new_consumptions": result["new_consumptions"],
        "new_dispatches": result["new_dispatches"],
        "final_consumed_by_operation": result["final_consumed_by_operation"],
        "final_dispatch_ref": result["final_dispatch_ref"],
    }


def run(fixtures_path: Path, mode: str = "baseline") -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual_full = simulate(fixture["input"], mode=mode)
        actual = project(actual_full)
        expected = fixture["expected"]
        passed = actual == expected
        results.append({
            "id": fixture["id"],
            "name": fixture["name"],
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "consume_events": actual_full["consume_events"],
            "dispatch_events": actual_full["dispatch_events"],
        })

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "mode": mode,
        "scope": "deterministic crash-window recovery semantics between durable consumption and consequential dispatch",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "total": total,
            "status": "PASS" if passed == total else "FAIL",
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--mode", default="baseline")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run(args.fixtures, mode=args.mode)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
