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
        id="final_message",
        type="message",
        role="assistant",
        content=[
            ResponseOutputText(
                text=text,
                type="output_text",
                annotations=[],
                logprobs=[],
            )
        ],
        status="completed",
    )


@dataclass
class SyntheticLedger:
    reconcile_script: list[str]
    attempts: dict[str, int] = field(default_factory=dict)
    effects: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    reconcile_calls: int = 0

    def charge(self, operation_id: str, amount: int) -> str:
        attempt = self.attempts.get(operation_id, 0) + 1
        self.attempts[operation_id] = attempt
        self.events.append(
            {
                "event": "charge_attempt",
                "operation_id": operation_id,
                "attempt": attempt,
                "amount": amount,
            }
        )

        # First attempt commits durably, but the response is lost. The caller therefore sees UNKNOWN.
        if attempt == 1:
            self.effects.append(
                {
                    "operation_id": operation_id,
                    "amount": amount,
                    "effect_index": len(self.effects) + 1,
                }
            )
            self.events.append(
                {
                    "event": "commit",
                    "operation_id": operation_id,
                    "attempt": attempt,
                    "response": "lost",
                }
            )
            raise RuntimeError("synthetic timeout after commit; outcome unknown to caller")

        self.effects.append(
            {
                "operation_id": operation_id,
                "amount": amount,
                "effect_index": len(self.effects) + 1,
            }
        )
        self.events.append(
            {
                "event": "commit",
                "operation_id": operation_id,
                "attempt": attempt,
                "response": "delivered",
            }
        )
        return f"committed:{operation_id}:attempt={attempt}"

    def status(self, operation_id: str) -> str:
        self.reconcile_calls += 1
        index = min(self.reconcile_calls - 1, len(self.reconcile_script) - 1)
        outcome = self.reconcile_script[index]
        effect_count = self.effect_count(operation_id)

        if outcome == "timeout":
            self.events.append(
                {
                    "event": "reconcile",
                    "operation_id": operation_id,
                    "status": "unknown",
                    "reason": "status_timeout",
                    "effect_count_hidden": effect_count,
                }
            )
            raise RuntimeError("synthetic reconciliation timeout; durable outcome still unknown")

        if outcome == "stale_unknown":
            payload = {
                "operation_id": operation_id,
                "status": "unknown",
                "freshness": "stale",
                "authorizes_retry": False,
            }
            self.events.append(
                {
                    "event": "reconcile",
                    "operation_id": operation_id,
                    "status": "unknown",
                    "reason": "stale_snapshot",
                    "freshness": "stale",
                    "effect_count_hidden": effect_count,
                }
            )
            return json.dumps(payload, sort_keys=True)

        if outcome == "committed":
            status = "committed" if effect_count > 0 else "absent"
            payload = {
                "operation_id": operation_id,
                "status": status,
                "freshness": "fresh",
                "effect_count": effect_count,
                "authorizes_retry": status == "absent",
            }
            self.events.append(
                {
                    "event": "reconcile",
                    "operation_id": operation_id,
                    "status": status,
                    "reason": "fresh_read",
                    "freshness": "fresh",
                    "effect_count": effect_count,
                }
            )
            return json.dumps(payload, sort_keys=True)

        raise RuntimeError(f"Unknown reconcile outcome: {outcome}")

    def effect_count(self, operation_id: str) -> int:
        return sum(1 for effect in self.effects if effect["operation_id"] == operation_id)


async def _run_scenario(
    FakeModel,
    *,
    scenario: str,
    reconcile_script: list[str],
    model_turns: list[list[Any]],
    operation_id: str,
    amount: int,
) -> dict[str, Any]:
    ledger = SyntheticLedger(reconcile_script=reconcile_script)

    @function_tool
    def charge(operation_id: str, amount: int) -> str:
        """Apply one synthetic side effect to the local benchmark ledger."""
        return ledger.charge(operation_id, amount)

    @function_tool
    def get_operation_status(operation_id: str) -> str:
        """Attempt to reconcile durable state for a previously attempted operation."""
        return ledger.status(operation_id)

    model = FakeModel()
    model.add_multiple_turn_outputs(model_turns)
    agent = Agent(
        name=f"ambiguous-reconcile-{scenario}",
        model=model,
        instructions=(
            "Follow the deterministic tool sequence supplied by the benchmark model. "
            "UNKNOWN is a first-class state and does not imply ABSENT."
        ),
        tools=[charge, get_operation_status],
    )

    started = time.monotonic()
    result = await Runner.run(agent, "Execute the synthetic operation with recovery semantics.", max_turns=10)

    return {
        "scenario": scenario,
        "operation_id": operation_id,
        "amount": amount,
        "effect_count": ledger.effect_count(operation_id),
        "attempt_count": ledger.attempts.get(operation_id, 0),
        "reconcile_calls": ledger.reconcile_calls,
        "events": ledger.events,
        "final_output": str(result.final_output),
        "duration_seconds": round(time.monotonic() - started, 4),
    }


