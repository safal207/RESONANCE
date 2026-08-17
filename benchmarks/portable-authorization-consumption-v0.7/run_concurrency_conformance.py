#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "concurrency_fixtures.json"


def simulate(data: dict[str, Any], mode: str = "baseline") -> dict[str, Any]:
    initial = data.get("initial_consumption") or {}
    consumed_by_operation = initial.get("operation_id")
    consumption_ref = initial.get("consumption_ref")
    dispatch_ref = initial.get("dispatch_ref")

    consume_events: list[dict[str, Any]] = []
    dispatch_events: list[dict[str, Any]] = []
    attempt_results: list[dict[str, Any]] = []

    for index, attempt in enumerate(data.get("attempts", []), start=1):
        worker = attempt["worker"]
        operation_id = attempt.get("operation_id")
        effective_operation_id = operation_id

        if mode == "idempotency_key_omission":
            effective_operation_id = f"{operation_id}::{worker}::{index}"

        stale_snapshot_allows = (
            mode == "non_atomic_check_then_set"
            and bool(data.get("concurrent_snapshot"))
            and attempt.get("pre_read") == "UNSPENT"
        )

        if consumed_by_operation is None or stale_snapshot_allows:
            new_consumption_ref = f"consume-{effective_operation_id}-{worker}"
            consumed_by_operation = effective_operation_id
            consumption_ref = new_consumption_ref
            consume_events.append(
                {
                    "worker": worker,
                    "operation_id": effective_operation_id,
                    "consumption_ref": new_consumption_ref,
                }
            )
            new_dispatch_ref = f"dispatch-{effective_operation_id}-{worker}"
            dispatch_ref = new_dispatch_ref
            dispatch_events.append(
                {
                    "worker": worker,
                    "operation_id": effective_operation_id,
                    "dispatch_ref": new_dispatch_ref,
                }
            )
            attempt_results.append(
                {
                    "worker": worker,
                    "operation_id": operation_id,
                    "status": "CONSUMED",
                    "consumption_ref": new_consumption_ref,
                    "dispatch_ref": new_dispatch_ref,
                }
            )
            continue

        if consumed_by_operation == effective_operation_id:
            if mode == "duplicate_dispatch_on_replay":
                duplicate_ref = f"dispatch-{effective_operation_id}-{worker}-duplicate"
                dispatch_events.append(
                    {
                        "worker": worker,
                        "operation_id": effective_operation_id,
                        "dispatch_ref": duplicate_ref,
                    }
                )
            attempt_results.append(
                {
                    "worker": worker,
                    "operation_id": operation_id,
                    "status": "IDEMPOTENT_REPLAY",
                    "consumption_ref": consumption_ref,
                    "dispatch_ref": dispatch_ref,
                }
            )
            continue

        if mode == "loser_dispatch":
            loser_ref = f"dispatch-{effective_operation_id}-{worker}-loser"
            dispatch_events.append(
                {
                    "worker": worker,
                    "operation_id": effective_operation_id,
                    "dispatch_ref": loser_ref,
                }
            )

        attempt_results.append(
            {
                "worker": worker,
                "operation_id": operation_id,
                "status": "ALREADY_CONSUMED",
                "consumption_ref": None,
                "dispatch_ref": None,
            }
        )

    return {
        "attempt_statuses": [item["status"] for item in attempt_results],
        "new_consumptions": len(consume_events),
        "new_dispatches": len(dispatch_events),
        "dispatch_workers": [item["worker"] for item in dispatch_events],
        "final_consumed_by_operation": consumed_by_operation,
        "attempt_results": attempt_results,
        "consume_events": consume_events,
        "dispatch_events": dispatch_events,
    }


def project(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempt_statuses": result["attempt_statuses"],
        "new_consumptions": result["new_consumptions"],
        "new_dispatches": result["new_dispatches"],
        "dispatch_workers": result["dispatch_workers"],
        "final_consumed_by_operation": result["final_consumed_by_operation"],
    }


def run(fixtures_path: Path, mode: str = "baseline") -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual_full = simulate(fixture["input"], mode=mode)
        actual = project(actual_full)
        expected = fixture["expected"]
        passed = actual == expected
        results.append(
            {
                "id": fixture["id"],
                "name": fixture["name"],
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "attempt_results": actual_full["attempt_results"],
                "consume_events": actual_full["consume_events"],
                "dispatch_events": actual_full["dispatch_events"],
            }
        )

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "mode": mode,
        "scope": "deterministic interleaving model for atomic single-use consumption, winner-only dispatch, and logical-operation idempotency",
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
