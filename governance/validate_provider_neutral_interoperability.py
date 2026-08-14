#!/usr/bin/env python3
"""Validate and replay the provider-neutral proof-logistics contract.

The validator is deliberately dependency-free.  It checks the smallest shared
spine at the handoff boundary while preserving native field names through an
explicit mapping.  It does not execute a provider, grant authority, or mutate
the represented source history.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


CONTRACT_SCHEMA = "neo.resonance.provider-neutral-interoperability.v0.1"
RESULT_SCHEMA = "neo.resonance.provider-neutral-interoperability-result.v0.1"
ROUTE = ("intent", "proofpath", "cml", "liminaldb", "rinse", "contractgraph_qa")
EVENT_SPINE = (
    "logical_operation_id",
    "execution_id",
    "attempt_id",
    "parent_cause",
    "intent",
    "resolved_target",
    "expected_invariants",
    "observed_outcome",
    "phase",
    "valid_time",
    "transaction_time",
    "recovery_state",
    "verification_refs",
)
EXPECTED_HEADS = {
    "proofpath": "4a05ee31d7497979c2505dd55bfef08823302e24",
    "cml": "2a649903693fc61a560ee056834127ada3120206",
    "liminaldb": "61b02fc81e0cb5cf1f1ed4658ecff58f683cb728",
    "rinse": "3be0d2ceb1440641b141cdb80c82ed118e4186dd",
    "contractgraph_qa": "1a3e4b45de9ea8d495fa96c1069704476295df5c",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_RECOVERY = {
    "not_started",
    "not_required",
    "reopened",
    "reflection_only",
    "verified",
}
ALLOWED_BINDING_KINDS = {"identity", "derived_reference", "structured_projection"}


class InteroperabilityError(ValueError):
    """Raised when the shared contract cannot be accepted."""


def canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InteroperabilityError(f"value is not canonical JSON: {exc}") from exc


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InteroperabilityError(f"{field} must be an object")
    return value


def _list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise InteroperabilityError(f"{field} must be an array")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InteroperabilityError(f"{field} must be a non-empty string")
    return value.strip()


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InteroperabilityError(f"{field} must be a boolean")
    return value


def _digest(value: object, field: str) -> str:
    value = _text(value, field)
    if not SHA256_RE.fullmatch(value):
        raise InteroperabilityError(f"{field} must be a sha256 reference")
    return value


def _time(value: object, field: str) -> datetime:
    raw = _text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InteroperabilityError(f"{field} must be RFC3339 time") from exc
    if parsed.tzinfo is None:
        raise InteroperabilityError(f"{field} must include a timezone")
    return parsed


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InteroperabilityError(f"cannot load {path}: {exc}") from exc
    return _object(value, str(path))


def _validate_authority(value: object, field: str) -> dict[str, bool]:
    authority = _object(value, field)
    for key in ("execution_authorized", "mutation_authorized", "external_effects_authorized"):
        if _bool(authority.get(key), f"{field}.{key}"):
            raise InteroperabilityError(f"{field}.{key} must remain false")
    return {key: False for key in ("execution_authorized", "mutation_authorized", "external_effects_authorized")}


def _validate_evidence_catalog(value: object) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    for index, raw in enumerate(_list(value, "evidence_catalog")):
        item = _object(raw, f"evidence_catalog[{index}]")
        ref = _text(item.get("ref"), f"evidence_catalog[{index}].ref")
        if ref in catalog:
            raise InteroperabilityError(f"duplicate evidence ref {ref}")
        catalog[ref] = {
            "role": _text(item.get("role"), f"evidence_catalog[{index}].role"),
            "digest": _digest(item.get("digest"), f"evidence_catalog[{index}].digest"),
        }
    if not catalog:
        raise InteroperabilityError("evidence_catalog must not be empty")
    return catalog


def _validate_invariants(value: object) -> dict[str, str]:
    invariants: dict[str, str] = {}
    for index, raw in enumerate(_list(value, "expected_invariants")):
        item = _object(raw, f"expected_invariants[{index}]")
        invariant_id = _text(item.get("id"), f"expected_invariants[{index}].id")
        if invariant_id in invariants:
            raise InteroperabilityError(f"duplicate invariant {invariant_id}")
        invariants[invariant_id] = _text(
            item.get("statement"), f"expected_invariants[{index}].statement"
        )
    if not invariants:
        raise InteroperabilityError("expected_invariants must not be empty")
    return invariants


def _validate_component_bindings(value: object) -> None:
    seen: set[str] = set()
    for index, raw in enumerate(_list(value, "component_bindings")):
        item = _object(raw, f"component_bindings[{index}]")
        component = _text(item.get("component"), f"component_bindings[{index}].component")
        if component in seen:
            raise InteroperabilityError(f"duplicate component binding {component}")
        seen.add(component)
        repository = _text(item.get("repository"), f"component_bindings[{index}].repository")
        if "/" not in repository:
            raise InteroperabilityError(f"component_bindings[{index}].repository is not owner/name")
        revision = _text(item.get("revision"), f"component_bindings[{index}].revision")
        if not HEAD_RE.fullmatch(revision):
            raise InteroperabilityError(f"component_bindings[{index}].revision is not a commit SHA")
        if component in EXPECTED_HEADS and revision != EXPECTED_HEADS[component]:
            raise InteroperabilityError(f"component binding {component} is stale")
    if set(ROUTE) != seen:
        raise InteroperabilityError("component_bindings must cover the primary route exactly")


def _validate_adjacent_planes(value: object) -> None:
    planes = _list(value, "adjacent_control_planes")
    capu = [item for item in planes if isinstance(item, dict) and item.get("component") == "capu"]
    if len(capu) != 1:
        raise InteroperabilityError("exactly one CaPU adjacent control-plane binding is required")
    plane = _object(capu[0], "adjacent_control_planes[capu]")
    if plane.get("in_primary_proof_route") is not False:
        raise InteroperabilityError("CaPU must remain outside the primary proof route")
    if plane.get("semantic_authority") != "cml":
        raise InteroperabilityError("CaPU cannot become the semantic authority")
    revision = _text(plane.get("revision"), "adjacent_control_planes[capu].revision")
    if revision != "babd2945046d2564e1110a76741827560c57fcca":
        raise InteroperabilityError("CaPU adjacent binding is stale")


def _validate_mapping(value: object, field: str) -> None:
    mapping = _object(value, field)
    if set(mapping) != set(EVENT_SPINE):
        raise InteroperabilityError(f"{field} must map every provider-neutral spine field exactly once")
    for key in EVENT_SPINE:
        item = _object(mapping[key], f"{field}.{key}")
        _text(item.get("native_path"), f"{field}.{key}.native_path")
        if item.get("semantic_status") != "preserved":
            raise InteroperabilityError(f"{field}.{key} does not preserve semantic identity")
        binding_kind = _text(item.get("binding_kind"), f"{field}.{key}.binding_kind")
        if binding_kind not in ALLOWED_BINDING_KINDS:
            raise InteroperabilityError(f"{field}.{key}.binding_kind is unsupported")


def _validate_event(
    event: Mapping[str, Any],
    index: int,
    *,
    operation_id: str,
    execution_id: str,
    attempt_id: str,
    intent_id: str,
    invariant_ids: set[str],
    evidence_catalog: Mapping[str, Mapping[str, str]],
    previous_event_id: str | None,
) -> str:
    field = f"events[{index}]"
    event_id = _text(event.get("event_id"), f"{field}.event_id")
    phase = _text(event.get("phase"), f"{field}.phase")
    if phase != ROUTE[index]:
        raise InteroperabilityError(f"{field}.phase must be {ROUTE[index]}")
    if _text(event.get("logical_operation_id"), f"{field}.logical_operation_id") != operation_id:
        raise InteroperabilityError(f"{field}.logical_operation_id changed the operation identity")
    if _text(event.get("execution_id"), f"{field}.execution_id") != execution_id:
        raise InteroperabilityError(f"{field}.execution_id changed the execution identity")
    if _text(event.get("attempt_id"), f"{field}.attempt_id") != attempt_id:
        raise InteroperabilityError(f"{field}.attempt_id changed the attempt identity")
    if _text(event.get("intent_id"), f"{field}.intent_id") != intent_id:
        raise InteroperabilityError(f"{field}.intent_id changed the intent binding")

    parent = event.get("parent_cause")
    if index == 0:
        if parent is not None:
            raise InteroperabilityError("the root event must have parent_cause=null")
    elif parent != previous_event_id:
        raise InteroperabilityError(f"{field}.parent_cause must point to the previous event")

    _object(event.get("intent"), f"{field}.intent")
    target = _object(event.get("resolved_target"), f"{field}.resolved_target")
    if _text(target.get("component"), f"{field}.resolved_target.component") != phase:
        raise InteroperabilityError(f"{field}.resolved_target.component must match phase")
    _text(target.get("operation"), f"{field}.resolved_target.operation")
    _text(target.get("scope"), f"{field}.resolved_target.scope")

    event_invariants = _list(event.get("expected_invariants"), f"{field}.expected_invariants")
    if not event_invariants:
        raise InteroperabilityError(f"{field}.expected_invariants must not be empty")
    for invariant in event_invariants:
        invariant_id = _text(invariant, f"{field}.expected_invariants item")
        if invariant_id not in invariant_ids:
            raise InteroperabilityError(f"{field} references unknown invariant {invariant_id}")

    outcome = _object(event.get("observed_outcome"), f"{field}.observed_outcome")
    _text(outcome.get("status"), f"{field}.observed_outcome.status")
    _text(outcome.get("decision"), f"{field}.observed_outcome.decision")
    _text(outcome.get("summary"), f"{field}.observed_outcome.summary")
    valid_time = _object(event.get("valid_time"), f"{field}.valid_time")
    valid_from = _time(valid_time.get("from"), f"{field}.valid_time.from")
    valid_to = valid_time.get("to")
    if valid_to is not None and _time(valid_to, f"{field}.valid_time.to") < valid_from:
        raise InteroperabilityError(f"{field}.valid_time.to precedes valid_time.from")
    transaction_time = _time(event.get("transaction_time"), f"{field}.transaction_time")
    if transaction_time < valid_from:
        raise InteroperabilityError(f"{field}.transaction_time precedes valid_time.from")
    recovery = _text(event.get("recovery_state"), f"{field}.recovery_state")
    if recovery not in ALLOWED_RECOVERY:
        raise InteroperabilityError(f"{field}.recovery_state is unsupported")

    refs = _list(event.get("verification_refs"), f"{field}.verification_refs")
    if not refs:
        raise InteroperabilityError(f"{field}.verification_refs must not be empty")
    for ref in refs:
        ref_id = _text(ref, f"{field}.verification_refs item")
        if ref_id not in evidence_catalog:
            raise InteroperabilityError(f"{field} references unknown evidence {ref_id}")
    _validate_authority(event.get("authority_boundary"), f"{field}.authority_boundary")
    projection = _object(event.get("native_projection"), f"{field}.native_projection")
    _text(projection.get("repository"), f"{field}.native_projection.repository")
    _text(projection.get("native_schema"), f"{field}.native_projection.native_schema")
    _validate_mapping(projection.get("field_map"), f"{field}.native_projection.field_map")
    return event_id


def validate_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the contract and return a compact deterministic summary."""

    contract = _object(payload, "contract")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise InteroperabilityError(f"contract.schema must be {CONTRACT_SCHEMA}")
    if contract.get("contract_version") != "0.1":
        raise InteroperabilityError("contract.contract_version must be 0.1")
    case_id = _text(contract.get("case_id"), "contract.case_id")
    operation_id = _text(contract.get("logical_operation_id"), "contract.logical_operation_id")
    execution_id = _text(contract.get("execution_id"), "contract.execution_id")
    attempt_id = _text(contract.get("attempt_id"), "contract.attempt_id")

    intent = _object(contract.get("intent"), "contract.intent")
    intent_id = _text(intent.get("intent_id"), "contract.intent.intent_id")
    _text(intent.get("kind"), "contract.intent.kind")
    _text(intent.get("purpose"), "contract.intent.purpose")
    _digest(intent.get("argument_digest"), "contract.intent.argument_digest")
    _text(intent.get("expected_outcome"), "contract.intent.expected_outcome")

    target = _object(contract.get("resolved_target"), "contract.resolved_target")
    if tuple(_text(item, "contract.resolved_target.route item") for item in _list(target.get("route"), "contract.resolved_target.route")) != ROUTE:
        raise InteroperabilityError("contract.resolved_target.route must be the canonical primary route")
    _text(target.get("scope"), "contract.resolved_target.scope")
    invariant_ids = set(_validate_invariants(contract.get("expected_invariants")))
    evidence_catalog = _validate_evidence_catalog(contract.get("evidence_catalog"))
    _validate_component_bindings(contract.get("component_bindings"))
    _validate_adjacent_planes(contract.get("adjacent_control_planes"))
    _validate_authority(contract.get("authority_boundary"), "contract.authority_boundary")

    events = _list(contract.get("events"), "contract.events")
    if len(events) != len(ROUTE):
        raise InteroperabilityError("contract.events must contain exactly one event per route phase")
    event_ids: list[str] = []
    previous: str | None = None
    for index, raw in enumerate(events):
        event = _object(raw, f"events[{index}]")
        event_id = _validate_event(
            event,
            index,
            operation_id=operation_id,
            execution_id=execution_id,
            attempt_id=attempt_id,
            intent_id=intent_id,
            invariant_ids=invariant_ids,
            evidence_catalog=evidence_catalog,
            previous_event_id=previous,
        )
        if event_id in event_ids:
            raise InteroperabilityError(f"duplicate event_id {event_id}")
        event_ids.append(event_id)
        previous = event_id

    return {
        "schema": CONTRACT_SCHEMA,
        "case_id": case_id,
        "logical_operation_id": operation_id,
        "execution_id": execution_id,
        "attempt_id": attempt_id,
        "route": list(ROUTE),
        "event_ids": event_ids,
        "event_count": len(events),
        "invariant_count": len(invariant_ids),
        "evidence_count": len(evidence_catalog),
        "causal_parent_chain_preserved": True,
        "semantic_mappings_preserved": True,
        "authority": {
            "execution_authorized": False,
            "mutation_authorized": False,
            "external_effects_authorized": False,
        },
    }


