#!/usr/bin/env python3
"""Normalize Graph–Field operator results into one advisory envelope.

This module deliberately does not import CML or other ecosystem packages.
It adapts serialized result shapes and preserves the authority boundary.
"""

from __future__ import annotations

from typing import Any


class OperatorFamilyError(ValueError):
    pass


UNIFIED_SCHEMA = "resonance.graph-field-operator.result.v0.1"
ORIENTATION_SCHEMA = "resonance.graph-field-dynamics.result.v0.1"
CML_RECOVERY_CONTRACT = "cml.focus-field.recovery-decision.v0.2"


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OperatorFamilyError(f"{field} must be numeric")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise OperatorFamilyError(f"{field} must be in [0, 1]")
    return value


def _base(operator_kind: str, source_contract: str) -> dict[str, Any]:
    return {
        "schema": UNIFIED_SCHEMA,
        "operator_kind": operator_kind,
        "source_contract": source_contract,
        "mode": "ADVISORY_ONLY",
        "authority_granted": False,
    }


def normalize_orientation(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize the executable RESONANCE orientation scorer output."""

    if result.get("schema") != ORIENTATION_SCHEMA:
        raise OperatorFamilyError("unsupported orientation source contract")
    if result.get("mode") != "ADVISORY_ONLY" or result.get("authority_granted") is not False:
        raise OperatorFamilyError("orientation source violated advisory authority boundary")

    ranking = result.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        raise OperatorFamilyError("orientation ranking must be a non-empty list")

    top = ranking[0]
    if not isinstance(top, dict):
        raise OperatorFamilyError("orientation ranking entries must be objects")
    node_id = top.get("id")
    if not isinstance(node_id, str) or not node_id:
        raise OperatorFamilyError("orientation top candidate id is required")

    score = _number(top.get("field_score"), "orientation.field_score")

    envelope = _base("orientation", ORIENTATION_SCHEMA)
    envelope.update(
        {
            "selection": {
                "id": node_id,
                "score": score,
                "state": "ORIENTATION_CANDIDATE",
            },
            "handoff": {
                "ready_for_separate_authority_check": True,
            },
            "source_state": {
                "tension": _number(top.get("tension"), "orientation.tension"),
                "blockedness": _number(top.get("blockedness"), "orientation.blockedness"),
                "next_safe_transition": top.get("next_safe_transition"),
            },
        }
    )
    return envelope


def normalize_cml_recovery(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a serialized CML Focus–Field Recovery v0.2 decision.

    This validates semantic consistency only. It does not independently verify
    the CML applicability or information-quality evidence that produced the
    decision.
    """

    if result.get("source_contract") != CML_RECOVERY_CONTRACT:
        raise OperatorFamilyError("unsupported CML recovery source contract")
    if result.get("authority_granted", False) is not False:
        raise OperatorFamilyError("recovery source must not grant authority")

    state = result.get("state")
    selected = result.get("selected_anchor_id")
    trusted = result.get("trusted_continuation")
    score = _number(result.get("score", 0.0), "recovery.score")

    if not isinstance(trusted, bool):
        raise OperatorFamilyError("trusted_continuation must be boolean")

    if state == "defocus":
        if selected is not None or trusted:
            raise OperatorFamilyError("defocus cannot carry a selected or trusted continuation")
        unified_state = "NO_SELECTION"
        ready = False
    elif state == "reanchored_exploratory":
        if not isinstance(selected, str) or not selected or trusted:
            raise OperatorFamilyError("exploratory re-anchor requires an untrusted selected anchor")
        unified_state = "EXPLORATORY_SELECTION"
        ready = False
    elif state == "reanchored":
        if not isinstance(selected, str) or not selected or not trusted:
            raise OperatorFamilyError("trusted re-anchor requires selected anchor and trusted_continuation=true")
        unified_state = "TRUSTED_REENTRY_CANDIDATE"
        ready = True
    else:
        raise OperatorFamilyError(f"unsupported recovery state: {state!r}")

    envelope = _base("recovery", CML_RECOVERY_CONTRACT)
    envelope.update(
        {
            "selection": {
                "id": selected,
                "score": score,
                "state": unified_state,
            },
            "handoff": {
                "ready_for_separate_authority_check": ready,
            },
            "source_state": {
                "state": state,
                "trusted_continuation": trusted,
                "rewind_steps_saved": result.get("rewind_steps_saved"),
                "source_revision": result.get("source_revision"),
            },
        }
    )
    return envelope
