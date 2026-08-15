#!/usr/bin/env python3
"""Evaluate a frozen prospective GFD-vs-FIFO routing observation pair.

Normalized utility is derived mechanically from raw counters under the rubric
that was frozen before outcomes. The evaluator is advisory only and emits one
calibration-compatible observation; it never mutates Graph–Field weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from prospective_routing_ab import RoutingFreezeError, freeze

OBSERVATION_SCHEMA = "resonance.graph-field-routing-ab.observations.v0.1"
RESULT_SCHEMA = "resonance.graph-field-routing-ab.result.v0.1"
UTILITY_WEIGHTS = {
    "useful_finding": 0.30,
    "information_gain": 0.25,
    "blocked_work_avoidance": 0.15,
    "stale_evidence_catch": 0.10,
    "downstream_rework_avoidance": 0.20,
}
COMPONENTS = (
    "divergence",
    "uncertainty",
    "blast_radius",
    "freshness_gap",
    "open_pressure",
    "opportunity",
)


class RoutingOutcomeError(ValueError):
    pass


def _false(value: Any, field: str) -> None:
    if value is not False:
        raise RoutingOutcomeError(f"{field} must be false")


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RoutingOutcomeError(f"{field} must be a non-negative integer")
    return value


def _evidence(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RoutingOutcomeError(f"{field} must contain at least one evidence reference")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise RoutingOutcomeError(f"{field} entries must be non-empty strings")
        result.append(item.strip())
    return result


def normalize_raw(raw: dict[str, Any], prefix: str) -> dict[str, float]:
    actionable = raw.get("actionable_finding")
    confirmation_only = raw.get("state_confirmation_only")
    if not isinstance(actionable, bool) or not isinstance(confirmation_only, bool):
        raise RoutingOutcomeError(f"{prefix}: finding flags must be boolean")
    if actionable and confirmation_only:
        raise RoutingOutcomeError(f"{prefix}: actionable_finding and state_confirmation_only are mutually exclusive")

    affected = _non_negative_int(raw.get("affected_work_items"), f"{prefix}.affected_work_items")
    avoided = _non_negative_int(
        raw.get("blocked_or_stale_actions_avoided"),
        f"{prefix}.blocked_or_stale_actions_avoided",
    )
    stale = raw.get("stale_evidence_drift_found")
    if not isinstance(stale, bool):
        raise RoutingOutcomeError(f"{prefix}.stale_evidence_drift_found must be boolean")
    redirected = _non_negative_int(
        raw.get("downstream_reviews_or_actions_redirected"),
        f"{prefix}.downstream_reviews_or_actions_redirected",
    )

    useful_finding = 1.0 if actionable else 0.5 if confirmation_only else 0.0
    if affected >= 3:
        information_gain = 1.0
    elif affected == 1:
        information_gain = 0.5
    elif affected == 0:
        information_gain = 0.0
    else:
        raise RoutingOutcomeError(
            f"{prefix}.affected_work_items=2 is outside the predeclared rubric; record a more specific unit"
        )

    blocked_work_avoidance = 1.0 if avoided >= 2 else 0.5 if avoided == 1 else 0.0
    stale_evidence_catch = 1.0 if stale else 0.0
    downstream_rework_avoidance = 1.0 if redirected >= 3 else 0.5 if redirected >= 1 else 0.0

    return {
        "useful_finding": useful_finding,
        "information_gain": information_gain,
        "blocked_work_avoidance": blocked_work_avoidance,
        "stale_evidence_catch": stale_evidence_catch,
        "downstream_rework_avoidance": downstream_rework_avoidance,
    }


def utility(dimensions: dict[str, float]) -> float:
    return round(sum(UTILITY_WEIGHTS[name] * dimensions[name] for name in UTILITY_WEIGHTS), 6)


def _validate_authority(payload: dict[str, Any]) -> None:
    authority = payload.get("authority")
    if not isinstance(authority, dict) or authority.get("mode") != "ADVISORY_ONLY":
        raise RoutingOutcomeError("authority must be ADVISORY_ONLY")
    for field in (
        "authority_granted",
        "may_execute",
        "may_mutate",
        "may_merge",
        "may_close_pr",
        "may_change_weights",
    ):
        _false(authority.get(field), f"authority.{field}")


def _arm(payload: dict[str, Any], name: str, expected_selection: str) -> dict[str, Any]:
    arm = payload.get(name)
    if not isinstance(arm, dict):
        raise RoutingOutcomeError(f"{name} must be an object")
    if arm.get("selection_id") != expected_selection:
        raise RoutingOutcomeError(
            f"{name}.selection_id must match frozen selection {expected_selection}"
        )
    finding = arm.get("finding")
    if not isinstance(finding, str) or not finding.strip():
        raise RoutingOutcomeError(f"{name}.finding must be non-empty")
    raw = arm.get("raw")
    if not isinstance(raw, dict):
        raise RoutingOutcomeError(f"{name}.raw must be an object")
    refs = _evidence(arm.get("evidence"), f"{name}.evidence")
    dimensions = normalize_raw(raw, f"{name}.raw")
    return {
        "selection_id": expected_selection,
        "finding": finding.strip(),
        "raw": raw,
        "normalized": dimensions,
        "utility": utility(dimensions),
        "evidence": refs,
        "non_claims": arm.get("non_claims", []),
    }


def evaluate(freeze_payload: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    try:
        frozen = freeze(freeze_payload)
    except RoutingFreezeError as exc:
        raise RoutingOutcomeError(f"invalid freeze: {exc}") from exc

    if observations.get("schema") != OBSERVATION_SCHEMA:
        raise RoutingOutcomeError("unsupported observation schema")
    if observations.get("experiment_id") != frozen["experiment_id"]:
        raise RoutingOutcomeError("observation experiment_id does not match frozen experiment")
    if observations.get("observation_mode") != "READ_ONLY_INVESTIGATION":
        raise RoutingOutcomeError("observation_mode must be READ_ONLY_INVESTIGATION")
    _validate_authority(observations)

    treatment = _arm(
        observations,
        "treatment",
        frozen["treatment"]["selection_id"],
    )
    baseline = _arm(
        observations,
        "baseline",
        frozen["baseline"]["selection_id"],
    )
    advantage = round(treatment["utility"] - baseline["utility"], 6)
    winner = "TREATMENT" if advantage > 0 else "BASELINE" if advantage < 0 else "TIE"

    treatment_node = next(
        node for node in freeze_payload["nodes"] if node["id"] == treatment["selection_id"]
    )
    selection_components = {name: treatment_node[name] for name in COMPONENTS}

    calibration_observation = {
        "selection": {
            "id": treatment["selection_id"],
            "components": selection_components,
        },
        "outcome": {
            **treatment["normalized"],
            "evidence": treatment["evidence"],
        },
        "baseline": {
            "kind": frozen["baseline"]["kind"],
            "observed_utility": baseline["utility"],
            "evidence": baseline["evidence"],
        },
        "synthetic": False,
    }

    return {
        "schema": RESULT_SCHEMA,
        "decision": "PAIRED_OBSERVED",
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
        "experiment_id": frozen["experiment_id"],
        "freeze_digest": frozen["freeze_digest"],
        "treatment": treatment,
        "baseline": baseline,
        "advantage": advantage,
        "winner": winner,
        "paired_observation_count": 1,
        "calibration_confidence": "INSUFFICIENT",
        "weight_update_allowed": False,
        "calibration_observation": calibration_observation,
        "interpretation": "one prospective pair is evidence for calibration mechanics, not validation of GFD",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate prospective GFD-vs-FIFO observations")
    parser.add_argument("freeze", type=Path)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        freeze_payload = json.loads(args.freeze.read_text(encoding="utf-8"))
        observations = json.loads(args.observations.read_text(encoding="utf-8"))
        if not isinstance(freeze_payload, dict) or not isinstance(observations, dict):
            raise RoutingOutcomeError("both inputs must be JSON objects")
        result = evaluate(freeze_payload, observations)
    except (OSError, json.JSONDecodeError, RoutingOutcomeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
