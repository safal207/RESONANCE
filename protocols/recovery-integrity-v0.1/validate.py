#!/usr/bin/env python3
"""Semantic validator for RecoveryIntegrityRecord v0.1.

No third-party packages are required. This validator checks the load-bearing
semantic invariants that JSON Schema alone does not express.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


VALID_PROJECTION_STATES = {"HEALTHY", "MISSING", "STALE", "CORRUPT", "UNPROVABLE"}
VALID_REBUILD = {"ALLOW_REBUILD", "NO_REBUILD", "HOLD"}
VALID_CONTINUATION = {"ALLOW_FORK", "NO_CONTINUATION", "HOLD"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(record: dict) -> list[str]:
    errors: list[str] = []

    if record.get("protocol_version") != "recovery-integrity-v0.1":
        fail(errors, "protocol_version must be recovery-integrity-v0.1")

    projection = record.get("projection") or {}
    authority = record.get("authority") or {}
    rollout = record.get("rollout") or {}
    decision = record.get("decision") or {}
    verifier = record.get("verifier") or {}
    outcome = record.get("observed_outcome") or {}

    pstate = projection.get("state")
    if pstate not in VALID_PROJECTION_STATES:
        fail(errors, f"invalid projection.state: {pstate!r}")

    rebuild = decision.get("rebuild_projection")
    continuation = decision.get("execution_continuation")
    if rebuild not in VALID_REBUILD:
        fail(errors, f"invalid rebuild decision: {rebuild!r}")
    if continuation not in VALID_CONTINUATION:
        fail(errors, f"invalid execution decision: {continuation!r}")

    # I1/I2: a known generation mismatch cannot be called HEALTHY.
    agen = authority.get("generation")
    pgen = projection.get("generation")
    if agen is not None and pgen is not None and agen != pgen and pstate == "HEALTHY":
        fail(errors, "generation mismatch cannot have projection.state=HEALTHY")

    # I3: stale/corrupt evidence must be preservable before a rebuild is authorized.
    if rebuild == "ALLOW_REBUILD" and pstate in {"STALE", "CORRUPT"}:
        if not projection.get("preserved_broken_ref"):
            fail(errors, "ALLOW_REBUILD for STALE/CORRUPT requires preserved_broken_ref")

    # I4: invalid authoritative evidence cannot authorize rebuild.
    if rebuild == "ALLOW_REBUILD" and authority.get("integrity") == "INVALID":
        fail(errors, "ALLOW_REBUILD is forbidden when authority.integrity=INVALID")

    # I5/I6: rebuild permission never grants continuation permission.
    if continuation == "ALLOW_FORK":
        if rollout.get("continuation_proof") != "PROVEN":
            fail(errors, "ALLOW_FORK requires rollout.continuation_proof=PROVEN")
        if record.get("external_side_effect_state") in {"AMBIGUOUS", "UNKNOWN"}:
            fail(errors, "ALLOW_FORK forbidden with ambiguous/unknown external side effects")
        if record.get("current_authority_proof") not in {"PROVEN", "NOT_REQUIRED"}:
            fail(errors, "ALLOW_FORK requires current authority proven or explicitly not required")

    # I7: verifier is read-only; verification and mutation are separate.
    if verifier.get("mode") != "read-only":
        fail(errors, "verifier.mode must be read-only")

    # I8: outcome is separate from pre-recovery verdict and must always be explicit.
    if not isinstance(outcome, dict) or "status" not in outcome:
        fail(errors, "observed_outcome.status is required")

    # Basic evidence presence.
    if not record.get("evidence_refs"):
        fail(errors, "at least one evidence_ref is required")
    if not record.get("recovery_id"):
        fail(errors, "recovery_id is required")
    if not record.get("source_case_ref"):
        fail(errors, "source_case_ref is required")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate.py <recovery-integrity-record.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    record = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(record)

    if errors:
        print("FAIL recovery-integrity-v0.1")
        for item in errors:
            print(f"- {item}")
        return 1

    print("PASS recovery-integrity-v0.1")
    print(f"projection={record['projection']['state']}")
    print(f"projection_decision={record['decision']['rebuild_projection']}")
    print(f"execution_decision={record['decision']['execution_continuation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
