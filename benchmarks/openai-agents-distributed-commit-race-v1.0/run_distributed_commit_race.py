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
INITIAL_VERSION = 100


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


@dataclass
class SharedStore:
    version: int = INITIAL_VERSION
    effects: int = 0
    state: str = "absent"
    events: list[dict[str, Any]] = field(default_factory=list)

    def read_state(self, node: str) -> str:
        snapshot = {"node": node, "state": self.state, "version": self.version, "effects": self.effects}
        self.events.append({"event": "read", **snapshot})
        return json.dumps(snapshot, sort_keys=True)

    def unsafe_commit(self, node: str, observed_version: int) -> str:
        self.effects += 1
        self.state = "committed"
        self.version += 1
        event = {
            "event": "unsafe_commit", "node": node, "observed_version": observed_version,
            "current_version_after": self.version, "effect_count": self.effects,
        }
        self.events.append(event)
        return json.dumps(event, sort_keys=True)

    def cas_commit(self, node: str, expected_version: int) -> str:
        before = self.version
        allowed = self.state == "absent" and expected_version == self.version
        event = {
            "event": "cas_check", "node": node, "expected_version": expected_version,
            "current_version": before, "state": self.state, "allowed": allowed,
        }
        self.events.append(event)
        if not allowed:
            conflict = {"event": "precondition_failed", "node": node, "effect_count": self.effects, "version": self.version}
            self.events.append(conflict)
            return json.dumps(conflict, sort_keys=True)
        self.effects += 1
        self.state = "committed"
        self.version += 1
        commit = {"event": "cas_commit", "node": node, "effect_count": self.effects, "version": self.version}
        self.events.append(commit)
        return json.dumps(commit, sort_keys=True)


async def _run(FakeModel, scenario: str, turns: list[list[Any]]) -> dict[str, Any]:
    store = SharedStore()

    @function_tool
    def read_state(node: str) -> str:
        """Read the shared synthetic operation state and version."""
        return store.read_state(node)

    @function_tool
    def unsafe_commit(node: str, observed_version: int) -> str:
        """Commit without atomically enforcing the version that was observed earlier."""
        return store.unsafe_commit(node, observed_version)

    @function_tool
    def cas_commit(node: str, expected_version: int) -> str:
        """Atomically commit only if state is ABSENT and the shared version still equals expected_version."""
        return store.cas_commit(node, expected_version)

    model = FakeModel()
    model.add_multiple_turn_outputs(turns)
    agent = Agent(
        name=f"distributed-race-{scenario}", model=model,
        instructions=(
            "Follow the deterministic benchmark sequence. A read result is only a snapshot. "
            "For irreversible transitions, bind the write to the observed shared-state version."
        ),
        tools=[read_state, unsafe_commit, cas_commit],
    )
    started = time.monotonic()
    result = await Runner.run(agent, "Resolve a synthetic two-node commit race.", max_turns=12)
    return {
        "scenario": scenario, "effect_count": store.effects, "final_version": store.version,
        "final_state": store.state, "events": store.events,
        "final_output": str(result.final_output), "duration_seconds": round(time.monotonic() - started, 4),
    }


