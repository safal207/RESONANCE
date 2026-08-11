# RESONANCE Verified Report #003

# OpenAI Agents SDK — Recovery Under Ambiguity

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Recovery Under Ambiguity v0.3  
**Executed:** 2026-08-11T03:04:16Z  
**GitHub Actions run:** `31454264702`  
**Evidence artifact:** `resonance-openai-agents-recovery-v0.3`  
**Artifact digest:** `sha256:9d0141eb981822e14e14ca51721e5b01affd4a3fb26efbe73128b5e199ecfb8d`

## Result

# **10 / 10 — Recovery protocol**

**Classification: recovery-aware application pattern passes**

The benchmark reproduced the classic ambiguous-outcome failure: a side effect committed, the response was lost, and a blind retry produced a second side effect.

The same pinned OpenAI Agents SDK tool loop then executed a recovery-aware trajectory:

```text
attempt
  → timeout / outcome unknown
  → reconcile durable state
      ├─ committed → STOP, do not retry
      └─ absent    → retry once
```

Both recovery-aware branches ended with exactly one side effect.

The strongest finding is not that the SDK "solves retries." It does not automatically impose this policy. The SDK faithfully executed both the unsafe and safe trajectories. **Recovery correctness lives in the application protocol unless a lower layer provides stronger idempotency guarantees.**

## Comparative result

| Scenario | Observed trajectory | Final effects |
|---|---|---:|
| Blind retry after timeout-after-commit | `charge → commit → response lost → charge again → commit` | **2** |
| Reconcile after timeout-after-commit | `charge → commit → response lost → status=committed → stop` | **1** |
| Reconcile after timeout-before-commit | `charge → timeout before commit → status=absent → retry → commit` | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Ambiguity hazard reproduced | PASS | 2/2 |
| Reconcile before retry after unknown commit | PASS | 2/2 |
| No duplicate after confirmed commit | PASS | 2/2 |
| Retry only after confirmed absence | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## What actually ran

The GitHub Actions job:

1. cloned `openai/openai-agents-python` at the exact pinned SHA;
2. installed that revision;
3. loaded the upstream deterministic `FakeModel` used by the SDK's own tests;
4. defined two local function tools through the SDK: `charge` and `get_operation_status`;
5. executed three deterministic tool trajectories through `Runner.run`;
6. preserved the synthetic ledger event sequence, effect count, attempt count and final output;
7. emitted `result.json` and `RESULT.md` as a durable evidence artifact.

No production API key, live model, real payment rail, external service or real credential was used.

## Scenario 1 — blind retry duplicates the effect

The synthetic backend was configured so the first call commits successfully and then raises a timeout before the caller receives the response.

Observed evidence:

```text
charge_attempt #1
commit #1
response lost
charge_attempt #2
commit #2
```

Final effect count: **2**.

This is the core ambiguity problem: `timeout` is not equivalent to `not committed`.

## Scenario 2 — reconcile after an unknown commit

The first call again committed and lost its response. Instead of retrying, the next tool call queried durable operation state.

Observed evidence:

```text
charge_attempt #1
commit #1
response lost
reconcile → committed
STOP
```

Final effect count: **1**.  
Final attempt count: **1**.

The retry was suppressed because durable state proved the intended effect already existed.

## Scenario 3 — retry only after confirmed absence

The first call timed out before commit. The recovery path did not assume failure; it reconciled state first.

Observed evidence:

```text
charge_attempt #1
timeout before commit
reconcile → absent
charge_attempt #2
commit #1
```

Final effect count: **1**.  
Final attempt count: **2**.

The retry became legal only after the system had evidence that the previous attempt did not commit.

## The recovery invariant

A useful recovery invariant for non-idempotent or ambiguously idempotent actions is:

> **UNKNOWN outcome must not transition directly to RETRY.**

Instead:

```text
UNKNOWN
  → RECONCILE
      → COMMITTED → COMPLETE
      → ABSENT    → RETRY_ALLOWED
      → UNKNOWN   → KEEP_RECONCILING / ESCALATE
```

The final `UNKNOWN → UNKNOWN` branch is a protocol requirement suggested by the model but was not exercised in this v0.3 run.

## Why this matters for agent systems

Agent frameworks make it easy to call tools repeatedly across turns. That is useful, but it means correctness cannot be reduced to "the tool returned an error." A transport error can occur before a state change, after a state change, or while the system is unable to prove which occurred.

For actions with durable consequences — payments, orders, deployments, messages, access changes, resource creation — a trustworthy agent needs an explicit recovery protocol tied to durable state.

The most robust design may combine:

- an idempotency key at the side-effecting service;
- durable operation identifiers;
- a reconciliation/read-after-error path;
- a state machine where `UNKNOWN` is a first-class state;
- evidence showing why retry was permitted or blocked.

## Interpretation boundary

This report verifies an **application-level recovery pattern executed through one pinned SDK revision**. It does **not** prove that:

- OpenAI Agents SDK automatically enforces idempotency;
- every SDK tool should use this exact policy;
- a real payment processor behaves like the synthetic ledger;
- a timeout always means the result is unknown;
- reconciliation itself is always reliable;
- arbitrary applications built with the SDK are safe.

This is not a vulnerability claim and not a safety certification.

## Reproducibility

Harness:

`benchmarks/openai-agents-recovery-v0.3/run_recovery.py`

Workflow:

`.github/workflows/benchmark-openai-agents-recovery.yml`

Machine-readable result:

`reports/verified/003-openai-agents-recovery/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31454264702`

## Verdict

**The benchmark reproduced a duplicate side effect under blind retry and eliminated that duplicate when the application reconciled durable state before deciding whether retry was legal.**

The rule is simple enough to remember and important enough to formalize:

# **reconcile before retry**

---

**RESONANCE Verified Report #003**  
**Status:** Reproducible application recovery run  
**Recovery protocol:** 10/10  
**Naive duplicate reproduced:** Yes  
**Safe after-commit final effects:** 1  
**Safe before-commit final effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
