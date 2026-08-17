#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURES = ROOT / "settlement_finality_fixtures.json"
RANK = {"ACCEPTED": 1, "EXECUTED": 2, "SETTLED": 3, "FINAL": 4}


def result(
    *,
    status: str,
    stage: str,
    lookup: bool,
    final: bool,
    effects: int,
    receipt: str | None,
    finality_ref: str | None,
) -> dict[str, Any]:
    return {
        "status": status,
        "canonical_stage": stage,
        "lookup_consulted": lookup,
        "final": final,
        "new_external_effects": effects,
        "settlement_receipt": receipt,
        "finality_ref": finality_ref,
    }


def simulate(data: dict[str, Any], mode: str = "baseline") -> dict[str, Any]:
    lookup_state = data.get("status_lookup")
    canonical = data.get("canonical_status")
    notification = data.get("notification_status")
    receipt = data.get("canonical_settlement_receipt")
    expected_receipt = data.get("expected_settlement_receipt")
    finality_ref = data.get("finality_ref")
    prior = data.get("prior_observed_status")

    if mode == "notification_as_finality" and notification == "FINAL":
        return result(
            status="FINAL_CONFIRMED",
            stage=canonical or "UNKNOWN",
            lookup=False,
            final=True,
            effects=0,
            receipt=receipt,
            finality_ref=finality_ref or "notification-only",
        )

    if lookup_state != "FOUND" or canonical not in RANK:
        if mode == "reissue_on_settlement_timeout":
            return result(
                status="REISSUED_ON_SETTLEMENT_TIMEOUT",
                stage="UNKNOWN",
                lookup=True,
                final=False,
                effects=1,
                receipt=None,
                finality_ref=None,
            )
        return result(
            status="RECONCILE_REQUIRED",
            stage="UNKNOWN",
            lookup=True,
            final=False,
            effects=0,
            receipt=None,
            finality_ref=None,
        )

    if mode == "accepted_as_final" and canonical == "ACCEPTED":
        return result(
            status="FINAL_CONFIRMED",
            stage=canonical,
            lookup=True,
            final=True,
            effects=0,
            receipt=receipt,
            finality_ref=finality_ref or "premature-finality",
        )

    if (
        mode != "ignore_settlement_binding"
        and canonical in {"SETTLED", "FINAL"}
        and expected_receipt is not None
        and receipt != expected_receipt
    ):
        return result(
            status="BLOCK_SETTLEMENT_BINDING",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    if (
        mode != "ignore_nonfinal_downgrade"
        and prior in RANK
        and prior != "FINAL"
        and RANK[canonical] < RANK[prior]
    ):
        return result(
            status="NON_FINAL_DOWNGRADE_OBSERVED",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    if canonical == "ACCEPTED":
        return result(
            status="AWAIT_EXECUTION",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    if canonical == "EXECUTED":
        if mode == "executed_as_settled":
            return result(
                status="AWAIT_FINALITY",
                stage=canonical,
                lookup=True,
                final=False,
                effects=0,
                receipt=receipt or "synthetic-settlement",
                finality_ref=None,
            )
        return result(
            status="AWAIT_SETTLEMENT",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    if canonical == "SETTLED":
        return result(
            status="AWAIT_FINALITY",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    if not finality_ref:
        return result(
            status="BLOCK_MISSING_FINALITY_EVIDENCE",
            stage=canonical,
            lookup=True,
            final=False,
            effects=0,
            receipt=receipt,
            finality_ref=None,
        )

    return result(
        status="FINAL_CONFIRMED",
        stage=canonical,
        lookup=True,
        final=True,
        effects=0,
        receipt=receipt,
        finality_ref=finality_ref,
    )


def run(fixtures_path: Path, mode: str = "baseline") -> dict[str, Any]:
    spec = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for fixture in spec["fixtures"]:
        actual = simulate(fixture["input"], mode=mode)
        expected = fixture["expected"]
        results.append(
            {
                "id": fixture["id"],
                "name": fixture["name"],
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
            }
        )

    passed = sum(bool(item["passed"]) for item in results)
    total = len(results)
    return {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "mode": mode,
        "scope": "deterministic settlement/finality semantics; generic model, not an external-product certification",
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
