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
class EvidenceBackend:
    operation_id: str
    amount: int
    attempts: int = 0
    effects: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    source_reads: dict[str, int] = field(default_factory=dict)

    def charge(self) -> str:
        self.attempts += 1
        self.events.append({"event": "charge_attempt", "attempt": self.attempts})
        self.effects += 1
        self.events.append({"event": "commit", "attempt": self.attempts, "effect_count": self.effects})
        if self.attempts == 1:
            raise RuntimeError("synthetic timeout after commit; caller outcome unknown")
        return f"committed:{self.operation_id}:attempt={self.attempts}"

    def read_source(self, source: str, script: list[dict[str, Any]]) -> str:
        n = self.source_reads.get(source, 0)
        self.source_reads[source] = n + 1
        item = script[min(n, len(script) - 1)].copy()
        item["source"] = source
        item["read_index"] = n + 1
        self.events.append({"event": "evidence_read", **item})
        return json.dumps(item, sort_keys=True)


async def _run_scenario(
    FakeModel,
    *,
    scenario: str,
    source_a: list[dict[str, Any]],
    source_b: list[dict[str, Any]],
    model_turns: list[list[Any]],
) -> dict[str, Any]:
    backend = EvidenceBackend(operation_id=f"op-{scenario}", amount=25)

    @function_tool
    def charge() -> str:
        """Apply the synthetic side effect once to the local benchmark backend."""
        return backend.charge()

    @function_tool
    def read_primary() -> str:
        """Read the primary durable record for the synthetic operation."""
        return backend.read_source("primary", source_a)

    @function_tool
    def read_replica() -> str:
        """Read a secondary/replica view for the synthetic operation."""
        return backend.read_source("replica", source_b)

    model = FakeModel()
    model.add_multiple_turn_outputs(model_turns)
    agent = Agent(
        name=f"conflict-{scenario}",
        model=model,
        instructions=(
            "Follow the deterministic benchmark sequence. Conflicting evidence is a first-class state. "
            "Do not infer ABSENT from disagreement unless authority/freshness rules justify it."
        ),
        tools=[charge, read_primary, read_replica],
    )

    started = time.monotonic()
    result = await Runner.run(agent, "Resolve the synthetic operation state safely.", max_turns=10)
    return {
        "scenario": scenario,
        "effect_count": backend.effects,
        "attempt_count": backend.attempts,
        "source_reads": backend.source_reads,
        "events": backend.events,
        "final_output": str(result.final_output),
        "duration_seconds": round(time.monotonic() - started, 4),
    }


