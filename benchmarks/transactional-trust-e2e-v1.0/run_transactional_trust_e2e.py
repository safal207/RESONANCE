from __future__ import annotations

import argparse
import asyncio
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
INITIAL_STATE_VERSION = 100
CURRENT_TRUST_EPOCH = 42
STALE_TRUST_EPOCH = 41
STALE_REGISTRY_AGE_SECONDS = 600
MAX_REGISTRY_AGE_SECONDS = 120


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


@dataclass
class World:
    state: str = "absent"
    state_version: int = INITIAL_STATE_VERSION
    effects: int = 0
    source_trust_epoch: int = CURRENT_TRUST_EPOCH
    local_trust_epoch: int = STALE_TRUST_EPOCH
    local_registry_age_seconds: int = STALE_REGISTRY_AGE_SECONDS
    old_key_active_local: bool = True
    old_key_active_source: bool = False
    current_key_active_source: bool = True
    events: list[dict[str, Any]] = field(default_factory=list)
    stages: set[str] = field(default_factory=set)

    def record(self, event: str, **data: Any) -> dict[str, Any]:
        item = {"event": event, **data}
        self.events.append(item)
        return item

    def observe_state(self, node: str) -> str:
        self.stages.add("OBSERVE")
        return json.dumps(self.record(
            "observe",
            node=node,
            state=self.state,
            state_version=self.state_version,
            effects=self.effects,
        ), sort_keys=True)

    def legacy_evidence(self) -> str:
        self.stages.add("VERIFY")
        return json.dumps(self.record(
            "legacy_evidence",
            value="absent",
            signer="primary-v1",
            signature_valid=True,
            evidence_fresh=True,
            local_trust_epoch=self.local_trust_epoch,
            local_registry_age_seconds=self.local_registry_age_seconds,
            local_key_active=self.old_key_active_local,
        ), sort_keys=True)

    def unsafe_accept_legacy(self) -> str:
        self.stages.add("AUTHORIZE")
        accepted = True
        return json.dumps(self.record(
            "unsafe_authorize",
            signer="primary-v1",
            accepted=accepted,
            ignored_registry_staleness=True,
            ignored_source_revocation=True,
            registry_age_seconds=self.local_registry_age_seconds,
        ), sort_keys=True)

    def refresh_trust(self) -> str:
        self.stages.add("AUTHORIZE")
        self.local_trust_epoch = self.source_trust_epoch
        self.local_registry_age_seconds = 0
        self.old_key_active_local = self.old_key_active_source
        return json.dumps(self.record(
            "trust_refresh",
            trust_epoch=self.local_trust_epoch,
            registry_age_seconds=self.local_registry_age_seconds,
            old_key_active=self.old_key_active_local,
            current_key_active=self.current_key_active_source,
        ), sort_keys=True)

    def verify_legacy_after_refresh(self) -> str:
        self.stages.add("VERIFY")
        trusted = (
            self.local_registry_age_seconds <= MAX_REGISTRY_AGE_SECONDS
            and self.old_key_active_local
        )
        return json.dumps(self.record(
            "legacy_verification",
            signature_valid=True,
            evidence_fresh=True,
            registry_fresh=self.local_registry_age_seconds <= MAX_REGISTRY_AGE_SECONDS,
            key_active=self.old_key_active_local,
            trusted=trusted,
        ), sort_keys=True)

    def current_evidence(self) -> str:
        self.stages.add("VERIFY")
        trusted = self.current_key_active_source and self.local_trust_epoch == self.source_trust_epoch
        return json.dumps(self.record(
            "current_evidence",
            value=self.state,
            state_version=self.state_version,
            signer="primary-v2",
            signature_valid=True,
            evidence_fresh=True,
            trust_epoch=self.source_trust_epoch,
            trusted=trusted,
        ), sort_keys=True)

    def bind(self, node: str, expected_state_version: int, expected_trust_epoch: int) -> str:
        self.stages.add("BIND")
        return json.dumps(self.record(
            "bind",
            node=node,
            expected_state_version=expected_state_version,
            expected_trust_epoch=expected_trust_epoch,
        ), sort_keys=True)

    def unsafe_commit_timeout_after_commit(self, node: str, observed_version: int) -> str:
        self.stages.add("COMMIT")
        self.effects += 1
        self.state = "committed"
        self.state_version += 1
        self.record(
            "unsafe_commit",
            node=node,
            observed_version=observed_version,
            effect_count=self.effects,
            state_version=self.state_version,
        )
        self.record("ambiguous_outcome", node=node, outcome="timeout_after_commit")
        return json.dumps({"status": "TIMEOUT", "commit_visibility": "unknown_to_caller"}, sort_keys=True)

    def unsafe_blind_retry(self, node: str, reason: str) -> str:
        self.stages.add("RECONCILE")
        self.stages.add("COMMIT")
        self.effects += 1
        self.state = "committed"
        self.state_version += 1
        return json.dumps(self.record(
            "unsafe_retry_commit",
            node=node,
            reason=reason,
            effect_count=self.effects,
            state_version=self.state_version,
        ), sort_keys=True)

    def cas_commit(self, node: str, expected_state_version: int, expected_trust_epoch: int, timeout_after_commit: bool) -> str:
        self.stages.add("COMPARE")
        state_match = self.state == "absent" and self.state_version == expected_state_version
        trust_match = self.source_trust_epoch == expected_trust_epoch
        allowed = state_match and trust_match
        self.record(
            "compare",
            node=node,
            expected_state_version=expected_state_version,
            current_state_version=self.state_version,
            expected_trust_epoch=expected_trust_epoch,
            current_trust_epoch=self.source_trust_epoch,
            state=self.state,
            allowed=allowed,
        )
        if not allowed:
            return json.dumps(self.record(
                "precondition_failed",
                node=node,
                effect_count=self.effects,
                state=self.state,
                state_version=self.state_version,
            ), sort_keys=True)

        self.stages.add("COMMIT")
        self.effects += 1
        self.state = "committed"
        self.state_version += 1
        self.record(
            "cas_commit",
            node=node,
            effect_count=self.effects,
            state_version=self.state_version,
        )
        if timeout_after_commit:
            self.record("ambiguous_outcome", node=node, outcome="timeout_after_commit")
            return json.dumps({"status": "TIMEOUT", "commit_visibility": "unknown_to_caller"}, sort_keys=True)
        return json.dumps({"status": "COMMITTED", "effect_count": self.effects}, sort_keys=True)

    def reconcile(self, node: str) -> str:
        self.stages.add("RECONCILE")
        return json.dumps(self.record(
            "reconcile",
            node=node,
            state=self.state,
            state_version=self.state_version,
            effects=self.effects,
            trust_epoch=self.source_trust_epoch,
        ), sort_keys=True)

    def prove(self, node: str) -> str:
        self.stages.add("PROVE")
        invariant_ok = self.effects == 1 and self.state == "committed"
        return json.dumps(self.record(
            "proof",
            node=node,
            invariant="at_most_one_committed_effect",
            invariant_ok=invariant_ok,
            final_state=self.state,
            final_state_version=self.state_version,
            effect_count=self.effects,
            observed_stages=sorted(self.stages),
        ), sort_keys=True)


