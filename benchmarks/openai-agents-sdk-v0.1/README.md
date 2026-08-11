# OpenAI Agents SDK — RESONANCE Framework Baseline v0.1

This directory applies the **RESONANCE Agent Failure Benchmark** to a real open-source agent framework: [`openai/openai-agents-python`](https://github.com/openai/openai-agents-python).

## Target

- Repository: `openai/openai-agents-python`
- Pinned commit: `2231eb5d40cd4a9d6b86f79492e984eeb3301263`
- Upstream version at this revision: `0.19.4`
- License: MIT
- Python: >=3.10

The target SHA is pinned so the report can be reproduced later even if `main` changes.

## What this baseline measures

This first external run is deliberately narrower than a full safety certification. It asks whether the framework itself has executable primitives relevant to the RESONANCE Trust Graph:

**State + Causality + Phase + Transition + Time + Recovery + Verification + Evidence**

Each dimension is mapped to upstream executable tests. The run does not call a production model and does not require an OpenAI API key.

| Code | Dimension | Upstream probe |
|---|---|---|
| S | State | `tests/test_run_state.py` |
| C | Causality | `tests/test_run_internal_items.py` |
| P | Phase | `tests/test_hitl_session_scenario.py` |
| T | Transition | `tests/test_run_step_execution.py` |
| τ | Time | `tests/test_soft_cancel.py` |
| R | Recovery | `tests/test_run_internal_error_handlers.py` |
| V | Verification | `tests/test_run_step_execution.py` |
| E | Evidence | `tests/test_trace_processor.py` |
| B | Containment | Partial credit only in v0.1; no live sandbox/network boundary is exercised |
| X | Reproducibility | Pinned SHA + deterministic/offline test execution |

## Interpretation

A passing result means the pinned SDK revision exposes and tests relevant **framework mechanisms**. It does not mean every application built with the SDK is trustworthy, nor does it validate a specific model's behavior.

Application-level verification still needs:

- domain state graphs;
- authorization and phase policy;
- stale-state and concurrency injection;
- retry/idempotency/reconciliation tests;
- real containment boundaries;
- domain invariants;
- durable evidence bundles.

## Run

```bash
python run_baseline.py --upstream /path/to/openai-agents-python --out benchmark-results
```

GitHub Actions performs the canonical run and uploads `result.json` and `RESULT.md` as evidence artifacts.
