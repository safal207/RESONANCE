#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "external_effect_fixtures.json"


def simulate(data: dict[str, Any], mode: str = "baseline") -> dict[str, Any]:
    key = data.get("idempotency_key")
    lookup = data.get("lookup_status")
    lookup_receipt = data.get("lookup_receipt")
    webhook = data.get("webhook_status")
    webhook_receipt = data.get("webhook_receipt")

    if not key:
        return {
            "status": "BLOCK_MISSING_IDEMPOTENCY_KEY",
            "lookup_consulted": False,
            "retry_attempts": 0,
            "new_external_effects": 0,
            "used_retry_key": None,
            "external_receipt": None,
        }

    if mode == "trust_timeout_as_failure" and data.get("initial_response") == "TIMEOUT":
        retry_key = key
        created = data.get("retry_result") == "CREATED"
        return {
            "status": "BLIND_RETRY_AFTER_TIMEOUT",
            "lookup_consulted": False,
            "retry_attempts": 1,
            "new_external_effects": 1 if created else 0,
            "used_retry_key": retry_key,
            "external_receipt": data.get("retry_receipt") if created else lookup_receipt,
        }

    if mode == "webhook_as_authority" and webhook == "SUCCESS":
        return {
            "status": "RECONCILED_SUCCESS",
            "lookup_consulted": False,
            "retry_attempts": 0,
            "new_external_effects": 0,
            "used_retry_key": None,
            "external_receipt": webhook_receipt,
        }

    if lookup == "FOUND_SUCCESS":
        return {
            "status": "RECONCILED_SUCCESS",
            "lookup_consulted": True,
            "retry_attempts": 0,
            "new_external_effects": 0,
            "used_retry_key": None,
            "external_receipt": lookup_receipt,
        }

    if lookup == "FOUND_FAILED":
        return {
            "status": "TERMINAL_FAILED",
            "lookup_consulted": True,
            "retry_attempts": 0,
            "new_external_effects": 0,
            "used_retry_key": None,
            "external_receipt": lookup_receipt,
        }

    if lookup == "UNKNOWN":
        if mode == "blind_resend_without_lookup":
            retry_key = key
            created = data.get("retry_result") == "CREATED"
            return {
                "status": "BLIND_RETRY_ON_UNKNOWN",
                "lookup_consulted": False,
                "retry_attempts": 1,
                "new_external_effects": 1 if created else 0,
                "used_retry_key": retry_key,
                "external_receipt": data.get("retry_receipt") if created else None,
            }
        return {
            "status": "RECONCILE_REQUIRED",
            "lookup_consulted": True,
            "retry_attempts": 0,
            "new_external_effects": 0,
            "used_retry_key": None,
            "external_receipt": None,
        }

    if lookup == "NOT_FOUND":
        retry_key = key
        if mode == "new_key_on_retry":
            retry_key = f"{key}-retry"
        created = data.get("retry_result") == "CREATED"
        receipt = data.get("retry_receipt") if created else lookup_receipt
        return {
            "status": "RETRIED_SAME_KEY_SUCCESS" if created and retry_key == key else "RETRIED_WITH_NEW_KEY",
            "lookup_consulted": True,
            "retry_attempts": 1,
            "new_external_effects": 1 if created else 0,
            "used_retry_key": retry_key,
            "external_receipt": receipt,
        }

    return {
        "status": "RECONCILE_REQUIRED",
        "lookup_consulted": True,
        "retry_attempts": 0,
        "new_external_effects": 0,
        "used_retry_key": None,
        "external_receipt": None,
    }


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
        "scope": "deterministic external-effect recovery semantics; generic model, not an external-product certification",
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
