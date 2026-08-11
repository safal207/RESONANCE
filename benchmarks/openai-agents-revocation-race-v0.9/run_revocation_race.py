from __future__ import annotations

import argparse
import asyncio
import copy
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
VERIFY_TIME = 1786424000
COMMIT_TIME = VERIFY_TIME + 30

INITIAL_TRUST = {
    "epoch": 41,
    "keys": {
        "primary-v1": {"authority": "primary", "activated_at": VERIFY_TIME - 3600, "revoked_at": None},
        "primary-v2": {"authority": "primary", "activated_at": VERIFY_TIME - 300, "revoked_at": None},
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
        id=f"item_{call_id}", call_id=call_id, name=name,
        arguments=json.dumps(arguments, sort_keys=True), type="function_call"
    )


def _text_message(text: str) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=f"msg_{abs(hash(text))}", type="message", role="assistant",
        content=[ResponseOutputText(text=text, type="output_text", annotations=[], logprobs=[])],
        status="completed",
    )


def _active(entry: dict[str, Any] | None, at_time: int) -> bool:
    if not entry:
        return False
    activated_at = int(entry["activated_at"])
    revoked_at = entry.get("revoked_at")
    return activated_at <= at_time and (revoked_at is None or at_time < int(revoked_at))


@dataclass
class RaceBackend:
    key_id: str
    first_attempt_commits: bool
    trust: dict[str, Any] = field(default_factory=lambda: copy.deepcopy(INITIAL_TRUST))
    attempts: int = 0
    effects: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def initial_attempt(self) -> str:
        self.attempts += 1
        self.events.append({"event": "initial_attempt", "attempt": self.attempts})
        if self.first_attempt_commits:
            self.effects += 1
            self.events.append({"event": "commit", "phase": "initial", "effect_count": self.effects})
            raise RuntimeError("synthetic timeout after commit; caller outcome unknown")
        self.events.append({"event": "no_commit_timeout", "phase": "initial"})
        raise RuntimeError("synthetic timeout before commit; caller outcome unknown")

    def verify_authority(self) -> str:
        entry = self.trust["keys"].get(self.key_id)
        active = _active(entry, VERIFY_TIME)
        token = {
            "key_id": self.key_id,
            "authority": entry.get("authority") if entry else None,
            "trust_epoch": int(self.trust["epoch"]),
            "verified_at": VERIFY_TIME,
            "key_active": active,
        }
        self.events.append({"event": "authority_verified", **token})
        return json.dumps(token, sort_keys=True)

    def revoke_after_verification(self) -> str:
        self.trust["epoch"] = int(self.trust["epoch"]) + 1
        self.trust["keys"][self.key_id]["revoked_at"] = VERIFY_TIME + 10
        event = {
            "event": "authority_revoked",
            "key_id": self.key_id,
            "revoked_at": VERIFY_TIME + 10,
            "new_trust_epoch": int(self.trust["epoch"]),
        }
        self.events.append(event)
        return json.dumps(event, sort_keys=True)

    def unsafe_retry(self) -> str:
        self.attempts += 1
        self.effects += 1
        self.events.append({
            "event": "unsafe_retry_commit",
            "attempt": self.attempts,
            "commit_time": COMMIT_TIME,
            "current_trust_epoch": int(self.trust["epoch"]),
            "effect_count": self.effects,
        })
        return f"committed-unsafely:effect={self.effects}"

    def conditional_retry(self, expected_trust_epoch: int) -> str:
        self.attempts += 1
        entry = self.trust["keys"].get(self.key_id)
        current_epoch = int(self.trust["epoch"])
        key_active_at_commit = _active(entry, COMMIT_TIME)
        epoch_matches = int(expected_trust_epoch) == current_epoch
        allowed = bool(epoch_matches and key_active_at_commit)
        self.events.append({
            "event": "conditional_retry_check",
            "attempt": self.attempts,
            "expected_trust_epoch": int(expected_trust_epoch),
            "current_trust_epoch": current_epoch,
            "epoch_matches": epoch_matches,
            "key_active_at_commit": key_active_at_commit,
            "commit_time": COMMIT_TIME,
            "allowed": allowed,
        })
        if not allowed:
            self.events.append({"event": "precondition_failed", "effect_count": self.effects})
            return "PRECONDITION_FAILED"
        self.effects += 1
        self.events.append({"event": "conditional_retry_commit", "effect_count": self.effects})
        return f"committed-conditionally:effect={self.effects}"

    def reverify_current_authority(self) -> str:
        entry = self.trust["keys"].get(self.key_id)
        verdict = {
            "event": "authority_reverified",
            "key_id": self.key_id,
            "trust_epoch": int(self.trust["epoch"]),
            "checked_at": COMMIT_TIME,
            "key_active": _active(entry, COMMIT_TIME),
        }
        self.events.append(verdict)
        return json.dumps(verdict, sort_keys=True)


