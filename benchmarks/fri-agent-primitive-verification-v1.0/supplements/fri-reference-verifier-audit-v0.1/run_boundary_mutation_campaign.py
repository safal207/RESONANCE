#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
FRI_ROOT = HERE.parents[1]
EVALUATOR_PATH = FRI_ROOT / "run_fri_conformance.py"
AUDIT_FIXTURES = HERE / "fixtures.json"

COMPARE_MUTATIONS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}


def load_evaluate(tree: ast.AST, module_name: str) -> Callable[[str, dict[str, Any]], tuple[str, str]]:
    namespace: dict[str, Any] = {
        "__name__": module_name,
        "__file__": str(EVALUATOR_PATH),
    }
    ast.fix_missing_locations(tree)
    exec(compile(tree, str(EVALUATOR_PATH), "exec"), namespace)
    evaluate = namespace.get("evaluate")
    if not callable(evaluate):
        raise RuntimeError("mutated module does not expose evaluate()")
    return evaluate


def run_controls(
    evaluate: Callable[[str, dict[str, Any]], tuple[str, str]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for control in controls:
        try:
            actual, reason = evaluate(control["rule"], control["input"])
            passed = actual == control["expected"]
            results.append(
                {
                    "id": control["id"],
                    "expected": control["expected"],
                    "actual": actual,
                    "pass": passed,
                    "reason": reason,
                    "exception": None,
                }
            )
        except Exception as exc:  # a crashing mutant is still killed by the fixture set
            results.append(
                {
                    "id": control["id"],
                    "expected": control["expected"],
                    "actual": None,
                    "pass": False,
                    "reason": None,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            )
    return results


def is_rule_dispatch_test(node: ast.AST) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    if not isinstance(node.left, ast.Name) or node.left.id != "rule":
        return False
    return any(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in node.comparators)


def evaluate_function(tree: ast.Module) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate":
            return node
    raise RuntimeError("evaluate() function not found")


class SiteCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.compare_sites: list[dict[str, Any]] = []
        self.guard_sites: list[dict[str, Any]] = []
        self._compare_index = 0
        self._if_index = 0

    def visit_Compare(self, node: ast.Compare) -> None:
        if not is_rule_dispatch_test(node):
            for op_index, op in enumerate(node.ops):
                if type(op) in COMPARE_MUTATIONS:
                    self.compare_sites.append(
                        {
                            "site_index": self._compare_index,
                            "op_index": op_index,
                            "lineno": getattr(node, "lineno", None),
                            "col_offset": getattr(node, "col_offset", None),
                            "original_op": type(op).__name__,
                            "mutated_op": COMPARE_MUTATIONS[type(op)].__name__,
                            "source": ast.unparse(node),
                        }
                    )
            self._compare_index += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if not is_rule_dispatch_test(node.test):
            self.guard_sites.append(
                {
                    "site_index": self._if_index,
                    "lineno": getattr(node, "lineno", None),
                    "col_offset": getattr(node, "col_offset", None),
                    "source": ast.unparse(node.test),
                }
            )
            self._if_index += 1
        self.generic_visit(node)


class CompareMutator(ast.NodeTransformer):
    def __init__(self, target_compare_index: int, target_op_index: int) -> None:
        self.target_compare_index = target_compare_index
        self.target_op_index = target_op_index
        self._compare_index = 0

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        node = self.generic_visit(node)
        if is_rule_dispatch_test(node):
            return node
        current = self._compare_index
        self._compare_index += 1
        if current != self.target_compare_index:
            return node
        op = node.ops[self.target_op_index]
        replacement = COMPARE_MUTATIONS.get(type(op))
        if replacement is None:
            raise RuntimeError(f"unsupported compare operator: {type(op).__name__}")
        node.ops[self.target_op_index] = replacement()
        return node


class GuardMutator(ast.NodeTransformer):
    def __init__(self, target_if_index: int, mode: str) -> None:
        self.target_if_index = target_if_index
        self.mode = mode
        self._if_index = 0

    def visit_If(self, node: ast.If) -> ast.AST:
        if is_rule_dispatch_test(node.test):
            return self.generic_visit(node)
        current = self._if_index
        self._if_index += 1
        if current == self.target_if_index:
            if self.mode == "bypass":
                node.test = ast.Constant(value=False)
            elif self.mode == "negate":
                node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            else:
                raise RuntimeError(f"unknown guard mutation mode: {self.mode}")
        return self.generic_visit(node)


def mutate_compare(tree: ast.Module, site: dict[str, Any]) -> ast.Module:
    mutated = copy.deepcopy(tree)
    evaluate = evaluate_function(mutated)
    CompareMutator(site["site_index"], site["op_index"]).visit(evaluate)
    return mutated


def mutate_guard(tree: ast.Module, site: dict[str, Any], mode: str) -> ast.Module:
    mutated = copy.deepcopy(tree)
    evaluate = evaluate_function(mutated)
    GuardMutator(site["site_index"], mode).visit(evaluate)
    return mutated


def mutant_result(
    mutant_id: str,
    family: str,
    metadata: dict[str, Any],
    tree: ast.Module,
    controls: list[dict[str, Any]],
) -> dict[str, Any]:
    results = run_controls(load_evaluate(tree, f"fri_auto_mutant_{mutant_id}"), controls)
    failing = [item["id"] for item in results if not item["pass"]]
    return {
        "id": mutant_id,
        "family": family,
        "status": "KILLED" if failing else "SURVIVED",
        "killed_by_controls": failing,
        **metadata,
    }


def summarize(mutants: list[dict[str, Any]]) -> dict[str, Any]:
    killed = sum(item["status"] == "KILLED" for item in mutants)
    total = len(mutants)
    return {
        "killed": killed,
        "survived": total - killed,
        "total": total,
        "mutation_score": killed / total if total else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automatically mutate FRI evaluator boundaries and guards and require the audit fixtures to kill them."
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--required-score",
        type=float,
        default=1.0,
        help="Required aggregate kill score for generated mutants (default: 1.0).",
    )
    args = parser.parse_args()

    source = EVALUATOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EVALUATOR_PATH))
    controls = json.loads(AUDIT_FIXTURES.read_text(encoding="utf-8"))["controls"]

    baseline_results = run_controls(load_evaluate(copy.deepcopy(tree), "fri_boundary_baseline"), controls)
    baseline_failures = [item["id"] for item in baseline_results if not item["pass"]]
    if baseline_failures:
        report = {
            "benchmark": "FRI Automatic Boundary Mutation Campaign",
            "version": "0.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {"status": "FAIL_BASELINE_NOT_GREEN"},
            "baseline_failures": baseline_failures,
            "mutants": [],
        }
        text = json.dumps(report, indent=2, sort_keys=True)
        print(text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return 1

    collector = SiteCollector()
    collector.visit(evaluate_function(tree))

    mutants: list[dict[str, Any]] = []
    for n, site in enumerate(collector.compare_sites, start=1):
        mutants.append(
            mutant_result(
                f"AUTO-CMP-{n:02d}",
                "boundary_compare",
                site,
                mutate_compare(tree, site),
                controls,
            )
        )

    for mode in ("bypass", "negate"):
        for n, site in enumerate(collector.guard_sites, start=1):
            mutants.append(
                mutant_result(
                    f"AUTO-GUARD-{mode.upper()}-{n:02d}",
                    f"guard_{mode}",
                    site,
                    mutate_guard(tree, site, mode),
                    controls,
                )
            )

    aggregate = summarize(mutants)
    families = {
        family: summarize([item for item in mutants if item["family"] == family])
        for family in sorted({item["family"] for item in mutants})
    }
    status = "PASS" if aggregate["mutation_score"] >= args.required_score else "FAIL"

    report = {
        "benchmark": "FRI Automatic Boundary Mutation Campaign",
        "version": "0.1",
        "scope": (
            "AST-generated comparison-boundary flips plus non-dispatch guard bypass/negation inside evaluate(); "
            "rule-dispatch comparisons are excluded to avoid trivial score inflation; order-inversion mutants are not yet gated"
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            **aggregate,
            "required_score": args.required_score,
            "compare_sites": len(collector.compare_sites),
            "guard_sites": len(collector.guard_sites),
            "status": status,
        },
        "families": families,
        "baseline_audit": "PASS",
        "mutants": mutants,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
