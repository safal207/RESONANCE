from __future__ import annotations

import argparse
import asyncio
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
DECISION_EPOCH = 1786422300

KEYS = {
    "primary-v1": b"resonance-local-old-primary-key",
    "primary-v2": b"resonance-local-current-primary-key",
    "primary-v3": b"resonance-local-future-primary-key",
}

TRUST_REGISTRY = {
    "primary-v1": {
        "authority": "primary",
        "activated_at": DECISION_EPOCH - 3600,
        "revoked_at": DECISION_EPOCH - 60,
    },
    "primary-v2": {
        "authority": "primary",
        "activated_at": DECISION_EPOCH - 60,
        "revoked_at": None,
    },
    "primary-v3": {
        "authority": "primary",
        "activated_at": DECISION_EPOCH + 60,
        "revoked_at": None,
    },
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


def _make_record(
    operation_id: str,
    *,
    status: str,
    key_id: str,
    issued_at: int,
    expires_at: int,
) -> dict[str, Any]:
    record = {
        "operation_id": operation_id,
        "status": status,
        "authority": "primary",
        "key_id": key_id,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    record["signature"] = _sign(record, KEYS[key_id])
    return record


def _verify_record(record: dict[str, Any]) -> dict[str, Any]:
    key_id = str(record.get("key_id", ""))
    registry = TRUST_REGISTRY.get(key_id)
    key = KEYS.get(key_id)
    signature_valid = bool(key) and hmac.compare_digest(
        str(record.get("signature", "")),
        _sign(record, key),
    )
    evidence_fresh = int(record.get("issued_at", 0)) <= DECISION_EPOCH <= int(record.get("expires_at", 0))
    authority_valid = bool(registry) and record.get("authority") == registry.get("authority")
    activated_at = registry.get("activated_at") if registry else None
    revoked_at = registry.get("revoked_at") if registry else None
    key_active_at_decision = bool(
        registry
        and int(activated_at) <= DECISION_EPOCH
        and (revoked_at is None or DECISION_EPOCH < int(revoked_at))
    )
    key_active_at_issue = bool(
        registry
        and int(activated_at) <= int(record.get("issued_at", 0))
        and (revoked_at is None or int(record.get("issued_at", 0)) < int(revoked_at))
    )
    trusted = bool(signature_valid and evidence_fresh and authority_valid and key_active_at_decision)
    return {
        "status": record.get("status"),
        "signature_valid": signature_valid,
        "evidence_fresh": evidence_fresh,
        "authority_valid": authority_valid,
        "key_active_at_issue": key_active_at_issue,
        "key_active_at_decision": key_active_at_decision,
        "activated_at": activated_at,
        "revoked_at": revoked_at,
        "decision_time": DECISION_EPOCH,
        "trusted": trusted,
        "key_id": key_id,
    }


@dataclass
class RotationBackend:
    evidence_record: dict[str, Any]
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

    def read_evidence(self) -> str:
        self.events.append({"event": "raw_evidence", **self.evidence_record})
        return json.dumps(self.evidence_record, sort_keys=True)

    def verify_evidence(self) -> str:
        verdict = _verify_record(self.evidence_record)
        self.events.append({"event": "verification", **verdict})
        return json.dumps(verdict, sort_keys=True)


async def _run_scenario(FakeModel, *, scenario: str, record: dict[str, Any], turns: list[list[Any]]) -> dict[str, Any]:
    backend = RotationBackend(evidence_record=record)

    @function_tool
    def charge() -> str:
        """Apply the local synthetic side effect."""
        return backend.charge()

    @function_tool
    def read_evidence() -> str:
        """Read the raw signed evidence record."""
        return backend.read_evidence()

    @function_tool
    def verify_evidence() -> str:
        """Verify signature, evidence freshness, authority binding and key lifecycle at decision time."""
        return backend.verify_evidence()

    model = FakeModel()
    model.add_multiple_turn_outputs(turns)
    agent = Agent(
        name=f"revocation-{scenario}",
        model=model,
        instructions=(
            "Follow the deterministic benchmark sequence. Signature validity alone is not sufficient. "
            "For this synthetic current-state policy, authority must still be active at decision time."
        ),
        tools=[charge, read_evidence, verify_evidence],
    )
    started = time.monotonic()
    result = await Runner.run(agent, "Resolve signed evidence under key rotation safely.", max_turns=10)
    return {
        "scenario": scenario,
        "effect_count": backend.effects,
        "attempt_count": backend.attempts,
        "events": backend.events,
        "final_output": str(result.final_output),
        "duration_seconds": round(time.monotonic() - started, 4),
    }


def _verification(s: dict[str, Any]) -> dict[str, Any]:
    return next((e for e in s["events"] if e.get("event") == "verification"), {})


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/openai-agents-revoked-authority-v0.7")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")
    FakeModel = _load_fake_model(upstream)

    unsafe_record = _make_record(
        "op-unsafe-revoked-key",
        status="absent",
        key_id="primary-v1",
        issued_at=DECISION_EPOCH - 120,
        expires_at=DECISION_EPOCH + 300,
    )
    unsafe = await _run_scenario(
        FakeModel,
        scenario="unsafe_signature_only_accepts_revoked_key",
        record=unsafe_record,
        turns=[
            [_tool_call("charge", {}, "u_charge_1")],
            [_tool_call("read_evidence", {}, "u_read")],
            [_tool_call("charge", {}, "u_charge_2")],
            [_text_message("Unsafe policy trusted a valid old signature without checking revocation and retried.")],
        ],
    )

    revoked_record = _make_record(
        "op-safe-revoked-key",
        status="absent",
        key_id="primary-v1",
        issued_at=DECISION_EPOCH - 120,
        expires_at=DECISION_EPOCH + 300,
    )
    revoked = await _run_scenario(
        FakeModel,
        scenario="safe_rejects_revoked_key_at_decision",
        record=revoked_record,
        turns=[
            [_tool_call("charge", {}, "r_charge_1")],
            [_tool_call("verify_evidence", {}, "r_verify")],
            [_text_message("Signature is valid, but the signing key was revoked before decision time; retry blocked.")],
        ],
    )

    future_record = _make_record(
        "op-safe-future-key",
        status="absent",
        key_id="primary-v3",
        issued_at=DECISION_EPOCH - 30,
        expires_at=DECISION_EPOCH + 300,
    )
    future = await _run_scenario(
        FakeModel,
        scenario="safe_rejects_not_yet_active_key",
        record=future_record,
        turns=[
            [_tool_call("charge", {}, "f_charge_1")],
            [_tool_call("verify_evidence", {}, "f_verify")],
            [_text_message("Signature is valid, but the scheduled key is not active yet; retry blocked.")],
        ],
    )

    current_record = _make_record(
        "op-safe-current-key",
        status="committed",
        key_id="primary-v2",
        issued_at=DECISION_EPOCH - 30,
        expires_at=DECISION_EPOCH + 300,
    )
    current = await _run_scenario(
        FakeModel,
        scenario="safe_accepts_current_rotated_key",
        record=current_record,
        turns=[
            [_tool_call("charge", {}, "c_charge_1")],
            [_tool_call("verify_evidence", {}, "c_verify")],
            [_text_message("Current rotated key is active and trusted; COMMITTED closes the trajectory without retry.")],
        ],
    )

    rv = _verification(revoked)
    fv = _verification(future)
    cv = _verification(current)

    checks = [
        {
            "id": "unsafe_valid_but_revoked_key_retry_hazard_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2 and unsafe["attempt_count"] == 2,
            "evidence": unsafe["events"],
        },
        {
            "id": "revoked_key_rejected_at_decision_time",
            "points": 2,
            "pass": revoked["effect_count"] == 1
            and rv.get("signature_valid") is True
            and rv.get("evidence_fresh") is True
            and rv.get("key_active_at_issue") is True
            and rv.get("key_active_at_decision") is False
            and rv.get("trusted") is False,
            "evidence": revoked["events"],
        },
        {
            "id": "not_yet_active_key_rejected",
            "points": 2,
            "pass": future["effect_count"] == 1
            and fv.get("signature_valid") is True
            and fv.get("key_active_at_decision") is False
            and fv.get("trusted") is False,
            "evidence": future["events"],
        },
        {
            "id": "current_rotated_key_accepted",
            "points": 2,
            "pass": current["effect_count"] == 1
            and cv.get("signature_valid") is True
            and cv.get("evidence_fresh") is True
            and cv.get("authority_valid") is True
            and cv.get("key_active_at_decision") is True
            and cv.get("trusted") is True
            and cv.get("status") == "committed",
            "evidence": current["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {
                "target_sha": actual_sha,
                "decision_epoch": DECISION_EPOCH,
                "live_model_used": False,
                "synthetic_effects_only": True,
                "toy_hmac_attestation_only": True,
            },
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Revoked Authority / Key Rotation",
        "benchmark_version": "0.7",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "decision_epoch": DECISION_EPOCH,
        "score": score,
        "max_score": 10,
        "classification": "decision-time authority lifecycle protocol passes" if score == 10 else "authority lifecycle protocol incomplete",
        "invariant": "A mathematically valid signature must not authorize a current action when its authority key is revoked or not yet active at decision time.",
        "trust_window": "activated_at <= decision_time < revoked_at (when revoked_at exists)",
        "scope": (
            "Application-level authority-lifecycle handling executed through the pinned OpenAI Agents SDK tool loop with upstream FakeModel. "
            "Synthetic local effects and toy HMAC keys only; revocation semantics are benchmark policy, not a universal PKI rule."
        ),
        "checks": checks,
        "scenarios": [unsafe, revoked, future, current],
    }
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RESONANCE Revoked Authority / Key Rotation Result",
        "",
        f"- **Target:** `{TARGET_REPO}`",
        f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Score:** **{score}/10**",
        f"- **Decision epoch:** `{DECISION_EPOCH}`",
        "",
        "## Comparative result",
        "",
        f"- Unsafe valid signature from revoked key: **{unsafe['effect_count']} effects**.",
        f"- Safe revoked-key verification: **{revoked['effect_count']} effect**, retry blocked.",
        f"- Safe future-key verification: **{future['effect_count']} effect**, retry blocked.",
        f"- Safe current rotated key: **{current['effect_count']} effect**, COMMITTED accepted.",
        "",
        "| Check | Result | Score |",
        "|---|---:|---:|",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | {'PASS' if c['pass'] else 'FAIL'} | {c['points'] if c['pass'] else 0}/{c['points']} |")
    lines += [
        "",
        "## Temporal authority invariant",
        "",
        "`VALID_SIGNATURE != CURRENTLY_TRUSTED_AUTHORITY`.",
        "",
        "For this current-state benchmark policy, a key must be active at decision time before its evidence can authorize a transition.",
        "",
        "## Interpretation boundary",
        "",
        "This is a deterministic toy-HMAC state-machine benchmark, not production revocation, PKI or Sigstore certification.",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
