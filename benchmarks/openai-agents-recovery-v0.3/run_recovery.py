from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import subprocess
import sys
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
    ambiguity_mode: str
    attempts: dict[str, int] = field(default_factory=dict)
    effects: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

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

        if attempt == 1 and self.ambiguity_mode == "timeout_after_commit":
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

        if attempt == 1 and self.ambiguity_mode == "timeout_before_commit":
            self.events.append(
                {
                    "event": "timeout_before_commit",
                    "operation_id": operation_id,
                    "attempt": attempt,
                }
            )
            raise RuntimeError("synthetic timeout before commit; outcome unknown to caller")

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
        count = sum(1 for effect in self.effects if effect["operation_id"] == operation_id)
        status = "committed" if count > 0 else "absent"
        self.events.append(
            {
                "event": "reconcile",
                "operation_id": operation_id,
                "status": status,
                "effect_count": count,
            }
        )
        return json.dumps(
            {
                "operation_id": operation_id,
                "status": status,
                "effect_count": count,
            },
            sort_keys=True,
        )

    def effect_count(self, operation_id: str) -> int:
        return sum(1 for effect in self.effects if effect["operation_id"] == operation_id)


async def _run_scenario(
    FakeModel,
    *,
    scenario: str,
    ambiguity_mode: str,
    model_turns: list[list[Any]],
    operation_id: str,
    amount: int,
) -> dict[str, Any]:
    ledger = SyntheticLedger(ambiguity_mode=ambiguity_mode)

    @function_tool
    def charge(operation_id: str, amount: int) -> str:
        """Apply one synthetic side effect to the local benchmark ledger."""
        return ledger.charge(operation_id, amount)

    @function_tool
    def get_operation_status(operation_id: str) -> str:
        """Reconcile the synthetic ledger for a previously attempted operation."""
        return ledger.status(operation_id)

    model = FakeModel()
    model.add_multiple_turn_outputs(model_turns)
    agent = Agent(
        name=f"recovery-{scenario}",
        model=model,
        instructions="Follow the deterministic recovery sequence supplied by the benchmark model.",
        tools=[charge, get_operation_status],
    )

    started = time.monotonic()
    result = await Runner.run(agent, "Execute the synthetic operation safely.", max_turns=8)
    duration = round(time.monotonic() - started, 4)

    return {
        "scenario": scenario,
        "ambiguity_mode": ambiguity_mode,
        "operation_id": operation_id,
        "amount": amount,
        "effect_count": ledger.effect_count(operation_id),
        "attempt_count": ledger.attempts.get(operation_id, 0),
        "events": ledger.events,
        "final_output": str(result.final_output),
        "duration_seconds": duration,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--out", default="benchmark-results/openai-agents-recovery-v0.3")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_sha != TARGET_SHA:
        raise RuntimeError(f"Pinned SHA mismatch: expected {TARGET_SHA}, got {actual_sha}")

    FakeModel = _load_fake_model(upstream)
    amount = 25

    naive_op = "op-naive-after-commit"
    naive = await _run_scenario(
        FakeModel,
        scenario="blind_retry_after_unknown_commit",
        ambiguity_mode="timeout_after_commit",
        operation_id=naive_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": naive_op, "amount": amount}, "naive_charge_1")],
            [_tool_call("charge", {"operation_id": naive_op, "amount": amount}, "naive_charge_2")],
            [_text_message("Blind retry completed.")],
        ],
    )

    safe_committed_op = "op-safe-after-commit"
    safe_after_commit = await _run_scenario(
        FakeModel,
        scenario="reconcile_after_unknown_commit",
        ambiguity_mode="timeout_after_commit",
        operation_id=safe_committed_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": safe_committed_op, "amount": amount}, "safe_commit_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": safe_committed_op}, "safe_commit_status_1")],
            [_text_message("Reconciled committed state; do not retry.")],
        ],
    )

    safe_absent_op = "op-safe-before-commit"
    safe_before_commit = await _run_scenario(
        FakeModel,
        scenario="reconcile_then_retry_when_absent",
        ambiguity_mode="timeout_before_commit",
        operation_id=safe_absent_op,
        amount=amount,
        model_turns=[
            [_tool_call("charge", {"operation_id": safe_absent_op, "amount": amount}, "safe_absent_charge_1")],
            [_tool_call("get_operation_status", {"operation_id": safe_absent_op}, "safe_absent_status_1")],
            [_tool_call("charge", {"operation_id": safe_absent_op, "amount": amount}, "safe_absent_charge_2")],
            [_text_message("Reconciled absent state; one retry committed exactly once.")],
        ],
    )

    checks = [
        {
            "id": "ambiguity_hazard_reproduced",
            "points": 2,
            "pass": naive["effect_count"] == 2,
            "evidence": f"blind retry produced {naive['effect_count']} effects from one intended operation",
        },
        {
            "id": "reconcile_before_retry_after_commit",
            "points": 2,
            "pass": [event["event"] for event in safe_after_commit["events"]] == ["charge_attempt", "commit", "reconcile"],
            "evidence": safe_after_commit["events"],
        },
        {
            "id": "no_duplicate_after_confirmed_commit",
            "points": 2,
            "pass": safe_after_commit["effect_count"] == 1 and safe_after_commit["attempt_count"] == 1,
            "evidence": {
                "effect_count": safe_after_commit["effect_count"],
                "attempt_count": safe_after_commit["attempt_count"],
            },
        },
        {
            "id": "retry_only_after_confirmed_absence",
            "points": 2,
            "pass": safe_before_commit["effect_count"] == 1
            and safe_before_commit["attempt_count"] == 2
            and any(event["event"] == "reconcile" and event["status"] == "absent" for event in safe_before_commit["events"]),
            "evidence": safe_before_commit["events"],
        },
        {
            "id": "pinned_reproducible_evidence",
            "points": 2,
            "pass": actual_sha == TARGET_SHA,
            "evidence": {"target_sha": actual_sha, "synthetic_external_effects_only": True},
        },
    ]

    score = sum(item["points"] for item in checks if item["pass"])
    payload = {
        "benchmark": "RESONANCE Recovery Under Ambiguity",
        "benchmark_version": "0.3",
        "target_repository": TARGET_REPO,
        "target_expected_sha": TARGET_SHA,
        "target_actual_sha": actual_sha,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_score": 10,
        "classification": "recovery-aware application pattern passes" if score == 10 else "recovery pattern incomplete",
        "scope": (
            "Application-level recovery semantics executed through the pinned OpenAI Agents SDK tool loop using its deterministic FakeModel. "
            "Synthetic local side effects only; this is not a claim that the SDK automatically enforces idempotency or reconciliation."
        ),
        "checks": checks,
        "scenarios": [naive, safe_after_commit, safe_before_commit],
    }

    (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# RESONANCE Recovery Under Ambiguity Result",
        "",
        f"- **Target:** `{TARGET_REPO}`",
        f"- **Pinned SHA:** `{actual_sha}`",
        f"- **Recovery protocol score:** **{score}/10**",
        f"- **Classification:** {payload['classification']}",
        "",
        "## Comparative result",
        "",
        f"- Blind retry after timeout-after-commit: **{naive['effect_count']} effects** from one intended operation.",
        f"- Reconcile after timeout-after-commit: **{safe_after_commit['effect_count']} effect**, no retry.",
        f"- Reconcile after timeout-before-commit: **{safe_before_commit['effect_count']} effect**, retry only after confirmed absence.",
        "",
        "| Check | Result | Score |",
        "|---|---:|---:|",
    ]
    for item in checks:
        lines.append(f"| {item['id']} | {'PASS' if item['pass'] else 'FAIL'} | {item['points'] if item['pass'] else 0}/{item['points']} |")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The SDK faithfully executed both the unsafe and safe trajectories. The measured property is therefore an application recovery protocol: after an ambiguous outcome, reconcile durable state before deciding whether a retry is legal.",
            "",
            "The benchmark does not use a real payment rail, production credential, external service, or live model.",
        ]
    )
    (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
