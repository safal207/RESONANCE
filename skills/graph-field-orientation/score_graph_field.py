#!/usr/bin/env python3
"""Deterministic Graph–Field Dynamics v0.1 scorer.

The scorer is advisory only. It ranks candidate work nodes/transitions and
does not grant execution, merge, deployment, or security authority.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

WEIGHTS = {
    "divergence": 0.25,
    "uncertainty": 0.20,
    "blast_radius": 0.20,
    "freshness_gap": 0.15,
    "open_pressure": 0.10,
    "opportunity": 0.10,
}

BLOCKEDNESS_PENALTY = 0.70
DEFAULT_DIFFUSION_ALPHA = 0.10


class GFDInputError(ValueError):
    pass


def _unit(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GFDInputError(f"{field} must be a number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise GFDInputError(f"{field} must be a finite number in [0, 1]")
    return value


def _node_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise GFDInputError("nodes must be a non-empty list")

    result: dict[str, dict[str, Any]] = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise GFDInputError("each node must be an object")
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise GFDInputError("each node.id must be a non-empty string")
        if node_id in result:
            raise GFDInputError(f"duplicate node id: {node_id}")
        result[node_id] = raw
    return result


def score(payload: dict[str, Any]) -> dict[str, Any]:
    nodes = _node_map(payload)
    alpha = _unit(payload.get("diffusion_alpha", DEFAULT_DIFFUSION_ALPHA), "diffusion_alpha")

    local: dict[str, dict[str, float]] = {}
    for node_id, raw in nodes.items():
        components = {}
        for field in WEIGHTS:
            components[field] = _unit(raw.get(field), f"{node_id}.{field}")
        blockedness = _unit(raw.get("blockedness", 0.0), f"{node_id}.blockedness")
        tension = sum(WEIGHTS[field] * components[field] for field in WEIGHTS)
        actionability = tension * (1.0 - BLOCKEDNESS_PENALTY * blockedness)
        local[node_id] = {
            "tension": tension,
            "blockedness": blockedness,
            "actionability": actionability,
        }

    neighbor_signal: dict[str, list[float]] = {node_id: [] for node_id in nodes}
    raw_edges = payload.get("edges", [])
    if not isinstance(raw_edges, list):
        raise GFDInputError("edges must be a list")

    for edge in raw_edges:
        if not isinstance(edge, dict):
            raise GFDInputError("each edge must be an object")
        source = edge.get("source")
        target = edge.get("target")
        if source not in nodes or target not in nodes:
            raise GFDInputError(f"edge references unknown node: {source!r} -> {target!r}")
        if source == target:
            raise GFDInputError(f"self edge is not allowed: {source}")
        weight = _unit(edge.get("weight", 1.0), f"edge {source}->{target}.weight")
        # v0.1 treats work-graph adjacency as undirected contextual coupling.
        neighbor_signal[source].append(weight * local[target]["tension"])
        neighbor_signal[target].append(weight * local[source]["tension"])

    results = []
    for node_id, raw in nodes.items():
        signals = neighbor_signal[node_id]
        diffusion_bonus = alpha * (sum(signals) / len(signals) if signals else 0.0)
        field_score = min(1.0, local[node_id]["actionability"] + diffusion_bonus)
        results.append(
            {
                "id": node_id,
                "label": raw.get("label", node_id),
                "tension": round(local[node_id]["tension"], 6),
                "blockedness": round(local[node_id]["blockedness"], 6),
                "actionability": round(local[node_id]["actionability"], 6),
                "diffusion_bonus": round(diffusion_bonus, 6),
                "field_score": round(field_score, 6),
                "evidence": raw.get("evidence", []),
                "next_safe_transition": raw.get("next_safe_transition"),
            }
        )

    results.sort(key=lambda item: (-item["field_score"], -item["tension"], item["id"]))
    return {
        "schema": "resonance.graph-field-dynamics.result.v0.1",
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
        "formula": {
            "weights": WEIGHTS,
            "blockedness_penalty": BLOCKEDNESS_PENALTY,
            "diffusion_alpha": alpha,
        },
        "ranking": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank work nodes with Graph–Field Dynamics v0.1")
    parser.add_argument("input", type=Path, help="Input JSON graph")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise GFDInputError("top-level JSON must be an object")
        result = score(payload)
    except (OSError, json.JSONDecodeError, GFDInputError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
