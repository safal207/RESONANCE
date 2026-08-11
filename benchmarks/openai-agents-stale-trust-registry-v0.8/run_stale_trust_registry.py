from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import hmac
import importlib.util
import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText
from agents import Agent, Runner, function_tool

TARGET_REPO = "openai/openai-agents-python"
TARGET_SHA = "2231eb5d40cd4a9d6b86f79492e984eeb3301263"
DECISION_EPOCH = 1786423200
MAX_REGISTRY_AGE_SECONDS = 120

KEYS = {
    "primary-v1": b"resonance-local-old-primary-key",
    "primary-v2": b"resonance-local-current-primary-key",
}

SOURCE_OF_TRUTH = {
    "primary-v1": {
        "authority": "primary",
        "activated_at": DECISION_EPOCH - 7200,
        "revoked_at": DECISION_EPOCH - 120,
    },
    "primary-v2": {
        "authority": "primary",
        "activated_at": DECISION_EPOCH - 120,
        "revoked_at": None,
    },
}

STALE_CACHE = {
    "generated_at": DECISION_EPOCH - 600,
    "entries": {
        "primary-v1": {
            "authority": "primary",
            "activated_at": DECISION_EPOCH - 7200,
            "revoked_at": None,
        },
        "primary-v2": {
            "authority": "primary",
            "activated_at": DECISION_EPOCH + 3600,
            "revoked_at": None,
        },
    },
}

FRESH_CACHE = {
    "generated_at": DECISION_EPOCH - 30,
    "entries": copy.deepcopy(SOURCE_OF_TRUTH),
}


def _load_fake_model(upstream: Path):
    module_path = upstream / "tests" / "fake_model.py"
    spec = importlib.util.spec_from_file_location("resonance_upstream_fake_model", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load upstream FakeModel from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FakeModel


def _tool_call(name: str, arguments: dict[str, Any], call_id: str) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(
        id=f"item_{call_id}",
        call_id=call_id,
        name=name,
        arguments=json.dumps(arguments, sort_keys=True),
        type="function_call",
    )


def _text_message(text: str) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=f"msg_{abs(hash(text))}",
        type="message",
        role="assistant",
        content=[ResponseOutputText(text=text, type="output_text", annotations=[], logprobs=[])],
        status="completed",
    )


def _canonical(record: dict[str, Any]) -> bytes:
    signed = {
        "operation_id": record["operation_id"],
        "status": record["status"],
        "authority": record["authority"],
        "key_id": record["key_id"],
        "issued_at": record["issued_at"],
        "expires_at": record["expires_at"],
    }
    return json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()


def _sign(record: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, _canonical(record), hashlib.sha256).hexdigest()


def _make_record(operation_id: str, *, status: str, key_id: str) -> dict[str, Any]:
    record = {
        "operation_id": operation_id,
        "status": status,
        "authority": "primary",
        "key_id": key_id,
        "issued_at": DECISION_EPOCH - 60,
        "expires_at": DECISION_EPOCH + 300,
    }
    record["signature"] = _sign(record, KEYS[key_id])
    return record


def _key_active(entry: dict[str, Any] | None, at_time: int) -> bool:
    if not entry:
        return False
    activated_at = int(entry["activated_at"])
    revoked_at = entry.get("revoked_at")
    return activated_at <= at_time and (revoked_at is None or at_time < int(revoked_at))


def _inspect(record: dict[str, Any], registry_snapshot: dict[str, Any]) -> dict[str, Any]:
    key_id = str(record.get("key_id", ""))
    key = KEYS.get(key_id)
    entry = registry_snapshot.get("entries", {}).get(key_id)
    signature_valid = bool(key) and hmac.compare_digest(str(record.get("signature", "")), _sign(record, key))
    evidence_fresh = int(record.get("issued_at", 0)) <= DECISION_EPOCH <= int(record.get("expires_at", 0))
    authority_valid = bool(entry) and record.get("authority") == entry.get("authority")
    registry_generated_at = int(registry_snapshot.get("generated_at", 0))
    registry_age_seconds = DECISION_EPOCH - registry_generated_at
    registry_fresh = 0 <= registry_age_seconds <= MAX_REGISTRY_AGE_SECONDS
    key_active_according_to_snapshot = _key_active(entry, DECISION_EPOCH)
    trusted = bool(signature_valid and evidence_fresh and authority_valid and registry_fresh and key_active_according_to_snapshot)
    return {
        "status": record.get("status"),
        "key_id": key_id,
        "signature_valid": signature_valid,
        "evidence_fresh": evidence_fresh,
        "authority_valid": authority_valid,
        "registry_generated_at": registry_generated_at,
        "registry_age_seconds": registry_age_seconds,
        "registry_fresh": registry_fresh,
        "key_active_according_to_snapshot": key_active_according_to_snapshot,
        "trusted": trusted,
    }