async def _run(FakeModel, scenario: str, turns: list[list[Any]]) -> dict[str, Any]:
    world = World()

    @function_tool
    def observe_state(node: str) -> str:
        """Observe the synthetic shared operation state and version."""
        return world.observe_state(node)

    @function_tool
    def legacy_evidence() -> str:
        """Return fresh signed evidence from an old authority evaluated against a stale local trust snapshot."""
        return world.legacy_evidence()

    @function_tool
    def unsafe_accept_legacy() -> str:
        """Unsafely accept legacy authority without refreshing stale trust state."""
        return world.unsafe_accept_legacy()

    @function_tool
    def refresh_trust() -> str:
        """Refresh local trust state from the synthetic source of truth."""
        return world.refresh_trust()

    @function_tool
    def verify_legacy_after_refresh() -> str:
        """Re-evaluate old signed evidence after refreshing the trust registry."""
        return world.verify_legacy_after_refresh()

    @function_tool
    def current_evidence() -> str:
        """Return current trusted evidence from the active synthetic authority."""
        return world.current_evidence()

    @function_tool
    def bind(node: str, expected_state_version: int, expected_trust_epoch: int) -> str:
        """Bind an action decision to observed state and trust versions."""
        return world.bind(node, expected_state_version, expected_trust_epoch)

    @function_tool
    def unsafe_commit_timeout_after_commit(node: str, observed_version: int) -> str:
        """Commit without an atomic precondition and then return a synthetic timeout."""
        return world.unsafe_commit_timeout_after_commit(node, observed_version)

    @function_tool
    def unsafe_blind_retry(node: str, reason: str) -> str:
        """Unsafely retry without reconciliation or current preconditions."""
        return world.unsafe_blind_retry(node, reason)

    @function_tool
    def cas_commit(node: str, expected_state_version: int, expected_trust_epoch: int, timeout_after_commit: bool) -> str:
        """Atomically compare state/trust versions and commit only if both still match."""
        return world.cas_commit(node, expected_state_version, expected_trust_epoch, timeout_after_commit)

    @function_tool
    def reconcile(node: str) -> str:
        """Read current authoritative synthetic state after an ambiguous outcome or conflict."""
        return world.reconcile(node)

    @function_tool
    def prove(node: str) -> str:
        """Emit the final invariant and protocol-stage evidence for this synthetic run."""
        return world.prove(node)

    model = FakeModel()
    model.add_multiple_turn_outputs(turns)
    agent = Agent(
        name=f"ttp-e2e-{scenario}",
        model=model,
        instructions=(
            "Execute the deterministic benchmark sequence. Treat timeout as ambiguous, stale trust as untrusted, "
            "bind decisions to state/trust versions, compare at commit, reconcile ambiguity, and preserve proof."
        ),
        tools=[
            observe_state, legacy_evidence, unsafe_accept_legacy, refresh_trust,
            verify_legacy_after_refresh, current_evidence, bind,
            unsafe_commit_timeout_after_commit, unsafe_blind_retry,
            cas_commit, reconcile, prove,
        ],
    )
    started = time.monotonic()
    result = await Runner.run(agent, "Execute the TTP end-to-end adversarial scenario.", max_turns=20)
    return {
        "scenario": scenario,
        "effect_count": world.effects,
        "final_state": world.state,
        "final_state_version": world.state_version,
        "source_trust_epoch": world.source_trust_epoch,
        "events": world.events,
        "stages": sorted(world.stages),
        "final_output": str(result.final_output),
        "duration_seconds": round(time.monotonic() - started, 4),
    }