def build_reflection(contract: Mapping[str, Any], source_digest: str) -> dict[str, Any]:
    operation_id = _text(contract.get("logical_operation_id"), "contract.logical_operation_id")
    return {
        "schema": "neo.resonance.provider-neutral-reflection.v0.1",
        "subject_id": f"logical-operation:{operation_id}",
        "source_digest": source_digest,
        "status": "SUPPORTED_WITH_LIMITS",
        "authority": {
            "classification": "REFLECTION_ONLY",
            "truth_authorized": False,
            "execution_authorized": False,
            "mutation_authorized": False,
        },
        "proposed_transition": {
            "kind": "REINTERPRETATION_CANDIDATE",
            "execution_allowed": False,
            "write_back_allowed": False,
        },
        "source_mutated": False,
        "write_back_performed": False,
    }


def independent_verify(
    reopened: Mapping[str, Any],
    serialized: bytes,
    reflection: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute identity and route facts using a separate verification path."""

    raw = _object(reopened, "reopened")
    expected_digest = "sha256:" + hashlib.sha256(serialized).hexdigest()
    if canonical_bytes(raw) != serialized:
        raise InteroperabilityError("reopened bytes are not canonical-byte identical")
    if _text(reflection.get("source_digest"), "reflection.source_digest") != expected_digest:
        raise InteroperabilityError("reflection source digest does not match reopened bytes")
    operation_id = _text(raw.get("logical_operation_id"), "reopened.logical_operation_id")
    events = raw.get("events")
    if not isinstance(events, list) or [item.get("phase") for item in events if isinstance(item, dict)] != list(ROUTE):
        raise InteroperabilityError("independent route reconstruction failed")
    if any(item.get("logical_operation_id") != operation_id for item in events if isinstance(item, dict)):
        raise InteroperabilityError("independent identity reconstruction failed")
    if reflection.get("authority", {}).get("execution_authorized") is not False:
        raise InteroperabilityError("reflection escalated execution authority")
    if reflection.get("source_mutated") is not False or reflection.get("write_back_performed") is not False:
        raise InteroperabilityError("reflection mutated source state")
    return {
        "status": "PASS",
        "identity_preserved": True,
        "route_reconstructed": list(ROUTE),
        "source_digest": expected_digest,
        "source_mutated": False,
        "write_back_performed": False,
    }


def run_lifecycle(contract: Mapping[str, Any], store_dir: Path) -> dict[str, Any]:
    summary = validate_contract(contract)
    serialized = canonical_bytes(contract)
    source_digest = "sha256:" + hashlib.sha256(serialized).hexdigest()
    store_dir.mkdir(parents=True, exist_ok=True)
    stored_path = store_dir / "provider-neutral-contract.json"
    stored_path.write_bytes(serialized)
    reopened_bytes = stored_path.read_bytes()
    reopened = json.loads(reopened_bytes.decode("utf-8"))
    reopened_summary = validate_contract(reopened)
    reflection = build_reflection(reopened, source_digest)
    independent = independent_verify(reopened, reopened_bytes, reflection)
    if serialized != reopened_bytes:
        raise InteroperabilityError("stored/reopened bytes changed")
    if summary != reopened_summary:
        raise InteroperabilityError("reopened validation summary changed")
    return {
        "summary": summary,
        "reflection": reflection,
        "independent_verification": independent,
        "serialized_digest": source_digest,
        "stored_byte_match": True,
        "reopened_byte_match": True,
        "store_path": str(stored_path),
    }


def _expect_rejected(name: str, value: Mapping[str, Any]) -> str:
    try:
        validate_contract(value)
    except InteroperabilityError:
        return "REJECTED"
    raise InteroperabilityError(f"negative case {name} was accepted")


def run_negative_cases(contract: Mapping[str, Any]) -> dict[str, str]:
    cases: dict[str, str] = {}
    changed_identity = copy.deepcopy(contract)
    changed_identity["events"][2]["logical_operation_id"] = "renamed-operation"
    cases["logical_operation_renaming"] = _expect_rejected("logical_operation_renaming", changed_identity)

    changed_parent = copy.deepcopy(contract)
    changed_parent["events"][2]["parent_cause"] = "event:intent:001"
    cases["causal_parent_break"] = _expect_rejected("causal_parent_break", changed_parent)

    unknown_phase = copy.deepcopy(contract)
    unknown_phase["events"][3]["phase"] = "unknown_provider"
    cases["unknown_phase"] = _expect_rejected("unknown_phase", unknown_phase)

    missing_evidence = copy.deepcopy(contract)
    missing_evidence["events"][4]["verification_refs"] = ["evidence://missing"]
    cases["missing_evidence_ref"] = _expect_rejected("missing_evidence_ref", missing_evidence)

    escalated = copy.deepcopy(contract)
    escalated["events"][5]["authority_boundary"]["execution_authorized"] = True
    cases["authority_escalation"] = _expect_rejected("authority_escalation", escalated)

    semantic_rename = copy.deepcopy(contract)
    semantic_rename["events"][1]["native_projection"]["field_map"]["logical_operation_id"]["semantic_status"] = "renamed"
    cases["semantic_rename"] = _expect_rejected("semantic_rename", semantic_rename)
    return cases


def run(fixture: Path, output_dir: Path, checked_subject: str | None = None) -> dict[str, Any]:
    contract = load_json(fixture)
    lifecycle_store = output_dir / "store"
    lifecycle = run_lifecycle(contract, lifecycle_store)
    negatives = run_negative_cases(contract)
    result = {
        "schema": RESULT_SCHEMA,
        "status": "PASS",
        "case_id": lifecycle["summary"]["case_id"],
        "logical_operation_id": lifecycle["summary"]["logical_operation_id"],
        "checked_subject": checked_subject,
        "route": list(ROUTE),
        "event_count": lifecycle["summary"]["event_count"],
        "serialized_digest": lifecycle["serialized_digest"],
        "stored_byte_match": lifecycle["stored_byte_match"],
        "reopened_byte_match": lifecycle["reopened_byte_match"],
        "reflection": lifecycle["reflection"],
        "independent_verification": lifecycle["independent_verification"],
        "negative_cases": negatives,
        "authority": lifecycle["summary"]["authority"],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checked-subject")
    args = parser.parse_args()
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result = run(args.fixture, args.output_dir, args.checked_subject)
        (args.output_dir / "reflection.json").write_text(
            json.dumps(result["reflection"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("P0_3_INTEROPERABILITY_PASS", result["serialized_digest"])
        return 0
    except (OSError, InteroperabilityError, json.JSONDecodeError) as exc:
        print(f"P0_3_INTEROPERABILITY_INCOMPLETE {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
