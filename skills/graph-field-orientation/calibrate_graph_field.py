#!/usr/bin/env python3
"""Produce bounded Graph–Field weight calibration proposals from observed outcomes.

The calibrator is advisory only. It never edits the canonical scorer weights and
never grants execution, merge, deployment, payment, or security authority.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

COMPONENTS = (
    "divergence",
    "uncertainty",
    "blast_radius",
    "freshness_gap",
    "open_pressure",
    "opportunity",
)

OUTCOME_WEIGHTS = {
    "useful_finding": 0.30,
    "information_gain": 0.25,
    "blocked_work_avoidance": 0.15,
    "stale_evidence_catch": 0.10,
    "downstream_rework_avoidance": 0.20,
}

DEFAULT_WEIGHTS = {
    "divergence": 0.25,
    "uncertainty": 0.20,
    "blast_radius": 0.20,
    "freshness_gap": 0.15,
    "open_pressure": 0.10,
    "opportunity": 0.10,
}

MAX_LEARNING_RATE = 0.10
MIN_RAW_WEIGHT = 1e-9


class CalibrationInputError(ValueError):
    pass


def _unit(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalibrationInputError(f"{field} must be numeric in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise CalibrationInputError(f"{field} must be finite and in [0, 1]")
    return value


def _refs(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CalibrationInputError(f"{field} must contain at least one evidence reference")
    refs: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CalibrationInputError(f"{field} entries must be non-empty strings")
        refs.append(item)
    return refs


def _weights(value: Any) -> dict[str, float]:
    if value is None:
        result = dict(DEFAULT_WEIGHTS)
    elif not isinstance(value, dict):
        raise CalibrationInputError("current_weights must be an object")
    else:
        result = {}
        for component in COMPONENTS:
            if component not in value:
                raise CalibrationInputError(f"current_weights missing {component}")
            result[component] = _unit(value[component], f"current_weights.{component}")
        extras = set(value) - set(COMPONENTS)
        if extras:
            raise CalibrationInputError(f"current_weights has unsupported components: {sorted(extras)}")

    total = sum(result.values())
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise CalibrationInputError("current_weights must sum to 1.0")
    return result


def _outcome_utility(outcome: dict[str, Any], prefix: str) -> float:
    return sum(
        OUTCOME_WEIGHTS[name] * _unit(outcome.get(name), f"{prefix}.{name}")
        for name in OUTCOME_WEIGHTS
    )


def _confidence(count: int) -> str:
    if count < 5:
        return "INSUFFICIENT"
    if count < 20:
        return "NASCENT"
    return "EVALUATE_ON_HOLDOUT"


def calibrate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != "resonance.graph-field-calibration.batch.v0.2":
        raise CalibrationInputError("unsupported calibration batch schema")

    current = _weights(payload.get("current_weights"))
    learning_rate = _unit(payload.get("learning_rate", 0.05), "learning_rate")
    if learning_rate > MAX_LEARNING_RATE:
        raise CalibrationInputError(f"learning_rate must be <= {MAX_LEARNING_RATE}")

    observations = payload.get("observations")
    if not isinstance(observations, list) or not observations:
        raise CalibrationInputError("observations must be a non-empty list")

    signals = {component: [] for component in COMPONENTS}
    summaries = []

    for index, observation in enumerate(observations):
        prefix = f"observations[{index}]"
        if not isinstance(observation, dict):
            raise CalibrationInputError(f"{prefix} must be an object")

        selection = observation.get("selection")
        if not isinstance(selection, dict):
            raise CalibrationInputError(f"{prefix}.selection must be an object")
        node_id = selection.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise CalibrationInputError(f"{prefix}.selection.id is required")

        components_raw = selection.get("components")
        if not isinstance(components_raw, dict):
            raise CalibrationInputError(f"{prefix}.selection.components must be an object")
        components = {
            component: _unit(components_raw.get(component), f"{prefix}.selection.components.{component}")
            for component in COMPONENTS
        }

        outcome = observation.get("outcome")
        if not isinstance(outcome, dict):
            raise CalibrationInputError(f"{prefix}.outcome must be an object")
        outcome_refs = _refs(outcome.get("evidence"), f"{prefix}.outcome.evidence")
        utility = _outcome_utility(outcome, f"{prefix}.outcome")

        baseline = observation.get("baseline")
        if not isinstance(baseline, dict):
            raise CalibrationInputError(f"{prefix}.baseline must be an object")
        baseline_kind = baseline.get("kind")
        if not isinstance(baseline_kind, str) or not baseline_kind.strip():
            raise CalibrationInputError(f"{prefix}.baseline.kind is required")
        baseline_utility = _unit(baseline.get("observed_utility"), f"{prefix}.baseline.observed_utility")
        baseline_refs = _refs(baseline.get("evidence"), f"{prefix}.baseline.evidence")

        weighted_mean = sum(current[c] * components[c] for c in COMPONENTS)
        advantage = utility - baseline_utility
        for component in COMPONENTS:
            signals[component].append(advantage * (components[component] - weighted_mean))

        summaries.append(
            {
                "selection_id": node_id,
                "observed_utility": round(utility, 6),
                "baseline_kind": baseline_kind,
                "baseline_utility": round(baseline_utility, 6),
                "advantage": round(advantage, 6),
                "outcome_evidence": outcome_refs,
                "baseline_evidence": baseline_refs,
                "synthetic": bool(observation.get("synthetic", False)),
            }
        )

    mean_signal = {
        component: sum(values) / len(values)
        for component, values in signals.items()
    }
    raw = {
        component: max(
            MIN_RAW_WEIGHT,
            current[component] * (1.0 + learning_rate * mean_signal[component]),
        )
        for component in COMPONENTS
    }
    raw_total = sum(raw.values())
    proposed = {component: raw[component] / raw_total for component in COMPONENTS}

    deltas = {component: proposed[component] - current[component] for component in COMPONENTS}
    mean_advantage = sum(item["advantage"] for item in summaries) / len(summaries)

    return {
        "schema": "resonance.graph-field-calibration.proposal.v0.2",
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
        "apply_recommended": False,
        "observation_count": len(summaries),
        "confidence": _confidence(len(summaries)),
        "learning_rate": learning_rate,
        "utility_weights": OUTCOME_WEIGHTS,
        "current_weights": {k: round(v, 9) for k, v in current.items()},
        "mean_component_signal": {k: round(v, 9) for k, v in mean_signal.items()},
        "proposed_weights": {k: round(v, 9) for k, v in proposed.items()},
        "weight_deltas": {k: round(v, 9) for k, v in deltas.items()},
        "mean_advantage": round(mean_advantage, 6),
        "observations": summaries,
        "next_required_check": "evaluate proposed weights on held-out observations before any configuration change",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce a bounded Graph–Field calibration proposal")
    parser.add_argument("input", type=Path, help="Calibration batch JSON")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise CalibrationInputError("top-level JSON must be an object")
        result = calibrate(payload)
    except (OSError, json.JSONDecodeError, CalibrationInputError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