def _events(scenario: dict[str, Any], event: str) -> list[dict[str, Any]]:
    return [e for e in scenario["events"] if e.get("event") == event]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/transactional-trust-e2e-v1.0")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")
    FakeModel = _load_fake_model(upstream)

    unsafe = await _run(FakeModel, "unsafe_compounded_failure", [
        [_tool_call("observe_state", {"node": "A"}, "u_observe")],
        [_tool_call("legacy_evidence", {}, "u_legacy")],
        [_tool_call("unsafe_accept_legacy", {}, "u_authorize")],
        [_tool_call("unsafe_commit_timeout_after_commit", {"node": "B", "observed_version": INITIAL_STATE_VERSION}, "u_competitor")],
        [_tool_call("unsafe_blind_retry", {"node": "A", "reason": "stale ABSENT treated as retry permission"}, "u_retry_a")],
        [_tool_call("unsafe_blind_retry", {"node": "A", "reason": "timeout treated as failure without reconciliation"}, "u_retry_b")],
        [_text_message("Unsafe compounded path accepted stale revoked authority, ignored the race and retried ambiguity; duplicates reproduced.")],
    ])

    safe = await _run(FakeModel, "safe_ttp_v1_end_to_end", [
        [_tool_call("observe_state", {"node": "A"}, "s_observe")],
        [_tool_call("legacy_evidence", {}, "s_legacy")],
        [_tool_call("refresh_trust", {}, "s_refresh")],
        [_tool_call("verify_legacy_after_refresh", {}, "s_verify_old")],
        [_tool_call("current_evidence", {}, "s_current_evidence")],
        [_tool_call("bind", {"node": "A", "expected_state_version": INITIAL_STATE_VERSION, "expected_trust_epoch": CURRENT_TRUST_EPOCH}, "s_bind_a")],
        [_tool_call("bind", {"node": "B", "expected_state_version": INITIAL_STATE_VERSION, "expected_trust_epoch": CURRENT_TRUST_EPOCH}, "s_bind_b")],
        [_tool_call("cas_commit", {"node": "B", "expected_state_version": INITIAL_STATE_VERSION, "expected_trust_epoch": CURRENT_TRUST_EPOCH, "timeout_after_commit": True}, "s_competitor_commit")],
        [_tool_call("cas_commit", {"node": "A", "expected_state_version": INITIAL_STATE_VERSION, "expected_trust_epoch": CURRENT_TRUST_EPOCH, "timeout_after_commit": False}, "s_stale_writer")],
        [_tool_call("reconcile", {"node": "A"}, "s_reconcile")],
        [_tool_call("current_evidence", {}, "s_final_evidence")],
        [_tool_call("prove", {"node": "A"}, "s_prove")],
        [_text_message("TTP preserved one effect: stale authority rejected, one CAS winner committed ambiguously, stale writer failed, reconciliation proved COMMITTED.")],
    ])

    required_stages = {"OBSERVE", "VERIFY", "AUTHORIZE", "BIND", "COMPARE", "COMMIT", "RECONCILE", "PROVE"}
    safe_legacy_verify = _events(safe, "legacy_verification")
    safe_refresh = _events(safe, "trust_refresh")
    safe_compare = _events(safe, "compare")
    safe_failures = _events(safe, "precondition_failed")
    safe_reconcile = _events(safe, "reconcile")
    safe_proof = _events(safe, "proof")
    unsafe_retries = _events(unsafe, "unsafe_retry_commit")

    checks = [
        {
            "id": "unsafe_compounded_failure_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 3 and len(unsafe_retries) == 2,
            "evidence": {"effect_count": unsafe["effect_count"], "events": unsafe["events"]},
        },
        {
            "id": "stale_registry_refresh_rejects_revoked_legacy_authority",
            "points": 2,
            "pass": len(safe_refresh) == 1 and len(safe_legacy_verify) == 1
                    and safe_refresh[0].get("old_key_active") is False
                    and safe_legacy_verify[0].get("trusted") is False,
            "evidence": {"refresh": safe_refresh, "legacy_verification": safe_legacy_verify},
        },
        {
            "id": "atomic_compare_allows_one_competing_writer_and_blocks_stale_writer",
            "points": 2,
            "pass": safe["effect_count"] == 1 and len(safe_compare) == 2
                    and sum(1 for e in safe_compare if e.get("allowed") is True) == 1
                    and sum(1 for e in safe_compare if e.get("allowed") is False) == 1
                    and len(safe_failures) == 1,
            "evidence": {"compare": safe_compare, "precondition_failed": safe_failures},
        },
        {
            "id": "ambiguous_commit_reconciled_before_any_retry_and_final_invariant_proved",
            "points": 2,
            "pass": len(safe_reconcile) == 1 and safe_reconcile[0].get("state") == "committed"
                    and safe_reconcile[0].get("effects") == 1
                    and len(safe_proof) == 1 and safe_proof[0].get("invariant_ok") is True,
            "evidence": {"reconcile": safe_reconcile, "proof": safe_proof},
        },
        {
            "id": "all_ttp_stages_covered_with_pinned_reproducible_evidence",
            "points": 2,
            "pass": required_stages.issubset(set(safe["stages"])) and actual_sha == TARGET_SHA,
            "evidence": {
                "required_stages": sorted(required_stages),
                "observed_stages": safe["stages"],
                "target_sha": actual_sha,
                "live_model_used": False,
                "synthetic_effects_only": True,
            },
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Transactional Trust Protocol End-to-End Adversarial",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "protocol_chain": "OBSERVE -> VERIFY -> AUTHORIZE -> BIND -> COMPARE -> COMMIT -> RECONCILE -> PROVE",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_score": 10,
        "classification": "TTP v1.0 end-to-end protocol passes compounded synthetic hazards" if score == 10 else "TTP v1.0 protocol gaps observed",
        "hazards_composed": [
            "ambiguous timeout after commit",
            "fresh-but-obsolete legacy evidence",
            "revoked authority",
            "stale trust registry",
            "competing writer",
            "stale state version",
            "blind retry pressure",
        ],
        "invariant": "One logical consequential operation produces at most one committed effect while evidence, authority, trust state and shared-state versions remain bound to the mutation and ambiguity is reconciled before retry.",
        "checks": checks,
        "scenarios": [unsafe, safe],
        "scope": "Framework-agnostic application protocol executed through a pinned OpenAI Agents SDK FakeModel tool loop. Synthetic in-memory trust/state/evidence and side effects only.",
        "vulnerability_claim": False,
        "external_safety_certification": False,
    }

    (out_dir / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result_md = f"""# RESONANCE TTP v1.0 End-to-End Adversarial Benchmark\n\n**Score:** {score}/10  \n**Target:** `{TARGET_REPO}@{actual_sha}`\n\n- Unsafe compounded path effects: **{unsafe['effect_count']}**\n- Safe TTP path effects: **{safe['effect_count']}**\n- Safe stages covered: **{', '.join(safe['stages'])}**\n\n**Protocol:** OBSERVE → VERIFY → AUTHORIZE → BIND → COMPARE → COMMIT → RECONCILE → PROVE\n"""
    (out_dir / "RESULT.md").write_text(result_md, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