def _has_unknown_reconcile(scenario: dict[str, Any]) -> bool:
    return any(
        event.get("event") == "reconcile" and event.get("status") == "unknown"
        for event in scenario["events"]
    )


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument(
        "--out",
        default="benchmark-results/openai-agents-ambiguous-reconciliation-v0.4",
    )
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")

    FakeModel = _load_fake_model(upstream)
    amount = 25

    unsafe_op = "op-unsafe-unknown-reconcile"
    unsafe = await _run_scenario(
        FakeModel,
        scenario="unsafe_retry_after_unknown_reconciliation",
        reconcile_script=["timeout"],
        operation_id=unsafe_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": unsafe_op, "amount": amount}, "unsafe_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": unsafe_op}, "unsafe_status_1")],
            [_tool_call("charge", {"operation_id": unsafe_op, "amount": amount}, "unsafe_charge_2")],
            [_text_message("Unsafe policy converted UNKNOWN into RETRY.")],
        ],
    )

    hold_op = "op-safe-hold-unknown"
    safe_hold = await _run_scenario(
        FakeModel,
        scenario="safe_hold_unknown_after_reconciliation_timeout",
        reconcile_script=["timeout"],
        operation_id=hold_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": hold_op, "amount": amount}, "hold_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": hold_op}, "hold_status_1")],
            [_text_message("Reconciliation is still UNKNOWN; retry blocked and escalation required.")],
        ],
    )

    stale_op = "op-safe-stale-unknown"
    safe_stale = await _run_scenario(
        FakeModel,
        scenario="safe_stale_status_does_not_authorize_retry",
        reconcile_script=["stale_unknown"],
        operation_id=stale_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": stale_op, "amount": amount}, "stale_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": stale_op}, "stale_status_1")],
            [_text_message("Stale UNKNOWN is not ABSENT; retry remains blocked.")],
        ],
    )

    resolve_op = "op-safe-eventual-resolution"
    safe_resolve = await _run_scenario(
        FakeModel,
        scenario="safe_unknown_then_fresh_committed",
        reconcile_script=["timeout", "committed"],
        operation_id=resolve_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": resolve_op, "amount": amount}, "resolve_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": resolve_op}, "resolve_status_1")],
            [_tool_call("get_operation_status", {"operation_id": resolve_op}, "resolve_status_2")],
            [_text_message("Fresh reconciliation confirmed COMMITTED; no retry required.")],
        ],
    )

    checks = [
        {
            "id": "unsafe_unknown_to_retry_hazard_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2 and _has_unknown_reconcile(unsafe),
            "evidence": unsafe["events"],
        },
        {
            "id": "unknown_preserved_after_reconcile_timeout",
            "points": 2,
            "pass": safe_hold["effect_count"] == 1
            and safe_hold["attempt_count"] == 1
            and _has_unknown_reconcile(safe_hold),
            "evidence": safe_hold["events"],
        },
        {
            "id": "stale_unknown_not_treated_as_absent",
            "points": 2,
            "pass": safe_stale["effect_count"] == 1
            and safe_stale["attempt_count"] == 1
            and any(
                event.get("event") == "reconcile"
                and event.get("status") == "unknown"
                and event.get("freshness") == "stale"
                for event in safe_stale["events"]
            ),
            "evidence": safe_stale["events"],
        },
        {
            "id": "repeat_reconciliation_can_resolve_without_retry",
            "points": 2,
            "pass": safe_resolve["effect_count"] == 1
            and safe_resolve["attempt_count"] == 1
            and safe_resolve["reconcile_calls"] == 2
            and any(
                event.get("event") == "reconcile"
                and event.get("status") == "committed"
                and event.get("freshness") == "fresh"
                for event in safe_resolve["events"]
            ),
            "evidence": safe_resolve["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {
                "target_sha": actual_sha,
                "synthetic_external_effects_only": True,
                "live_model_used": False,
            },
        },
    ]

    score = sum(item["points"] for item in checks if item["pass"])
    payload = {
        "benchmark": "RESONANCE Ambiguous Reconciliation",
        "benchmark_version": "0.4",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_score": 10,
        "classification": (
            "UNKNOWN-preserving recovery pattern passes"
            if score == 10
            else "ambiguous reconciliation handling incomplete"
        ),
        "invariant": "UNKNOWN reconciliation outcome must not authorize retry.",
        "scope": (
            "Application-level ambiguity preservation executed through the pinned OpenAI Agents SDK tool loop using its deterministic FakeModel. "
            "Synthetic local side effects only; this does not claim that the SDK automatically enforces recovery policy."
        ),
        "checks": checks,
        "scenarios": [unsafe, safe_hold, safe_stale, safe_resolve],
    }

    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RESONANCE Ambiguous Reconciliation Result",
        "",
        f"- **Target:** `{TARGET_REPO}`",
        f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Ambiguous reconciliation score:** **{score}/10**",
        f"- **Classification:** {payload['classification']}",
        "",
        "## Comparative result",
        "",
        f"- Unsafe UNKNOWN → RETRY: **{unsafe['effect_count']} effects**.",
        f"- Safe timeout → HOLD UNKNOWN: **{safe_hold['effect_count']} effect**, retry blocked.",
        f"- Safe stale UNKNOWN: **{safe_stale['effect_count']} effect**, retry blocked.",
        f"- UNKNOWN → later fresh COMMITTED: **{safe_resolve['effect_count']} effect**, no retry.",
        "",
        "| Check | Result | Score |",
        "|---|---:|---:|",
    ]
    for item in checks:
        lines.append(
            f"| {item['id']} | {'PASS' if item['pass'] else 'FAIL'} | "
            f"{item['points'] if item['pass'] else 0}/{item['points']} |"
        )
    lines.extend(
        [
            "",
            "## Recovery invariant",
            "",
            "`UNKNOWN → RETRY` is illegal unless an independent rule proves the operation is safe to repeat.",
            "",
            "A timeout, stale read, unavailable status endpoint or otherwise inconclusive reconciliation result must preserve UNKNOWN. The next legal transitions are another reconciliation attempt, escalation, compensation policy, or a separately proven idempotent retry path.",
            "",
            "## Interpretation boundary",
            "",
            "The SDK faithfully executed both the unsafe and safe trajectories. The measured property is an application protocol for preserving uncertainty, not an automatic SDK safety guarantee.",
            "",
            "No production API key, real payment rail, external service, real credential, or live model was used.",
        ]
    )
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