@dataclass
class RegistryBackend:
    evidence_record: dict[str, Any]
    registry_snapshot: dict[str, Any]
    registry_available: bool = True
    attempts: int = 0
    effects: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def charge(self) -> str:
        self.attempts += 1
        self.events.append({"event": "charge_attempt", "attempt": self.attempts})
        self.effects += 1
        self.events.append({"event": "commit", "attempt": self.attempts, "effect_count": self.effects})
        if self.attempts == 1:
            raise RuntimeError("synthetic timeout after commit; caller outcome unknown")
        return f"committed:attempt={self.attempts}"

    def inspect_cached_trust(self) -> str:
        verdict = _inspect(self.evidence_record, self.registry_snapshot)
        self.events.append({"event": "cached_trust_inspection", **verdict})
        return json.dumps(verdict, sort_keys=True)

    def refresh_trust_registry(self) -> str:
        if not self.registry_available:
            self.events.append({"event": "registry_refresh", "status": "unavailable"})
            raise RuntimeError("synthetic trust registry unavailable")
        self.registry_snapshot = {
            "generated_at": DECISION_EPOCH,
            "entries": copy.deepcopy(SOURCE_OF_TRUTH),
        }
        self.events.append({"event": "registry_refresh", "status": "refreshed", "generated_at": DECISION_EPOCH})
        return json.dumps({"status": "refreshed", "generated_at": DECISION_EPOCH}, sort_keys=True)

    def verify_current_trust(self) -> str:
        verdict = _inspect(self.evidence_record, self.registry_snapshot)
        self.events.append({"event": "current_trust_verification", **verdict})
        return json.dumps(verdict, sort_keys=True)


async def _run_scenario(
    FakeModel,
    *,
    scenario: str,
    record: dict[str, Any],
    cache: dict[str, Any],
    registry_available: bool,
    turns: list[list[Any]],
) -> dict[str, Any]:
    backend = RegistryBackend(
        evidence_record=record,
        registry_snapshot=copy.deepcopy(cache),
        registry_available=registry_available,
    )

    @function_tool
    def charge() -> str:
        """Apply the local synthetic side effect."""
        return backend.charge()

    @function_tool
    def inspect_cached_trust() -> str:
        """Inspect evidence against the local cached trust registry, including registry age."""
        return backend.inspect_cached_trust()

    @function_tool
    def refresh_trust_registry() -> str:
        """Refresh the local synthetic trust registry from its source of truth."""
        return backend.refresh_trust_registry()

    @function_tool
    def verify_current_trust() -> str:
        """Verify evidence against the currently held trust-registry snapshot."""
        return backend.verify_current_trust()

    model = FakeModel()
    model.add_multiple_turn_outputs(turns)
    agent = Agent(
        name=f"stale-registry-{scenario}",
        model=model,
        instructions=(
            "Follow the deterministic benchmark sequence. Evidence freshness and trust-registry freshness are separate. "
            "A stale or unavailable registry must not authorize an irreversible retry."
        ),
        tools=[charge, inspect_cached_trust, refresh_trust_registry, verify_current_trust],
    )
    started = time.monotonic()
    result = await Runner.run(agent, "Resolve evidence under possibly stale trust state safely.", max_turns=12)
    return {
        "scenario": scenario,
        "effect_count": backend.effects,
        "attempt_count": backend.attempts,
        "events": backend.events,
        "final_output": str(result.final_output),
        "duration_seconds": round(time.monotonic() - started, 4),
    }


