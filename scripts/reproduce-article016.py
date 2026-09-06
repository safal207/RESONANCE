#!/usr/bin/env python3
"""Replay existing repository-owned seeds for Article 016; no external actions."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import platform
import runpy
import subprocess
import sys

PINS = {
    "cml": "7a3a98c60a402d394e4d286da956823898454b8a",
    "cgqa": "f861b934d77e64fd35f768e2a33bb4a00963bc19",
}
CGQA_CASES = [
    ("pass_committed_stop.json", "pass", None),
    ("pass_failed_retry_same_identity.json", "pass", None),
    ("fail_retry_before_reconcile.json", "fail", "APR-001_UNRESOLVED_AMBIGUITY_FINANCIAL_ACTION"),
    ("fail_changed_idempotency_after_failed_reconcile.json", "fail", "APR-004_IDEMPOTENCY_CHANGED_ON_RETRY"),
]


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cml", required=True, type=Path)
    parser.add_argument("--cgqa", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    roots = {name: getattr(args, name).resolve() for name in PINS}
    source_hashes = {}
    for name, root in roots.items():
        if git(root, "rev-parse", "HEAD") != PINS[name]:
            raise SystemExit(f"{name}: checkout must match pinned commit {PINS[name]}")
        if git(root, "status", "--porcelain", "--untracked-files=no"):
            raise SystemExit(f"{name}: tracked source changes are not allowed")
        sys.path.insert(0, str(root))
        source_hashes[name] = {
            file: digest((root / file).read_bytes())
            for file in git(root, "ls-files").splitlines()
            if file.endswith(".py") and (root / file).is_file()
        }

    demo = runpy.run_path(str(roots["cml"] / "examples/agent_approval_lineage_audit.py"))
    cml_module = importlib.import_module("cml.audit")
    cgqa_module = importlib.import_module("contractgraph_qa.payment_recovery")
    for name, module in [("cml", cml_module), ("cgqa", cgqa_module)]:
        if not Path(module.__file__).resolve().is_relative_to(roots[name]):
            raise SystemExit(f"{name}: imported evaluator is outside the pinned checkout")

    def evaluate() -> list[dict]:
        results = []
        for name, factory, expected, codes in [
            ("cml_invalid_approval_lineage", "make_invalid_trace", False,
             {"CML-AUDIT-R7-ML_ACTION_REQUIRES_POLICY_APPROVAL", "CML-AUDIT-R5-EXEC_REQUIRES_HUMAN_APPROVAL"}),
            ("cml_valid_approval_lineage", "make_valid_trace", True, set()),
        ]:
            records = demo[factory]()
            config = cml_module.AuditConfig.from_yaml_string(demo["APPROVAL_LINEAGE_RULES"])
            result = cml_module.AuditEngine(config).run(records)
            native = result.to_dict()
            actual_codes = {finding.code for finding in result.findings}
            results.append({
                "case": name, "input": [record.to_dict() for record in records],
                "rules": demo["APPROVAL_LINEAGE_RULES"], "native_result": native,
                "expected_pass": expected, "observed_pass": result.passed(),
                "expected_codes": sorted(codes),
                "matched": result.passed() == expected and codes.issubset(actual_codes),
            })
        for filename, expected, code in CGQA_CASES:
            path = roots["cgqa"] / "benchmarks/agent-payment-recovery-v0.1/cases" / filename
            payload = json.loads(path.read_text())
            native = cgqa_module.evaluate_payment_recovery_scenario(payload)
            actual_codes = {v["code"] for v in native["violations"]}
            results.append({
                "case": filename, "input": payload, "input_sha256": digest(path.read_bytes()),
                "native_result": native, "expected_verdict": expected,
                "expected_code": code,
                "matched": native["status"] == expected and (code is None or code in actual_codes),
            })
        return results

    first, second = evaluate(), evaluate()
    repeat_equal = canonical(first) == canonical(second)
    report = {
        "schema": "resonance.article016.native-seed-replay.v1",
        "scope": "Six existing synthetic trace cases; no LLM, provider, runtime enforcement or effect-count experiment",
        "source_commits": PINS, "python_version": platform.python_version(),
        "platform": platform.system(), "pyyaml_version": importlib.import_module("yaml").__version__,
        "source_python_sha256": source_hashes,
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "results_sha256": digest(canonical(first)), "repeat_equal": repeat_equal,
        "cases": first, "matched_cases": sum(row["matched"] for row in first),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ["matched_cases", "repeat_equal", "results_sha256"]}))
    if not repeat_equal or not all(row["matched"] for row in first):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
