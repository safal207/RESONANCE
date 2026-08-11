# RESONANCE Verified Report #010

# OpenAI Agents SDK — Distributed Commit Race

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Distributed Commit Race v1.0  
**Executed:** 2026-08-11T04:48:02Z  
**GitHub Actions run:** `31459591950`  
**Evidence artifact:** `resonance-openai-agents-distributed-commit-race-v1.0`  
**Artifact digest:** `sha256:e69f4f65802ff653e7575b8e9fbaa9b6c97a83455d88a191bfe8aa8a06aaa3dc`

## Result

# **10 / 10 — Atomic state-version preconditions**

**Classification: atomic state-version precondition protocol passes**

Report #009 bound authorization to the trust state that existed when it was verified. Report #010 moves the race one step closer to the write itself: **what if two nodes both read the same valid `ABSENT / version=100` snapshot, and one commits after both checks but before the other write?**

```text
Node A read → ABSENT / version 100
Node B read → ABSENT / version 100
Node B commit → COMMITTED / version 101
Node A write using old version 100
```

If compare and write are separate, both nodes can act on a snapshot that was true when observed but false when used.

## Comparative result

| Scenario | Transition rule | Final effects |
|---|---|---:|
| Unsafe split check/write | both nodes reuse `ABSENT/version=100` without enforcement | **2** |
| Safe two-node CAS | first writer changes `100→101`; second writer fails stale precondition | **1** |
| Safe unchanged version | version remains 100 until commit | **1** |
| Safe external mutation | another node commits first; stale writer is rejected | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe split check/write duplicate reproduced | PASS | 2/2 |
| Two-node CAS allows a single winner | PASS | 2/2 |
| Losing writer gets precondition failure and rereads `COMMITTED` | PASS | 2/2 |
| Unchanged version permits progress; concurrent mutation blocks stale write | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — two correct reads can still produce a wrong result

Both synthetic nodes read:

```text
state   = ABSENT
version = 100
effects = 0
```

Node B then committed and advanced the shared version to 101. Node A nevertheless performed an unconditional write using its earlier observation.

```text
A read v100
B read v100
B write → effect #1 / v101
A write from stale v100 → effect #2 / v102
```

Final effect count: **2**.

Neither read was false. The failure came from treating a snapshot as permission after the shared state had changed.

## Scenario 2 — CAS creates one winner

Both nodes again read version 100. This time the irreversible operation required `expected_version=100` atomically with the transition.

Node B won:

```text
expected = 100
current  = 100
state    = ABSENT
allowed  = true
commit   → version 101 / effect #1
```

Node A then attempted the same conditional transition:

```text
expected = 100
current  = 101
state    = COMMITTED
allowed  = false
```

It received a precondition failure before another side effect occurred. A reread returned `COMMITTED / version=101 / effects=1`.

Final effect count: **1**.

## Scenario 3 — atomic safety must still permit progress

With no concurrent mutation, Node A read `ABSENT/version=100` and committed with `expected_version=100`. The condition still held, so the transition succeeded and advanced state to version 101.

Final effect count: **1**.

## Scenario 4 — an external writer invalidates the snapshot

Node A read version 100. Node B then committed first. When Node A attempted the transition with `expected_version=100`, current version was already 101 and state was `COMMITTED`, so the operation was rejected.

Final effect count: **1**.

## The atomic-transition invariant

# **CHECK + WRITE MUST SHARE ONE STATE PRECONDITION**

A safe path is:

```text
read state/version N
        ↓
prepare transition
        ↓
COMPARE-AND-TRANSITION(expected=N)
   ├─ N still current → commit once
   └─ state changed   → fail / reread / reconcile
```

The forbidden structure is:

```text
CHECK(state=N)
     ↓
other actor changes state
     ↓
WRITE based only on old CHECK
```

The key difference from Report #009 is that this race exists even when authorization itself does not change. **The business state being mutated can change after verification.**

## Verification becomes transaction-bound

The RESONANCE transition model now needs an explicit execution binding:

```text
Verified transition =
  actor
+ intended action
+ observed state
+ observed state version
+ authorization/trust version
+ invariant
+ atomic commit precondition
+ resulting evidence
```

Useful distinctions now include:

```text
READ WAS CORRECT       ≠ WRITE IS STILL LEGAL
CHECK PASSED           ≠ STATE IS UNCHANGED
SAME INTENT            ≠ SAME TRANSITION
TWO VALID READERS      ≠ TWO VALID WRITERS
VERSION MATCH          = EXECUTION PRECONDITION
PRECONDITION FAILURE   ≠ OPERATION FAILURE
```

A precondition failure is often a successful safety outcome: it means the system noticed that the world changed before mutation.

## Why this matters

Agent systems increasingly coordinate through shared ledgers, databases, queues, policy stores, wallets and external APIs. Multiple workers can independently make correct observations and still collide on the same irreversible transition.

This connects the RESONANCE coordinates directly:

```text
STATE
  ↕
TRANSITION
  ↕
TIME (τ)
  ↕
CAUSALITY
  ↕
VERIFICATION
  ↕
EVIDENCE
```

Verification is therefore incomplete if it proves only that the precondition was true earlier. For consequential writes, the verified state must remain bound to the mutation boundary.

## Important boundary

This benchmark uses an in-memory synthetic store and deterministic side effects. It does **not** test or certify:

- a production database transaction engine;
- linearizability across real distributed storage;
- real compare-and-swap implementations;
- distributed consensus;
- exactly-once delivery guarantees;
- payment rails or blockchain finality;
- arbitrary applications built with the SDK.

The pinned OpenAI Agents SDK tool loop executes the deterministic application protocol using upstream `FakeModel`. The SDK does not automatically impose application-level atomicity, and this report does not claim that it should.

No live model, production API key, real credential or external side-effecting service was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-distributed-commit-race-v1.0/run_distributed_commit_race.py`

Workflow:

`.github/workflows/benchmark-openai-agents-distributed-commit-race.yml`

Machine-readable result:

`reports/verified/010-openai-agents-distributed-commit-race/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31459591950`

## Verdict

**The benchmark reproduced a duplicate when two nodes acted on the same previously valid snapshot using separate check and write steps. Binding the irreversible transition atomically to the observed shared-state version produced a single winner, converted the losing write into a precondition failure, and preserved exactly one side effect.**

The RESONANCE rule now becomes:

# **verify state; version the state; bind authorization to execution; make compare + transition atomic; on conflict, reread and reconcile**

---

**RESONANCE Verified Report #010**  
**Status:** Reproducible distributed commit race run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Single CAS winner:** Yes  
**Stale writer blocked:** Yes  
**Legitimate unchanged-state commit allowed:** Yes  
**Vulnerability claim:** No  
**External safety certification:** No
