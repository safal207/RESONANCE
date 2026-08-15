#!/usr/bin/env python3
"""Deterministic Generation-N crash simulator for Recovery Integrity v0.1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from validate import validate


@dataclass(frozen=True)
class GenerationCase:
    name: str
    authority_generation: int
    projection_generation: Optional[int]
    projection_present: bool = True
    projection_readable: bool = True
    projection_checksum_valid: bool = True


@dataclass(frozen=True)
class SimulationResult:
    name: str
    projection_state: str
    rebuild_decision: str
    execution_decision: str
    validator_errors: tuple[str, ...]


def classify_projection(case: GenerationCase) -> str:
    if not case.projection_present:
        return "MISSING"
    if not case.projection_readable or not case.projection_checksum_valid:
        return "CORRUPT"
    if case.projection_generation is None:
        return "UNPROVABLE"
    if case.projection_generation == case.authority_generation:
        return "HEALTHY"
    if case.projection_generation < case.authority_generation:
        return "STALE"
    return "UNPROVABLE"


def rebuild_decision(state: str) -> str:
    if state == "HEALTHY":
        return "NO_REBUILD"
    if state in {"MISSING", "STALE", "CORRUPT"}:
        return "ALLOW_REBUILD"
    return "HOLD"


def make_record(case: GenerationCase) -> dict:
    state = classify_projection(case)
    rebuild = rebuild_decision(state)
    preserved = None
    if state in {"STALE", "CORRUPT"}:
        preserved = f"sim://{case.name}/projection-before-recovery"

    return {
        "protocol_version": "recovery-integrity-v0.1",
        "recovery_id": f"generation-sim-{case.name}",
        "source_case_ref": "sim://generation-n-crash",
        "authority": {
            "source_ref": f"sim://{case.name}/authority",
            "generation": case.authority_generation,
            "integrity": "VALID",
        },
        "projection": {
            "source_ref": f"sim://{case.name}/projection",
            "generation": case.projection_generation,
            "state": state,
            "preserved_broken_ref": preserved,
        },
        "rollout": {
            "source_ref": f"sim://{case.name}/rollout",
            "integrity": "UNKNOWN",
            "continuation_proof": "NOT_PROVEN",
        },
        "last_committed_action_ref": None,
        "pending_action_ref": None,
        "external_side_effect_state": "UNKNOWN",
        "current_authority_proof": "NOT_PROVEN",
        "decision": {
            "rebuild_projection": rebuild,
            "execution_continuation": "HOLD",
        },
        "evidence_refs": [f"sim://{case.name}/generation-evidence"],
        "verifier": {
            "verifier_id": "resonance-generation-n-simulator-v0.1",
            "mode": "read-only",
        },
        "pre_recovery_snapshot_ref": f"sim://{case.name}/pre",
        "post_recovery_snapshot_ref": None,
        "observed_outcome": {
            "status": "NOT_OBSERVED",
            "outcome_ref": None,
        },
    }


def simulate(case: GenerationCase) -> SimulationResult:
    record = make_record(case)
    errors = tuple(validate(record))
    return SimulationResult(
        name=case.name,
        projection_state=record["projection"]["state"],
        rebuild_decision=record["decision"]["rebuild_projection"],
        execution_decision=record["decision"]["execution_continuation"],
        validator_errors=errors,
    )


CANONICAL_CASES = (
    GenerationCase("healthy", authority_generation=42, projection_generation=42),
    GenerationCase("stale", authority_generation=42, projection_generation=41),
    GenerationCase(
        "corrupt",
        authority_generation=42,
        projection_generation=42,
        projection_checksum_valid=False,
    ),
    GenerationCase("split-generation", authority_generation=41, projection_generation=42),
)


def main() -> int:
    failures = 0
    print("case             projection    rebuild          execution   validator")
    print("-" * 77)
    for case in CANONICAL_CASES:
        result = simulate(case)
        status = "PASS" if not result.validator_errors else "FAIL"
        if result.validator_errors:
            failures += 1
        print(
            f"{result.name:16} "
            f"{result.projection_state:13} "
            f"{result.rebuild_decision:16} "
            f"{result.execution_decision:11} "
            f"{status}"
        )
        for error in result.validator_errors:
            print(f"  - {error}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