def _event(s: dict[str, Any], name: str) -> dict[str, Any]:
    return next((e for e in s["events"] if e.get("event") == name), {})


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/openai-agents-stale-trust-registry-v0.8")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")
    FakeModel = _load_fake_model(upstream)

    old_absent = _make_record("op-stale-old-key", status="absent", key_id="primary-v1")

    unsafe = await _run_scenario(
        FakeModel,
        scenario="unsafe_stale_registry_allows_revoked_key",
        record=old_absent,
        cache=STALE_CACHE,
        registry_available=True,
        turns=[
            [_tool_call("charge", {}, "u_charge_1")],
            [_tool_call("inspect_cached_trust", {}, "u_cache")],
            [_tool_call("charge", {}, "u_charge_2")],
            [_text_message("Unsafe policy used stale trust state that still marked primary-v1 active and retried.")],
        ],
    )

    refreshed = await _run_scenario(
        FakeModel,
        scenario="safe_refresh_reveals_revocation",
        record=old_absent,
        cache=STALE_CACHE,
        registry_available=True,
        turns=[
            [_tool_call("charge", {}, "r_charge_1")],
            [_tool_call("inspect_cached_trust", {}, "r_cache")],
            [_tool_call("refresh_trust_registry", {}, "r_refresh")],
            [_tool_call("verify_current_trust", {}, "r_verify")],
            [_text_message("Registry refresh reveals primary-v1 revoked; retry blocked.")],
        ],
    )

    unavailable = await _run_scenario(
        FakeModel,
        scenario="safe_refresh_unavailable_holds_trust_unknown",
        record=old_absent,
        cache=STALE_CACHE,
        registry_available=False,
        turns=[
            [_tool_call("charge", {}, "x_charge_1")],
            [_tool_call("inspect_cached_trust", {}, "x_cache")],
            [_tool_call("refresh_trust_registry", {}, "x_refresh")],
            [_text_message("Registry is stale and refresh is unavailable; TRUST_UNKNOWN preserved and retry blocked.")],
        ],
    )

    current_committed = _make_record("op-fresh-current-key", status="committed", key_id="primary-v2")
    fresh = await _run_scenario(
        FakeModel,
        scenario="safe_fresh_registry_accepts_current_key",
        record=current_committed,
        cache=FRESH_CACHE,
        registry_available=True,
        turns=[
            [_tool_call("charge", {}, "f_charge_1")],
            [_tool_call("verify_current_trust", {}, "f_verify")],
            [_text_message("Fresh trust registry confirms current primary-v2 and COMMITTED; no retry.")],
        ],
    )

    unsafe_cache = _event(unsafe, "cached_trust_inspection")
    refresh_cache = _event(refreshed, "cached_trust_inspection")
    refresh_verify = _event(refreshed, "current_trust_verification")
    unavailable_refresh = _event(unavailable, "registry_refresh")
    fresh_verify = _event(fresh, "current_trust_verification")

    checks = [
        {
            "id": "unsafe_stale_registry_retry_hazard_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2
            and unsafe_cache.get("signature_valid") is True
            and unsafe_cache.get("evidence_fresh") is True
            and unsafe_cache.get("registry_fresh") is False
            and unsafe_cache.get("key_active_according_to_snapshot") is True,
            "evidence": unsafe["events"],
        },
        {
            "id": "stale_registry_refresh_reveals_revocation",
            "points": 2,
            "pass": refreshed["effect_count"] == 1
            and refresh_cache.get("registry_fresh") is False
            and refresh_verify.get("registry_fresh") is True
            and refresh_verify.get("key_active_according_to_snapshot") is False
            and refresh_verify.get("trusted") is False,
            "evidence": refreshed["events"],
        },
        {
            "id": "unavailable_refresh_preserves_trust_unknown",
            "points": 2,
            "pass": unavailable["effect_count"] == 1
            and unavailable["attempt_count"] == 1
            and unavailable_refresh.get("status") == "unavailable",
            "evidence": unavailable["events"],
        },
        {
            "id": "fresh_registry_accepts_current_rotated_key",
            "points": 2,
            "pass": fresh["effect_count"] == 1
            and fresh_verify.get("registry_fresh") is True
            and fresh_verify.get("key_active_according_to_snapshot") is True
            and fresh_verify.get("trusted") is True
            and fresh_verify.get("status") == "committed",
            "evidence": fresh["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {
                "target_sha": actual_sha,
                "decision_epoch": DECISION_EPOCH,
                "max_registry_age_seconds": MAX_REGISTRY_AGE_SECONDS,
                "live_model_used": False,
                "synthetic_effects_only": True,
                "toy_hmac_attestation_only": True,
            },
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Stale Trust Registry",
        "benchmark_version": "0.8",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "decision_epoch": DECISION_EPOCH,
        "max_registry_age_seconds": MAX_REGISTRY_AGE_SECONDS,
        "score": score,
        "max_score": 10,
        "classification": "trust-registry freshness protocol passes" if score == 10 else "trust-registry freshness protocol incomplete",
        "invariant": "Fresh evidence must not authorize irreversible retry when the trust registry is stale or unavailable; refresh or preserve TRUST_UNKNOWN.",
        "scope": (
            "Application-level trust-registry freshness handling executed through the pinned OpenAI Agents SDK tool loop with upstream FakeModel. "
            "Synthetic local effects, toy HMAC keys and in-memory trust registries only."
        ),
        "checks": checks,
        "scenarios": [unsafe, refreshed, unavailable, fresh],
    }
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RESONANCE Stale Trust Registry Result",
        "",
        f"- **Target:** `{TARGET_REPO}`",
        f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Score:** **{score}/10**",
        f"- **Max registry age:** **{MAX_REGISTRY_AGE_SECONDS}s**",
        "",
        "## Comparative result",
        "",
        f"- Unsafe stale cache → retry: **{unsafe['effect_count']} effects**.",
        f"- Safe stale cache → refresh → revoked: **{refreshed['effect_count']} effect**, retry blocked.",
        f"- Safe stale cache → refresh unavailable: **{unavailable['effect_count']} effect**, TRUST_UNKNOWN held.",
        f"- Safe fresh cache + current key: **{fresh['effect_count']} effect**, COMMITTED accepted.",
        "",
        "| Check | Result | Score |",
        "|---|---:|---:|",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | {'PASS' if c['pass'] else 'FAIL'} | {c['points'] if c['pass'] else 0}/{c['points']} |")
    lines += [
        "",
        "## Registry freshness invariant",
        "",
        "`FRESH EVIDENCE + STALE TRUST STATE` is not trusted evidence for a new irreversible action.",
        "",
        "If the registry cannot be refreshed, the safe state is `TRUST_UNKNOWN`, not implicit permission to retry.",
        "",
        "## Interpretation boundary",
        "",
        "The SDK executes deterministic application trajectories. This benchmark tests application trust-state freshness policy, not a production registry, PKI, revocation service or SDK security guarantee.",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
