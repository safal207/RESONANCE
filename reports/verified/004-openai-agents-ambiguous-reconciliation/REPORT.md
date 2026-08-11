# RESONANCE Verified Report #004

# OpenAI Agents SDK — Ambiguous Reconciliation

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Ambiguous Reconciliation v0.4  
**Executed:** 2026-08-11T03:27:05Z  
**GitHub Actions run:** `31455403621`  
**Evidence artifact:** `resonance-openai-agents-ambiguous-reconciliation-v0.4`  
**Artifact digest:** `sha256:f09d763fb399873236593901560eb29a7dbeec9df1dc2c244f69b2a53e66fef2`

## Result

# **10 / 10 — Ambiguous reconciliation**

**Classification: UNKNOWN-preserving recovery pattern passes**

The benchmark pushed the recovery problem one level deeper. The side effect committed and its response was lost. Then the reconciliation path itself became inconclusive through either a timeout or a stale status snapshot.

The unsafe policy collapsed that uncertainty into retry and produced a duplicate effect. The safe policies preserved `UNKNOWN`, blocked retry, and either escalated or reconciled again until fresh evidence arrived.

```text
attempt
  → timeout / outcome unknown
  → reconcile
      ├─ fresh COMMITTED → COMPLETE
      ├─ fresh ABSENT    → RETRY_ALLOWED
      └─ timeout / stale / inconclusive → UNKNOWN
                                      ↓
                           reconcile again / escalate
```

## Comparative result

| Scenario | Observed trajectory | Final effects |
|---|---|---:|
| Unsafe retry after ambiguous reconciliation | `commit → response lost → reconcile timeout → retry → commit` | **2** |
| Safe hold after reconciliation timeout | `commit → response lost → reconcile timeout → HOLD UNKNOWN` | **1** |
| Safe stale-status handling | `commit → response lost → stale UNKNOWN → HOLD UNKNOWN` | **1** |
| Safe eventual resolution | `commit → response lost → reconcile timeout → fresh committed → stop` | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe UNKNOWN → RETRY hazard reproduced | PASS | 2/2 |
| UNKNOWN preserved after reconciliation timeout | PASS | 2/2 |
| Stale UNKNOWN not treated as ABSENT | PASS | 2/2 |
| Repeat reconciliation resolves without retry | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — unsafe UNKNOWN → RETRY

The first synthetic charge committed durably, then lost its response. The next status check also timed out. The unsafe trajectory interpreted the still-unknown outcome as permission to retry.

Observed evidence:

```text
charge_attempt #1
commit #1
response lost
reconcile → UNKNOWN (status timeout)
charge_attempt #2
commit #2
```

Final effect count: **2**.

This is the exact failure the benchmark is designed to expose: an inconclusive reconciliation result is not evidence that the original effect is absent.

## Scenario 2 — preserve UNKNOWN after status timeout

The same initial commit and lost response occurred. Reconciliation timed out again, but the safe trajectory did not issue another side-effecting call.

Observed evidence:

```text
charge_attempt #1
commit #1
response lost
reconcile → UNKNOWN
STOP / ESCALATE
```

Final effect count: **1**.  
Final attempt count: **1**.

## Scenario 3 — stale UNKNOWN is not ABSENT

A stale status snapshot returned `status=unknown` with `freshness=stale`. The safe path refused to reinterpret stale uncertainty as a negative answer.

Observed evidence:

```text
commit #1
response lost
reconcile → UNKNOWN (stale snapshot)
retry blocked
```

Final effect count: **1**.

## Scenario 4 — uncertainty can resolve later

The first reconciliation timed out. A second reconciliation returned fresh durable state showing `committed`. No retry was issued.

Observed evidence:

```text
commit #1
response lost
reconcile #1 → UNKNOWN
reconcile #2 → COMMITTED
COMPLETE
```

Final effect count: **1**.  
Reconciliation calls: **2**.

## The invariant

# **UNKNOWN reconciliation outcome must not authorize retry.**

A timeout, stale read, unavailable status endpoint or otherwise inconclusive reconciliation result must preserve `UNKNOWN`.

Legal next transitions include:

- reconcile again;
- escalate to a human or policy layer;
- use a separately proven idempotent retry path;
- execute a domain-specific compensation protocol when justified.

The illegal shortcut is:

```text
UNKNOWN → RETRY
```

unless independent evidence proves the action is safe to repeat.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop faithfully executed both the unsafe and safe deterministic trajectories through the upstream `FakeModel`.

That is the important boundary of the result. This report verifies an **application-level protocol for preserving uncertainty**. It does not claim that OpenAI Agents SDK automatically prevents unsafe retries or enforces this state machine by default.

## Why this matters

Real agent systems often operate across networks, payment processors, queues, deployment systems, SaaS APIs and eventually consistent databases. A recovery read can fail for the same reasons as the original action, or it can return stale evidence.

A trustworthy system therefore needs to distinguish at least:

```text
ABSENT      ≠ UNKNOWN
STALE       ≠ ABSENT
TIMEOUT     ≠ ABSENT
NO EVIDENCE ≠ NO EFFECT
```

Preserving those distinctions is a small state-machine decision with large consequences.

## Interpretation boundary

This report does **not** verify:

- a real payment processor or financial rail;
- arbitrary SDK applications;
- live-model reasoning quality;
- production network retries;
- correctness of every reconciliation source;
- service-side idempotency guarantees;
- safety of compensation logic;
- automatic enforcement by OpenAI Agents SDK.

No production API key, live model, external service or real credential was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-ambiguous-reconciliation-v0.4/run_ambiguous_reconciliation.py`

Workflow:

`.github/workflows/benchmark-openai-agents-ambiguous-reconciliation.yml`

Machine-readable result:

`reports/verified/004-openai-agents-ambiguous-reconciliation/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31455403621`

## Verdict

**The benchmark reproduced a duplicate side effect when an inconclusive reconciliation result was treated as permission to retry. Preserving UNKNOWN prevented the duplicate in every safe trajectory.**

The recovery rule now becomes stricter:

# **reconcile before retry — and preserve UNKNOWN when reconciliation is inconclusive**

---

**RESONANCE Verified Report #004**  
**Status:** Reproducible ambiguous-reconciliation run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Safe timeout final effects:** 1  
**Safe stale final effects:** 1  
**Eventual fresh reconciliation:** COMMITTED, no retry  
**Vulnerability claim:** No  
**External safety certification:** No
