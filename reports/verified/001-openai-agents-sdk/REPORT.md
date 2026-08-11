# RESONANCE Verified Report #001

# OpenAI Agents SDK — Framework Trust Baseline

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Agent Failure Benchmark — Framework Baseline v0.1  
**Executed:** 2026-08-11T01:33:20Z  
**GitHub Actions run:** `31449604425`  
**Evidence artifact:** `resonance-openai-agents-baseline`  
**Artifact digest:** `sha256:d0759dc612a299abc976bc45fe4a45aec8da6bfbcbd50c7194a95c464e39c3bb`

## Result

# **95 / 100**

**Classification: strong structural baseline**

The pinned OpenAI Agents SDK revision passed all eight executable framework probes used for State, Causality, Phase, Transition, Time, Recovery, Verification, and Evidence.

Containment received partial credit because this baseline did **not** exercise a real sandbox, operating-system privilege boundary, or network boundary.

This score is **not a safety certification** for applications built with the SDK.

## What actually ran

The benchmark cloned the upstream repository at the exact target SHA, installed the SDK, and executed selected upstream test suites without a production API key or live model dependency.

Seven unique upstream suites executed **597 tests**:

| Suite | Tests | Result | RESONANCE dimension |
|---|---:|---|---|
| `tests/test_run_state.py` | 348 | PASS | State |
| `tests/test_run_internal_items.py` | 53 | PASS | Causality |
| `tests/test_hitl_session_scenario.py` | 2 | PASS | Phase |
| `tests/test_run_step_execution.py` | 108 | PASS | Transition + Verification |
| `tests/test_soft_cancel.py` | 25 | PASS | Time |
| `tests/test_run_internal_error_handlers.py` | 5 | PASS | Recovery |
| `tests/test_trace_processor.py` | 56 | PASS | Evidence |
| **Total unique tests** | **597** | **PASS** | |

## Scorecard

| Code | Dimension | Result | Score | Evidence |
|---|---|---:|---:|---|
| S | State | PASS | 10/10 | Run state, serialization, approval/rejection and resume semantics have executable coverage. |
| C | Causality | PASS | 10/10 | Run-item structures and tool/action correlation have executable coverage. |
| P | Phase | PASS | 10/10 | Approval-gated tool execution can interrupt, persist and resume before execution. |
| T | Transition | PASS | 10/10 | Step resolution, tool execution, interruptions and execution outcomes are tested. |
| τ | Time | PASS | 10/10 | Immediate vs after-turn cancellation semantics are explicitly tested. |
| R | Recovery | PASS | 10/10 | Run error-handler paths have executable coverage. |
| V | Verification | PASS | 10/10 | Tool guardrail and execution-result paths are exercised by the run-step suite. |
| E | Evidence | PASS | 10/10 | Trace processing has executable coverage for inspectable execution evidence. |
| B | Containment | PARTIAL | 5/10 | Guardrails/approvals/cancellation are covered, but no real sandbox or network boundary was exercised. |
| X | Reproducibility | PASS | 10/10 | Exact target SHA, deterministic/offline framework test execution, durable artifact. |

## Strongest finding

The SDK already has substantial executable machinery around the parts of agent behavior that become important once software acts across tools and time:

```text
state
  + tool/action correlation
  + approval interruption/resume
  + step execution
  + cancellation timing
  + error handling
  + guardrails
  + tracing
```

That makes it a strong substrate for application-level trust engineering.

## The missing 5 points matter

The 95/100 score should not be read as "95% safe."

The largest untested boundary in this run is **containment**. A framework may correctly manage state, approval, tracing and error handling while an application still exposes excessive filesystem, shell, credential, network or production access.

A stronger v0.2 run should therefore add an actual sandbox boundary and verify that a deliberately overreaching tool trajectory cannot escape its declared environment.

## Interpretation boundary

This report verifies **framework capability coverage at one pinned revision**. It does not verify:

- a specific OpenAI model;
- prompt-injection resistance of an application;
- correctness of user-defined tools;
- domain-specific state machines or invariants;
- financial authorization or idempotency;
- production credential isolation;
- network containment;
- the safety of arbitrary applications built with the SDK.

Those properties live above or beside the framework and require application-specific tests.

## Reproducibility

Canonical harness:

`benchmarks/openai-agents-sdk-v0.1/run_baseline.py`

Canonical workflow:

`.github/workflows/benchmark-openai-agents.yml`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31449604425`

## Verdict

**OpenAI Agents SDK v0.19.4 at the tested revision demonstrates a strong structural baseline for building verifiable agent workflows.**

Its framework primitives cover the majority of the RESONANCE Trust Graph dimensions exercised here. The next verification frontier is not another unit-test pass; it is containment plus application-specific invariants under injected faults.

---

**RESONANCE Verified Report #001**  
**Status:** Reproducible framework baseline  
**Score:** 95/100  
**Critical-failure cap:** Not triggered  
**External safety certification:** No
