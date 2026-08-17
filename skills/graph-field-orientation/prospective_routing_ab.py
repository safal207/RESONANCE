#!/usr/bin/env python3
"""Freeze and verify a prospective GFD-vs-FIFO routing experiment.

This module is intentionally read-only and non-authorizing. It verifies that
candidate selection and the utility rubric are fixed before any outcome is
recorded. It does not execute either selected work item and it cannot update
Graph–Field weights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from score_graph_field import GFDInputError, score

SCHEMA = "resonance.graph-field-routing-ab.freeze.v0.1"
RECEIPT_SCHEMA = "resonance.graph-field-routing-ab.freeze-receipt.v0.1"
COMPLETED_P2_1 = "p2-1-trust-spine-cost-latency"
UTILITY_WEIGHTS = {
    "useful_finding": 0.30,
    "information_gain": 0.25,
    "blocked_work_avoidance": 0.15,
    "stale_evidence_catch": 0.10,
    "downstream_rework_avoidance": 0.20,
}


class RoutingFreezeError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_object(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RoutingFreezeError(f"{field} must be a non-empty string")
    return value.strip()


def _timestamp(value: Any, field: str) -> datetime:
    text = _text(value, field)
    if not text.endswith("Z"):
        raise RoutingFreezeError(f"{field} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise RoutingFreezeError(f"{field} is not a valid ISO-8601 timestamp") from exc
    return parsed


def _false(value: Any, field: str) -> None:
    if value is not False:
        raise RoutingFreezeError(f"{field} must be false")


def _validate_authority(payload: dict[str, Any]) -> None:
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise RoutingFreezeError("authority must be an object")
    if authority.get("mode") != "ADVISORY_ONLY":
        raise RoutingFreezeError("authority.mode must be ADVISORY_ONLY")
    for name in (
        "authority_granted",
        "may_execute",
        "may_mutate",
        "may_merge",
        "may_deploy",
        "may_pay",
        "may_change_weights",
    ):
        _false(authority.get(name), f"authority.{name}")


def _validate_utility(payload: dict[str, Any]) -> dict[str, float]:
    utility = payload.get("utility")
    if not isinstance(utility, dict):
        raise RoutingFreezeError("utility must be an object")
    dimensions = utility.get("dimensions")
    if not isinstance(dimensions, dict):
        raise RoutingFreezeError("utility.dimensions must be an object")
    if set(dimensions) != set(UTILITY_WEIGHTS):
        raise RoutingFreezeError("utility dimensions differ from the frozen calibration rubric")

    observed: dict[str, float] = {}
    for name, expected in UTILITY_WEIGHTS.items():
        dimension = dimensions.get(name)
        if not isinstance(dimension, dict):
            raise RoutingFreezeError(f"utility.dimensions.{name} must be an object")
        weight = dimension.get("weight")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise RoutingFreezeError(f"utility.dimensions.{name}.weight must be numeric")
        weight = float(weight)
        if not math.isclose(weight, expected, abs_tol=1e-12):
            raise RoutingFreezeError(f"utility.dimensions.{name}.weight drifted from {expected}")
        levels = dimension.get("levels")
        if not isinstance(levels, dict) or len(levels) < 2:
            raise RoutingFreezeError(f"utility.dimensions.{name}.levels must be predeclared")
        observed[name] = weight

    if not math.isclose(sum(observed.values()), 1.0, abs_tol=1e-12):
        raise RoutingFreezeError("utility weights must sum to 1.0")
    return observed


def _validate_nodes(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, datetime]]:
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise RoutingFreezeError("nodes must be a non-empty list")

    seen: set[str] = set()
    ready_times: dict[str, datetime] = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise RoutingFreezeError(f"nodes[{index}] must be an object")
        node_id = _text(node.get("id"), f"nodes[{index}].id")
        if node_id in seen:
            raise RoutingFreezeError(f"duplicate node id: {node_id}")
        if node_id == COMPLETED_P2_1:
            raise RoutingFreezeError("completed P2-1 must not appear in the active prospective candidate set")
        seen.add(node_id)
        if not isinstance(node.get("eligible"), bool):
            raise RoutingFreezeError(f"{node_id}.eligible must be boolean")
        ready_times[node_id] = _timestamp(node.get("ready_since"), f"{node_id}.ready_since")
        evidence = node.get("ready_evidence")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
            raise RoutingFreezeError(f"{node_id}.ready_evidence must contain non-empty strings")
        if node["eligible"] is False and not isinstance(node.get("blocked_reason"), str):
            raise RoutingFreezeError(f"{node_id}.blocked_reason is required when ineligible")

    completed = payload.get("completed_nodes_excluded")
    if not isinstance(completed, list) or COMPLETED_P2_1 not in completed:
        raise RoutingFreezeError("completed_nodes_excluded must preserve P2-1 exclusion")
    return nodes, ready_times


def freeze(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA:
        raise RoutingFreezeError("unsupported prospective routing freeze schema")
    if payload.get("frozen_before_outcome") is not True:
        raise RoutingFreezeError("frozen_before_outcome must be true")
    if payload.get("outcomes") is not None:
        raise RoutingFreezeError("freeze fixture must not contain post-selection outcomes")
    _text(payload.get("experiment_id"), "experiment_id")
    _timestamp(payload.get("frozen_at"), "frozen_at")
    revision = _text(payload.get("pre_experiment_gfd_revision"), "pre_experiment_gfd_revision")
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise RoutingFreezeError("pre_experiment_gfd_revision must be a full lowercase Git SHA")

    _validate_authority(payload)
    utility_weights = _validate_utility(payload)
    nodes, ready_times = _validate_nodes(payload)

    eligible_ids = {node["id"] for node in nodes if node["eligible"] is True}
    if not eligible_ids:
        raise RoutingFreezeError("prospective experiment needs at least one eligible node")

    graph_payload = {
        "diffusion_alpha": payload.get("diffusion_alpha", 0.1),
        "nodes": nodes,
        "edges": payload.get("edges", []),
    }
    try:
        gfd = score(graph_payload)
    except GFDInputError as exc:
        raise RoutingFreezeError(str(exc)) from exc

    eligible_ranking = [item for item in gfd["ranking"] if item["id"] in eligible_ids]
    treatment_selected = eligible_ranking[0]

    treatment = payload.get("treatment")
    if not isinstance(treatment, dict) or treatment.get("kind") != "GFD_ORIENTATION_V0_1":
        raise RoutingFreezeError("treatment.kind must be GFD_ORIENTATION_V0_1")
    expected_treatment = _text(treatment.get("expected_selection"), "treatment.expected_selection")
    if treatment_selected["id"] != expected_treatment:
        raise RoutingFreezeError(
            f"treatment selection drift: expected {expected_treatment}, got {treatment_selected['id']}"
        )
    expected_score = treatment.get("expected_field_score")
    if isinstance(expected_score, bool) or not isinstance(expected_score, (int, float)):
        raise RoutingFreezeError("treatment.expected_field_score must be numeric")
    if not math.isclose(treatment_selected["field_score"], float(expected_score), abs_tol=1e-6):
        raise RoutingFreezeError("treatment field score drifted after freeze")

    fifo_selected = min(
        (node for node in nodes if node["eligible"] is True),
        key=lambda node: (ready_times[node["id"]], node["id"]),
    )
    baseline = payload.get("baseline")
    if not isinstance(baseline, dict) or baseline.get("kind") != "FIFO_READY_NODE":
        raise RoutingFreezeError("baseline.kind must be FIFO_READY_NODE")
    if baseline.get("tie_break") != "node_id_ascending":
        raise RoutingFreezeError("baseline tie_break must be node_id_ascending")
    expected_baseline = _text(baseline.get("expected_selection"), "baseline.expected_selection")
    if fifo_selected["id"] != expected_baseline:
        raise RoutingFreezeError(
            f"baseline selection drift: expected {expected_baseline}, got {fifo_selected['id']}"
        )

    digest = "sha256:" + sha256_object(payload)
    return {
        "schema": RECEIPT_SCHEMA,
        "status": "FROZEN_BEFORE_OUTCOME",
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
        "experiment_id": payload["experiment_id"],
        "freeze_digest": digest,
        "pre_experiment_gfd_revision": revision,
        "active_candidate_count": len(nodes),
        "eligible_candidate_count": len(eligible_ids),
        "treatment": {
            "kind": treatment["kind"],
            "selection_id": treatment_selected["id"],
            "field_score": treatment_selected["field_score"],
            "tension": treatment_selected["tension"],
        },
        "baseline": {
            "kind": baseline["kind"],
            "selection_id": fifo_selected["id"],
            "ready_since": fifo_selected["ready_since"],
        },
        "utility_weights": utility_weights,
        "outcome_recording_allowed": True,
        "calibration_allowed": False,
        "weight_update_allowed": False,
        "next_required_transition": "observe both frozen arms under the same predeclared utility rubric",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze a prospective GFD-vs-FIFO routing A/B")
    parser.add_argument("input", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RoutingFreezeError("top-level JSON must be an object")
        result = freeze(payload)
    except (OSError, json.JSONDecodeError, RoutingFreezeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
