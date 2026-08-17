#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "compensation_fixtures.json"

TRIGGERS = {"SETTLEMENT_FAILED", "REVERSED"}


def result(
    *,
    status: str,
    original_effect_ref: str | None,
    lookup_consulted: bool = False,
    authorization_checked: bool = False,
    new_effects: int = 0,
    retry_attempts: int = 0,
    used_key: str | None = None,
    compensation_receipt: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "lookup_consulted": lookup_consulted,
        "compensation_authorized_checked": authorization_checked,
        "new_compensation_effects": new_effects,
        "retry_attempts": retry_attempts,
        "used_compensation_key": used_key,
        "compensation_receipt": compensation_receipt,
        "bound_original_effect_ref": original_effect_ref,
    }


def simulate(data: dict[str, Any], mode: str = "baseline") -> dict[str, Any]:
    effect_ref = data.get("original_effect_ref")
    trigger = data.get("compensation_trigger")
    authorized = bool(data.get("compensation_authorized"))
    target_ref = data.get("compensation_target_effect_ref")
    key = data.get("compensation_idempotency_key")
    lookup = data.get("compensation_lookup_status")
    lookup_receipt = data.get("compensation_lookup_receipt")
    same_replay = bool(data.get("same_operation_replay"))

    if trigger not in TRIGGERS:
        if mode == "compensate_without_trigger":
            return result(
                status="COMPENSATED_WITHOUT_TRIGGER",
                original_effect_ref=effect_ref,
                new_effects=1,
                retry_attempts=1,
                used_key=key,
                compensation_receipt=data.get("retry_receipt"),
            )
        return result(status="NO_COMPENSATION_REQUIRED", original_effect_ref=effect_ref)

    authorization_checked = True
    if not authorized and mode != "skip_compensation_authority":
        return result(
            status="BLOCK_COMPENSATION_NOT_AUTHORIZED",
            original_effect_ref=effect_ref,
            authorization_checked=True,
        )

    if target_ref != effect_ref and mode != "ignore_compensation_binding":
        return result(
            status="BLOCK_COMPENSATION_BINDING",
            original_effect_ref=effect_ref,
            authorization_checked=True,
        )

    if not key:
        if mode == "allow_missing_compensation_key":
            key = "generated-retry-key"
        else:
            return result(
                status="BLOCK_MISSING_COMPENSATION_IDEMPOTENCY_KEY",
                original_effect_ref=effect_ref,
                authorization_checked=True,
            )

    if lookup == "FOUND_SUCCESS":
        if mode == "duplicate_compensation_after_timeout" and data.get("compensation_initial_response") == "TIMEOUT":
            return result(
                status="DUPLICATE_COMPENSATION_AFTER_TIMEOUT",
                original_effect_ref=effect_ref,
                lookup_consulted=True,
                authorization_checked=authorization_checked,
                new_effects=1,
                retry_attempts=1,
                used_key=key,
                compensation_receipt=data.get("retry_receipt"),
            )
        if mode == "replay_emits_duplicate_compensation" and same_replay:
            return result(
                status="DUPLICATE_COMPENSATION_ON_REPLAY",
                original_effect_ref=effect_ref,
                lookup_consulted=True,
                authorization_checked=authorization_checked,
                new_effects=1,
                retry_attempts=1,
                used_key=key,
                compensation_receipt=data.get("retry_receipt"),
            )
        return result(
            status="IDEMPOTENT_COMPENSATION_REPLAY" if same_replay else "COMPENSATION_RECONCILED",
            original_effect_ref=effect_ref,
            lookup_consulted=True,
            authorization_checked=authorization_checked,
            compensation_receipt=lookup_receipt,
        )

    if lookup == "UNKNOWN":
        if mode == "blind_compensation_on_unknown":
            return result(
                status="BLIND_COMPENSATION_RETRY",
                original_effect_ref=effect_ref,
                lookup_consulted=True,
                authorization_checked=authorization_checked,
                new_effects=1,
                retry_attempts=1,
                used_key=key,
                compensation_receipt=data.get("retry_receipt"),
            )
        return result(
            status="RECONCILE_COMPENSATION_REQUIRED",
            original_effect_ref=effect_ref,
            lookup_consulted=True,
            authorization_checked=authorization_checked,
        )

    if lookup == "NOT_FOUND":
        retry_key = key
        if mode == "new_compensation_key_on_retry":
            retry_key = f"{key}-retry"
        created = data.get("retry_result") == "CREATED"
        return result(
            status="COMPENSATED" if created and retry_key == key else "COMPENSATED_WITH_NEW_KEY",
            original_effect_ref=effect_ref,
            lookup_consulted=True,
            authorization_checked=authorization_checked,
            new_effects=1 if created else 0,
            retry_attempts=1,
            used_key=retry_key,
            compensation_receipt=data.get("retry_receipt") if created else None,
        )

    return result(
        status="RECONCILE_COMPENSATION_REQUIRED",
        original_effect_ref=effect_ref,
        lookup_consulted=True,
        authorization_checked=authorization_checked,
    )


def run(fixtures_path: Path, mode: str = "baseline") -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual = simulate(fixture["input"], mode=mode)
        expected = fixture["expected"]
        results.append({
            "id": fixture["id"],
            "name": fixture["name"],
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
        })

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "mode": mode,
        "scope": "deterministic compensation/reversal semantics; generic model, not an external-product certification",
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