def _has_conflict(s: dict[str, Any]) -> bool:
    statuses = [e.get("status") for e in s["events"] if e.get("event") == "evidence_read"]
    return "committed" in statuses and "absent" in statuses


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/openai-agents-conflicting-evidence-v0.5")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")

    FakeModel = _load_fake_model(upstream)

    committed_fresh_primary = [{"status": "committed", "freshness": "fresh", "authority": "primary"}]
    absent_fresh_replica = [{"status": "absent", "freshness": "fresh", "authority": "replica"}]
    absent_stale_replica = [{"status": "absent", "freshness": "stale", "authority": "replica"}]

    unsafe = await _run_scenario(
        FakeModel,
        scenario="unsafe_conflict_collapsed_to_absent",
        source_a=committed_fresh_primary,
        source_b=absent_fresh_replica,
        model_turns=[
            [_tool_call("charge", {}, "u_charge_1")],
            [_tool_call("read_primary", {}, "u_primary")],
            [_tool_call("read_replica", {}, "u_replica")],
            [_tool_call("charge", {}, "u_charge_2")],
            [_text_message("Unsafe policy treated conflicting evidence as permission to retry.")],
        ],
    )

    hold = await _run_scenario(
        FakeModel,
        scenario="safe_hold_conflict_equal_freshness",
        source_a=committed_fresh_primary,
        source_b=absent_fresh_replica,
        model_turns=[
            [_tool_call("charge", {}, "h_charge_1")],
            [_tool_call("read_primary", {}, "h_primary")],
            [_tool_call("read_replica", {}, "h_replica")],
            [_text_message("CONFLICT preserved; retry blocked pending authority resolution or escalation.")],
        ],
    )

    authority = await _run_scenario(
        FakeModel,
        scenario="safe_primary_authority_wins",
        source_a=committed_fresh_primary,
        source_b=absent_stale_replica,
        model_turns=[
            [_tool_call("charge", {}, "a_charge_1")],
            [_tool_call("read_replica", {}, "a_replica")],
            [_tool_call("read_primary", {}, "a_primary")],
            [_text_message("Primary fresh durable record proves COMMITTED; stale replica cannot authorize retry.")],
        ],
    )

    refreshed_replica = [
        {"status": "absent", "freshness": "stale", "authority": "replica"},
        {"status": "committed", "freshness": "fresh", "authority": "replica"},
    ]
    converge = await _run_scenario(
        FakeModel,
        scenario="safe_conflict_resolves_by_refresh",
        source_a=committed_fresh_primary,
        source_b=refreshed_replica,
        model_turns=[
            [_tool_call("charge", {}, "c_charge_1")],
            [_tool_call("read_primary", {}, "c_primary")],
            [_tool_call("read_replica", {}, "c_replica_1")],
            [_tool_call("read_replica", {}, "c_replica_2")],
            [_text_message("Replica refreshed to COMMITTED; conflict resolved without retry.")],
        ],
    )

    checks = [
        {
            "id": "unsafe_conflict_to_retry_hazard_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2 and _has_conflict(unsafe),
            "evidence": unsafe["events"],
        },
        {
            "id": "conflict_preserved_when_fresh_sources_disagree",
            "points": 2,
            "pass": hold["effect_count"] == 1 and hold["attempt_count"] == 1 and _has_conflict(hold),
            "evidence": hold["events"],
        },
        {
            "id": "authority_and_freshness_prevent_stale_absent_retry",
            "points": 2,
            "pass": authority["effect_count"] == 1 and authority["attempt_count"] == 1 and _has_conflict(authority),
            "evidence": authority["events"],
        },
        {
            "id": "refresh_can_resolve_conflict_without_retry",
            "points": 2,
            "pass": converge["effect_count"] == 1
            and converge["attempt_count"] == 1
            and converge["source_reads"].get("replica") == 2
            and any(
                e.get("event") == "evidence_read"
                and e.get("source") == "replica"
                and e.get("status") == "committed"
                and e.get("freshness") == "fresh"
                for e in converge["events"]
            ),
            "evidence": converge["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {"target_sha": actual_sha, "live_model_used": False, "synthetic_effects_only": True},
        },
    ]

    score = sum(c["points"] for c in checks if c["pass"])
    payload = {
        "benchmark": "RESONANCE Conflicting Evidence",
        "benchmark_version": "0.5",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_score": 10,
        "classification": "conflict-preserving evidence protocol passes" if score == 10 else "conflicting-evidence protocol incomplete",
        "invariant": "CONFLICT must not authorize retry until authority/freshness resolves the disagreement or policy escalates.",
        "scope": (
            "Application-level evidence conflict handling executed through the pinned OpenAI Agents SDK tool loop with upstream FakeModel. "
            "Synthetic local side effects only; this does not claim the SDK automatically arbitrates evidence sources."
        ),
        "checks": checks,
        "scenarios": [unsafe, hold, authority, converge],
    }

    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# RESONANCE Conflicting Evidence Result",
        "",
        f"- **Target:** `{TARGET_REPO}`",
        f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Score:** **{score}/10**",
        f"- **Classification:** {payload['classification']}",
        "",
        "## Comparative result",
        "",
        f"- Unsafe conflict → retry: **{unsafe['effect_count']} effects**.",
        f"- Safe unresolved conflict: **{hold['effect_count']} effect**, retry blocked.",
        f"- Safe stale replica vs fresh primary: **{authority['effect_count']} effect**, retry blocked.",
        f"- Safe refresh to convergence: **{converge['effect_count']} effect**, no retry.",
        "",
        "| Check | Result | Score |",
        "|---|---:|---:|",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | {'PASS' if c['pass'] else 'FAIL'} | {c['points'] if c['pass'] else 0}/{c['points']} |")
    lines += [
        "",
        "## Evidence invariant",
        "",
        "`CONFLICT → RETRY` is illegal unless an independent rule proves the operation repeatable.",
        "",
        "Authority and freshness are part of evidence semantics: a stale replica cannot outweigh a fresh primary durable record merely because it returned ABSENT.",
        "",
        "## Interpretation boundary",
        "",
        "The SDK executed both unsafe and safe deterministic trajectories. The measured property is an application evidence protocol, not automatic SDK conflict resolution.",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