def _events(s: dict[str, Any], name: str) -> list[dict[str, Any]]:
    return [e for e in s["events"] if e.get("event") == name]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/openai-agents-distributed-commit-race-v1.0")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")
    FakeModel = _load_fake_model(upstream)

    unsafe = await _run(FakeModel, "unsafe_split_check_then_write", [
        [_tool_call("read_state", {"node": "A"}, "u_read_a")],
        [_tool_call("read_state", {"node": "B"}, "u_read_b")],
        [_tool_call("unsafe_commit", {"node": "B", "observed_version": INITIAL_VERSION}, "u_commit_b")],
        [_tool_call("unsafe_commit", {"node": "A", "observed_version": INITIAL_VERSION}, "u_commit_a")],
        [_text_message("Both nodes reused the same ABSENT/version=100 snapshot and committed; duplicate reproduced.")],
    ])

    cas_race = await _run(FakeModel, "safe_two_node_cas_race", [
        [_tool_call("read_state", {"node": "A"}, "c_read_a")],
        [_tool_call("read_state", {"node": "B"}, "c_read_b")],
        [_tool_call("cas_commit", {"node": "B", "expected_version": INITIAL_VERSION}, "c_commit_b")],
        [_tool_call("cas_commit", {"node": "A", "expected_version": INITIAL_VERSION}, "c_commit_a")],
        [_tool_call("read_state", {"node": "A"}, "c_reread_a")],
        [_text_message("Node B won the CAS; Node A failed the stale precondition and reread COMMITTED.")],
    ])

    unchanged = await _run(FakeModel, "safe_unchanged_version_commits", [
        [_tool_call("read_state", {"node": "A"}, "s_read_a")],
        [_tool_call("cas_commit", {"node": "A", "expected_version": INITIAL_VERSION}, "s_commit_a")],
        [_text_message("Version remained unchanged, so the conditional commit executed exactly once.")],
    ])

    stale_after_external = await _run(FakeModel, "safe_external_mutation_blocks_stale_writer", [
        [_tool_call("read_state", {"node": "A"}, "e_read_a")],
        [_tool_call("cas_commit", {"node": "B", "expected_version": INITIAL_VERSION}, "e_commit_b")],
        [_tool_call("cas_commit", {"node": "A", "expected_version": INITIAL_VERSION}, "e_commit_a")],
        [_text_message("A concurrent commit changed the version before Node A wrote; stale writer was rejected.")],
    ])

    unsafe_reads = _events(unsafe, "read")
    unsafe_commits = _events(unsafe, "unsafe_commit")
    cas_checks = _events(cas_race, "cas_check")
    cas_failures = _events(cas_race, "precondition_failed")
    cas_reads = _events(cas_race, "read")
    unchanged_commits = _events(unchanged, "cas_commit")
    external_failures = _events(stale_after_external, "precondition_failed")

    checks = [
        {
            "id": "unsafe_split_check_write_duplicate_reproduced", "points": 2,
            "pass": unsafe["effect_count"] == 2 and len(unsafe_reads) == 2
                    and all(r.get("version") == INITIAL_VERSION and r.get("state") == "absent" for r in unsafe_reads)
                    and len(unsafe_commits) == 2,
            "evidence": unsafe["events"],
        },
        {
            "id": "two_node_cas_allows_single_winner", "points": 2,
            "pass": cas_race["effect_count"] == 1 and len(cas_checks) == 2
                    and sum(1 for e in cas_checks if e.get("allowed") is True) == 1
                    and sum(1 for e in cas_checks if e.get("allowed") is False) == 1,
            "evidence": cas_race["events"],
        },
        {
            "id": "stale_writer_gets_precondition_failure_and_rereads_committed", "points": 2,
            "pass": len(cas_failures) == 1 and cas_reads[-1].get("state") == "committed"
                    and cas_reads[-1].get("effects") == 1,
            "evidence": cas_race["events"],
        },
        {
            "id": "unchanged_version_allows_progress_and_external_mutation_blocks", "points": 2,
            "pass": unchanged["effect_count"] == 1 and len(unchanged_commits) == 1
                    and stale_after_external["effect_count"] == 1 and len(external_failures) == 1,
            "evidence": {"unchanged": unchanged["events"], "external_mutation": stale_after_external["events"]},
        },
        {
            "id": "pinned_reproducible_evidence", "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {"target_sha": actual_sha, "initial_version": INITIAL_VERSION, "live_model_used": False, "synthetic_effects_only": True},
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Distributed Commit Race", "benchmark_version": "1.0",
        "target_repository": TARGET_REPO, "target_expected_sha": TARGET_SHA, "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(), "initial_version": INITIAL_VERSION,
        "score": score, "max_score": 10,
        "classification": "atomic state-version precondition protocol passes" if score == 10 else "protocol gaps observed",
        "invariant": "A read/verification snapshot must not authorize an irreversible write after shared state changes; compare and transition must be atomic or version-bound.",
        "scope": "Application-level distributed commit race executed through the pinned OpenAI Agents SDK tool loop using upstream FakeModel. Synthetic in-memory state and side effects only.",
        "checks": checks, "scenarios": [unsafe, cas_race, unchanged, stale_after_external],
    }
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result_md = f"""# RESONANCE Distributed Commit Race v1.0\n\n**Score:** {score}/10  \n**Target:** `{TARGET_REPO}@{actual_sha}`\n\n- Unsafe split check/write final effects: **{unsafe['effect_count']}**\n- Safe two-node CAS final effects: **{cas_race['effect_count']}**\n- Safe unchanged-version final effects: **{unchanged['effect_count']}**\n- Safe external-mutation final effects: **{stale_after_external['effect_count']}**\n\n**Invariant:** compare and irreversible transition must be atomic or bound to the shared-state version observed during verification.\n"""
    (out_dir / "RESULT.md").write_text(result_md, encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