async def _run_scenario(FakeModel, *, scenario: str, key_id: str, first_attempt_commits: bool, turns: list[list[Any]]) -> dict[str, Any]:
    backend = RaceBackend(key_id=key_id, first_attempt_commits=first_attempt_commits)

    @function_tool
    def initial_attempt() -> str:
        """Run the first local synthetic side-effect attempt, which intentionally times out."""
        return backend.initial_attempt()

    @function_tool
    def verify_authority() -> str:
        """Verify current key authority and return a trust-epoch-bound authorization token."""
        return backend.verify_authority()

    @function_tool
    def revoke_after_verification() -> str:
        """Apply a synthetic key revocation after verification and advance the trust epoch."""
        return backend.revoke_after_verification()

    @function_tool
    def unsafe_retry() -> str:
        """Retry without checking whether the earlier authorization is still current."""
        return backend.unsafe_retry()

    @function_tool
    def conditional_retry(expected_trust_epoch: int) -> str:
        """Retry only if trust epoch is unchanged and the key remains active at commit time."""
        return backend.conditional_retry(expected_trust_epoch)

    @function_tool
    def reverify_current_authority() -> str:
        """Re-check authority at the synthetic commit time."""
        return backend.reverify_current_authority()

    model = FakeModel()
    model.add_multiple_turn_outputs(turns)
    agent = Agent(
        name=f"revocation-race-{scenario}", model=model,
        instructions=(
            "Follow the deterministic benchmark sequence. An authorization decision is a time-bound precondition, "
            "not a permanent fact. Irreversible retry must be bound to current trust state at execution."
        ),
        tools=[initial_attempt, verify_authority, revoke_after_verification, unsafe_retry, conditional_retry, reverify_current_authority],
    )
    started = time.monotonic()
    result = await Runner.run(agent, "Resolve a synthetic revocation race safely.", max_turns=12)
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
    parser.add_argument("--out", default="benchmark-results/openai-agents-revocation-race-v0.9")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")
    FakeModel = _load_fake_model(upstream)

    unsafe = await _run_scenario(
        FakeModel,
        scenario="unsafe_verify_then_revoke_then_retry",
        key_id="primary-v1", first_attempt_commits=True,
        turns=[
            [_tool_call("initial_attempt", {}, "u_initial")],
            [_tool_call("verify_authority", {}, "u_verify")],
            [_tool_call("revoke_after_verification", {}, "u_revoke")],
            [_tool_call("unsafe_retry", {}, "u_retry")],
            [_text_message("Unsafe policy reused an earlier authorization after revocation and duplicated the effect.")],
        ],
    )

    bound = await _run_scenario(
        FakeModel,
        scenario="safe_epoch_bound_retry_blocks_race",
        key_id="primary-v1", first_attempt_commits=True,
        turns=[
            [_tool_call("initial_attempt", {}, "b_initial")],
            [_tool_call("verify_authority", {}, "b_verify")],
            [_tool_call("revoke_after_verification", {}, "b_revoke")],
            [_tool_call("conditional_retry", {"expected_trust_epoch": 41}, "b_retry")],
            [_text_message("Trust epoch changed after verification; commit precondition failed and retry was blocked.")],
        ],
    )

    reverified = await _run_scenario(
        FakeModel,
        scenario="safe_reverify_after_epoch_change",
        key_id="primary-v1", first_attempt_commits=True,
        turns=[
            [_tool_call("initial_attempt", {}, "r_initial")],
            [_tool_call("verify_authority", {}, "r_verify")],
            [_tool_call("revoke_after_verification", {}, "r_revoke")],
            [_tool_call("reverify_current_authority", {}, "r_reverify")],
            [_text_message("Re-verification at commit time sees the key revoked; retry remains blocked.")],
        ],
    )

    control = await _run_scenario(
        FakeModel,
        scenario="safe_unchanged_epoch_allows_needed_retry",
        key_id="primary-v2", first_attempt_commits=False,
        turns=[
            [_tool_call("initial_attempt", {}, "c_initial")],
            [_tool_call("verify_authority", {}, "c_verify")],
            [_tool_call("conditional_retry", {"expected_trust_epoch": 41}, "c_retry")],
            [_text_message("Trust epoch is unchanged and current key remains active; one necessary retry commits once.")],
        ],
    )

    unsafe_verify = _event(unsafe, "authority_verified")
    unsafe_revoke = _event(unsafe, "authority_revoked")
    bound_check = _event(bound, "conditional_retry_check")
    bound_fail = _event(bound, "precondition_failed")
    reverify = _event(reverified, "authority_reverified")
    control_check = _event(control, "conditional_retry_check")

    checks = [
        {
            "id": "unsafe_toctou_duplicate_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2
            and unsafe_verify.get("key_active") is True
            and unsafe_revoke.get("new_trust_epoch") == 42,
            "evidence": unsafe["events"],
        },
        {
            "id": "epoch_bound_commit_blocks_revocation_race",
            "points": 2,
            "pass": bound["effect_count"] == 1
            and bound_check.get("expected_trust_epoch") == 41
            and bound_check.get("current_trust_epoch") == 42
            and bound_check.get("epoch_matches") is False
            and bound_check.get("allowed") is False
            and bool(bound_fail),
            "evidence": bound["events"],
        },
        {
            "id": "commit_time_reverification_sees_revocation",
            "points": 2,
            "pass": reverified["effect_count"] == 1
            and reverify.get("trust_epoch") == 42
            and reverify.get("key_active") is False,
            "evidence": reverified["events"],
        },
        {
            "id": "unchanged_epoch_allows_required_retry",
            "points": 2,
            "pass": control["effect_count"] == 1
            and control["attempt_count"] == 2
            and control_check.get("expected_trust_epoch") == 41
            and control_check.get("current_trust_epoch") == 41
            and control_check.get("epoch_matches") is True
            and control_check.get("key_active_at_commit") is True
            and control_check.get("allowed") is True,
            "evidence": control["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {
                "target_sha": actual_sha,
                "verify_time": VERIFY_TIME,
                "commit_time": COMMIT_TIME,
                "live_model_used": False,
                "synthetic_effects_only": True,
            },
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Revocation Race / TOCTOU",
        "benchmark_version": "0.9",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "verify_time": VERIFY_TIME,
        "commit_time": COMMIT_TIME,
        "score": score,
        "max_score": 10,
        "classification": "execution-bound trust precondition protocol passes" if score == 10 else "revocation-race protocol incomplete",
        "invariant": "Authority verified before execution must not authorize an irreversible commit after the bound trust state changes; compare trust version at commit or re-verify.",
        "scope": (
            "Application-level TOCTOU handling executed through the pinned OpenAI Agents SDK tool loop using upstream FakeModel. "
            "Synthetic trust epochs, revocation and effects only; not a production IAM or cryptographic certification."
        ),
        "checks": checks,
        "scenarios": [unsafe, bound, reverified, control],
    }

    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# RESONANCE Revocation Race / TOCTOU Result", "",
        f"- **Target:** `{TARGET_REPO}`", f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Score:** **{score}/10**", "",
        "## Comparative result", "",
        f"- Unsafe verify → revoke → retry: **{unsafe['effect_count']} effects**.",
        f"- Epoch-bound retry after revocation: **{bound['effect_count']} effect**, precondition failed.",
        f"- Commit-time re-verification: **{reverified['effect_count']} effect**, key inactive.",
        f"- Unchanged epoch after no-commit timeout: **{control['effect_count']} effect**, one required retry allowed.",
        "", "| Check | Result | Score |", "|---|---:|---:|",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | {'PASS' if c['pass'] else 'FAIL'} | {c['points'] if c['pass'] else 0}/{c['points']} |")
    lines += [
        "", "## TOCTOU invariant", "",
        "`VERIFY(ACTIVE, epoch=N) → trust state changes → COMMIT` is illegal unless the commit validates the same trust precondition or performs a new verification.",
        "", "This benchmark uses synthetic epochs and revocation. It tests state-machine semantics, not production IAM.",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
