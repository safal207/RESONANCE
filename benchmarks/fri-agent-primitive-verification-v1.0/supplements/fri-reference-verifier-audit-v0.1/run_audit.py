#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRI_ROOT = HERE.parents[1]
DEFAULT_FIXTURES = HERE / "fixtures.json"


def load_reference_evaluator():
    path = FRI_ROOT / "run_fri_conformance.py"
    spec = importlib.util.spec_from_file_location("fri_reference", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load reference evaluator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit FRI reference evaluator with positive, negative, and missing-evidence controls.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evaluate = load_reference_evaluator()
    spec = json.loads(args.fixtures.read_text(encoding="utf-8"))
    results = []

    for control in spec["controls"]:
        actual, reason = evaluate(control["rule"], control["input"])
        expected = control["expected"]
        results.append(
            {
                "id": control["id"],
                "rule": control["rule"],
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
                "reason": reason,
            }
        )

    passed = sum(bool(item["pass"]) for item in results)
    total = len(results)
    report = {
        "benchmark": spec["benchmark"],
        "version": spec["version"],
        "scope": spec["scope"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "total": total,
            "status": "PASS" if passed == total else "FAIL",
        },
        "results": results,
    }

    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
