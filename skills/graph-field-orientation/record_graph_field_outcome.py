#!/usr/bin/env python3
"""Validate and record an evidence-backed Graph–Field outcome before calibration.

This intake layer deliberately accepts a real outcome that is not yet calibration-
eligible. It preserves raw observed metrics and fails closed on attempts to turn an
unpaired observation into a weight update.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "resonance.graph-field-outcome.observation.v0.2"
RECEIPT_SCHEMA = "resonance.graph-field-outcome.intake.v0.2"
EXPECTED_SELECTION = "p2-1-trust-spine-cost-latency"
EXPECTED_SOURCE_RUN = 31879737027
EXPECTED_VERIFICATION_RUN = 31883970399
EXPECTED_MEASURED_SUBJECT = "7fd3e744037832b74b2ee4c4c71cc8fce18fc329"
EXPECTED_VERIFIER_SUBJECT = "447098344c71dd1e9dd11a69ef7767ddbe106ca0"


class OutcomeIntakeError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_object(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OutcomeIntakeError(f"{label} must be an object")
    return value


def _refs(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise OutcomeIntakeError(f"{label} must contain evidence references")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise OutcomeIntakeError(f"{label} entries must be non-empty strings")
        result.append(item.strip())
    return result


def _unit(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OutcomeIntakeError(f"{label} must be numeric in [0,1]")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise OutcomeIntakeError(f"{label} must be finite and in [0,1]")
    return value


def _false(value: object, label: str) -> None:
    if value is not False:
        raise OutcomeIntakeError(f"{label} must be false")


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA:
        raise OutcomeIntakeError("unsupported outcome observation schema")
    if payload.get("synthetic") is not False:
        raise OutcomeIntakeError("P2-1 real outcome must be synthetic=false")

    observation_id = payload.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id.strip():
        raise OutcomeIntakeError("observation_id is required")

    pre = _mapping(payload.get("pre_action"), "pre_action")
    if pre.get("selection_id") != EXPECTED_SELECTION:
        raise OutcomeIntakeError("pre_action selection does not match frozen P2-1 choice")
    score = _unit(pre.get("field_score"), "pre_action.field_score")
    if score != 0.800588:
        raise OutcomeIntakeError("pre_action field_score does not match frozen snapshot")
    components = _mapping(pre.get("components"), "pre_action.components")
    expected_components = {
        "divergence": 0.90,
        "uncertainty": 0.65,
        "blast_radius": 1.00,
        "freshness_gap": 0.40,
        "open_pressure": 0.70,
        "opportunity": 1.00,
        "blockedness": 0.05,
    }
    for name, expected in expected_components.items():
        if _unit(components.get(name), f"pre_action.components.{name}") != expected:
            raise OutcomeIntakeError(f"pre_action component drift: {name}")
    if set(components) != set(expected_components):
        raise OutcomeIntakeError("pre_action components contain unsupported fields")
    selection_refs = _refs(pre.get("selection_evidence"), "pre_action.selection_evidence")

    outcome = _mapping(payload.get("observed_outcome"), "observed_outcome")
    if outcome.get("status") != "MEASURED_AND_INDEPENDENTLY_VERIFIED":
        raise OutcomeIntakeError("real outcome must be independently verified")
    if outcome.get("repository") != "safal207/ContractGraph-QA" or outcome.get("pull_request") != 63:
        raise OutcomeIntakeError("outcome source repository/PR mismatch")
    if outcome.get("measured_subject") != EXPECTED_MEASURED_SUBJECT:
        raise OutcomeIntakeError("measured subject mismatch")
    if outcome.get("verifier_subject") != EXPECTED_VERIFIER_SUBJECT:
        raise OutcomeIntakeError("verifier subject mismatch")
    if outcome.get("source_workflow_run_id") != EXPECTED_SOURCE_RUN:
        raise OutcomeIntakeError("source workflow run mismatch")
    if outcome.get("verification_workflow_run_id") != EXPECTED_VERIFICATION_RUN:
        raise OutcomeIntakeError("verification workflow run mismatch")
    outcome_refs = _refs(outcome.get("evidence"), "observed_outcome.evidence")

    metrics = _mapping(outcome.get("metrics"), "observed_outcome.metrics")
    exact_metrics = {
        "job_elapsed_seconds": 45,
        "substantive_window_seconds": 35,
        "runner_overhead_seconds": 10,
        "substantive_step_count": 13,
        "source_evidence_artifact_bytes": 28222,
        "dominant_measurement_group": "liminaldb",
        "dominant_group_observed_seconds": 23,
        "timestamp_resolution_seconds": 1,
        "monetary_cost_status": "NOT_MEASURED",
        "monetary_cost_usd": None,
    }
    for name, expected in exact_metrics.items():
        if metrics.get(name) != expected:
            raise OutcomeIntakeError(f"observed metric mismatch: {name}")
    if set(metrics) != set(exact_metrics):
        raise OutcomeIntakeError("observed metrics contain unsupported fields")

    calibration = _mapping(payload.get("calibration"), "calibration")
    if calibration.get("utility_annotation_status") != "UNSCORED":
        raise OutcomeIntakeError("real outcome utility must remain UNSCORED until a frozen rubric is applied")
    if calibration.get("baseline_status") != "MISSING":
        raise OutcomeIntakeError("unpaired outcome baseline_status must be MISSING")
    if calibration.get("eligibility") != "BASELINE_REQUIRED":
        raise OutcomeIntakeError("unpaired outcome must remain BASELINE_REQUIRED")
    _false(calibration.get("weight_update_allowed"), "calibration.weight_update_allowed")

    authority = _mapping(payload.get("authority"), "authority")
    for field in (
        "may_authorize",
        "may_execute",
        "may_mutate",
        "merge_authorized",
        "deployment_authorized",
        "payment_authorized",
        "external_effects_authorized",
    ):
        _false(authority.get(field), f"authority.{field}")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
        "decision": "RECORDED_UNPAIRED",
        "observation_id": observation_id,
        "selection_id": EXPECTED_SELECTION,
        "field_score": score,
        "observed_outcome_status": outcome["status"],
        "measured_subject": outcome["measured_subject"],
        "verifier_subject": outcome["verifier_subject"],
        "source_workflow_run_id": outcome["source_workflow_run_id"],
        "verification_workflow_run_id": outcome["verification_workflow_run_id"],
        "dominant_measurement_group": metrics["dominant_measurement_group"],
        "dominant_group_observed_seconds": metrics["dominant_group_observed_seconds"],
        "job_elapsed_seconds": metrics["job_elapsed_seconds"],
        "substantive_window_seconds": metrics["substantive_window_seconds"],
        "source_evidence_artifact_bytes": metrics["source_evidence_artifact_bytes"],
        "monetary_cost_status": metrics["monetary_cost_status"],
        "selection_evidence": selection_refs,
        "outcome_evidence": outcome_refs,
        "calibration_eligibility": "BASELINE_REQUIRED",
        "weight_update_allowed": False,
        "next_required_check": "record a simpler observed routing baseline under the same frozen utility definition; do not infer baseline utility from this selected outcome",
    }
    return {**receipt, "receipt_digest": "sha256:" + sha256_object(receipt)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one real Graph–Field outcome before calibration")
    parser.add_argument("input", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise OutcomeIntakeError("top-level JSON must be an object")
        result = validate(payload)
    except (OSError, json.JSONDecodeError, OutcomeIntakeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
