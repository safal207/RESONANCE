# RESONANCE Verified Report #005

# OpenAI Agents SDK — Conflicting Evidence

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Conflicting Evidence v0.5  
**Executed:** 2026-08-11T04:00:04Z  
**GitHub Actions run:** `31457067152`  
**Evidence artifact:** `resonance-openai-agents-conflicting-evidence-v0.5`  
**Artifact digest:** `sha256:bfa1aafdfbb21363176c0ed33f1b67cfd699edf54a924239a55c1f5fcd8dba17`

## Result

# **10 / 10 — Conflicting evidence**

**Classification: conflict-preserving evidence protocol passes**

This run asks a harder question than “is the outcome known?” Two sources can both return concrete answers and still disagree.

The benchmark created one synthetic committed side effect, lost the response, then exposed two evidence sources:

```text
primary → COMMITTED
replica → ABSENT
```

The unsafe policy collapsed the disagreement into permission to retry and produced a duplicate effect. The safe policies either preserved `CONFLICT`, applied explicit authority/freshness rules, or refreshed the stale source until the evidence converged.

## Comparative result

| Scenario | Evidence | Final effects |
|---|---|---:|
| Unsafe conflict → retry | fresh primary `COMMITTED` + fresh replica `ABSENT` → retry | **2** |
| Safe unresolved conflict | fresh primary `COMMITTED` + fresh replica `ABSENT` → `CONFLICT` | **1** |
| Safe authority/freshness resolution | stale replica `ABSENT` + fresh primary `COMMITTED` → complete | **1** |
| Safe refresh to convergence | stale replica `ABSENT` → refreshed replica `COMMITTED` | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe CONFLICT → RETRY hazard reproduced | PASS | 2/2 |
| Fresh disagreement preserved as CONFLICT | PASS | 2/2 |
| Authority/freshness blocks stale-ABSENT retry | PASS | 2/2 |
| Refresh resolves conflict without retry | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — collapsing conflict creates a duplicate

The first synthetic charge committed and then lost its response. The benchmark queried both evidence sources.

Observed:

```text
charge #1 → COMMIT
primary → COMMITTED / fresh
replica → ABSENT / fresh
unsafe decision → RETRY
charge #2 → COMMIT
```

Final effect count: **2**.

The failure is not missing evidence. It is **incorrect arbitration of conflicting evidence**.

## Scenario 2 — disagreement becomes a first-class state

The same fresh disagreement was observed, but the safe trajectory did not choose the convenient answer.

```text
COMMITTED + ABSENT
       ↓
    CONFLICT
       ↓
retry blocked
resolve authority / refresh / escalate
```

Final effect count: **1**.

## Scenario 3 — freshness and authority are evidence semantics

A secondary replica returned `ABSENT`, but the snapshot was explicitly stale. The primary durable source returned fresh `COMMITTED`.

The safe protocol treated the primary durable record as stronger evidence and did not retry.

Final effect count: **1**.

This benchmark does not claim that “primary always wins” in every system. The requirement is that **source authority must be defined by the application domain rather than improvised after a conflict appears**.

## Scenario 4 — refresh can resolve disagreement

The primary returned fresh `COMMITTED`; the replica initially returned stale `ABSENT`. A second replica read refreshed to `COMMITTED`.

```text
primary → COMMITTED / fresh
replica → ABSENT / stale
          ↓ refresh
replica → COMMITTED / fresh
          ↓
       COMPLETE
```

No retry was issued. Final effect count: **1**.

## The evidence invariant

# **CONFLICT must not authorize retry.**

A useful evidence record needs more than a value:

```text
Evidence = value + source + authority + freshness + provenance
```

A safe decision can then distinguish:

```text
ABSENT from replica ≠ ABSENT from source of record
STALE ABSENT        ≠ fresh ABSENT
DISAGREEMENT        ≠ permission to choose the cheapest transition
```

Legal next moves from `CONFLICT` can include:

- refresh one or more sources;
- consult the domain-defined source of record;
- compare timestamps/version vectors/operation IDs;
- escalate when authority is unresolved;
- use a separately proven idempotent operation where repetition is safe.

The dangerous shortcut is:

```text
CONFLICT → RETRY
```

without an explicit evidence-resolution rule.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop executed all four deterministic trajectories using the upstream `FakeModel`.

That boundary matters. The SDK did not automatically arbitrate evidence sources, and this report does not claim it should. The measured property is an **application-level evidence protocol** built on top of the framework.

## Why this matters

Agent systems increasingly combine databases, caches, APIs, queues, replicas, observability systems and human approvals. Those sources can disagree because of replication lag, stale caches, partial failures, differing authority, race conditions or incomplete provenance.

A trustworthy agent should therefore preserve not only `UNKNOWN`, but also `CONFLICT`.

```text
UNKNOWN  = insufficient evidence
CONFLICT = evidence exists but disagrees
```

They are different states and can require different recovery paths.

## Interpretation boundary

This report does **not** verify:

- a real payment processor or database cluster;
- production replica consistency;
- arbitrary OpenAI Agents SDK applications;
- live-model reasoning quality;
- automatic SDK evidence arbitration;
- universal source-authority rules;
- safety of applications built with the SDK.

No production API key, live model, real credential or external side-effecting service was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-conflicting-evidence-v0.5/run_conflicting_evidence.py`

Workflow:

`.github/workflows/benchmark-openai-agents-conflicting-evidence.yml`

Machine-readable result:

`reports/verified/005-openai-agents-conflicting-evidence/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31457067152`

## Verdict

**The benchmark reproduced a duplicate side effect when conflicting evidence was collapsed into permission to retry. Preserving CONFLICT — and resolving it through explicit authority/freshness rules or refreshed evidence — prevented the duplicate in every safe trajectory.**

The RESONANCE recovery rule now becomes:

# **preserve UNKNOWN; preserve CONFLICT; act only on resolved evidence**

---

**RESONANCE Verified Report #005**  
**Status:** Reproducible conflicting-evidence run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Safe conflict final effects:** 1  
**Authority/freshness final effects:** 1  
**Refresh convergence final effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
