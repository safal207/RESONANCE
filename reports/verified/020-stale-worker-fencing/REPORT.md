# RESONANCE Verified Report #020

# Stale Worker Resurrection / Fencing Token Split-Brain

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Stale Worker Resurrection / Fencing Token Split-Brain v1.0  
**Coordinator:** PostgreSQL 17.6  
**Protected boundary:** Dockerized HTTP resource service with persistent SQLite state  
**GitHub Actions run:** `31474292875`  
**Evidence artifact:** `resonance-stale-worker-fencing-v1.0`  
**Artifact ID:** `9094593495`  
**Artifact digest:** `sha256:62ad23e3cf55a5742e587334098263dfb9686989923bb2f181ac12d9533689cf`

## Result

# **10 / 10 — Stale-worker fencing protocol passes**

Report #019 established that temporal history needs monotonic epochs. #020 moves that principle into distributed execution ownership.

## Scenario

```text
Worker A acquires token 1
A stalls
Worker B acquires token 2
PostgreSQL owner = B / fence = 2
B performs external effect
A wakes and tries to act with token 1
```

The coordination database correctly knew that B was current. The question was whether the protected external resource would enforce that fact.

## Unsafe: ownership state without resource-side fencing

The HTTP resource accepted both writes without comparing fencing tokens:

```text
B / fence 2 → HTTP 200 / APPLIED → effect #1
A / fence 1 → HTTP 200 / APPLIED → effect #2
```

Final remote state:

```text
effect_count = 2
status = CONFLICT
```

The stale worker did not regain ownership in PostgreSQL. It simply retained enough stale local context to perform an unprotected external mutation.

# **CURRENT OWNER IN THE COORDINATOR ≠ EXCLUSIVE EXECUTION AT AN EXTERNAL RESOURCE**

## Safe A: monotonic fencing token enforced by the protected resource

The same takeover sequence generated token 1 for A and token 2 for B. The HTTP resource persisted the largest accepted fence.

B wrote first:

```text
presented_fence = 2
→ HTTP 200
→ delivery = APPLIED
→ highest_fence = 2
→ effect_count = 1
```

A then resumed with stale token 1:

```text
presented_fence = 1
highest_fence   = 2
→ HTTP 409
→ delivery = fenced_out
→ effect_count = 1
```

The stale process could wake up. Its old authority could not.

## Safe B: fresh coordination recheck

A second safe path reread the coordinator before A made any external call:

```text
A bound token = 1
current owner = B
current fence = 2
→ stale_detected = true
→ worker_a_write_made = false
```

B then performed the fenced write and the final effect count remained one.

This is useful prevention, but it is not equivalent to resource-side fencing. A process can become stale after a recheck and before the external mutation. The protected resource is the final authority that can reject an old token at commit time.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| New owner receives strictly higher fencing token | PASS | 2/2 |
| Unfenced external resource reproduces stale-worker duplicate | PASS | 2/2 |
| External resource rejects stale fencing token | PASS | 2/2 |
| Fenced path preserves one effect | PASS | 2/2 |
| Fresh coordinator recheck stops stale worker before call | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **LEASE / OWNERSHIP CLAIM ≠ EXTERNAL EXECUTION AUTHORITY**

# **NEW OWNER MUST RECEIVE A STRICTLY MONOTONIC FENCING TOKEN**

# **THE PROTECTED RESOURCE MUST COMPARE THE FENCE AT THE MUTATION BOUNDARY**

# **STALE WORKER RESURRECTION IS AN AUTHORITY-LIFECYCLE TRANSITION, NOT JUST A LIVENESS EVENT**

## TTP stale-worker rule

```text
ACQUIRE OWNERSHIP
      ↓
receive monotonic fence N
      ↓
BIND execution to N
      ↓
worker stalls / lease expires / ownership transfers
      ↓
new owner receives N+1
      ↓
protected mutation presents fence
   ├─ fence < highest accepted → FENCE / REJECT
   └─ fence >= highest accepted → evaluate normal mutation preconditions
      ↓
RECONCILE
      ↓
PROVE
```

## External grounding

The benchmark is a RESONANCE implementation, not an etcd test. Current etcd documentation similarly distinguishes leases from mutation-order validation and notes that external resources need their own version validation; etcd revisions provide an increasing logical order that can be used for such coordination designs.

## Interpretation boundary

This benchmark does not certify etcd, ZooKeeper, Redis, Kubernetes leader election, distributed consensus, production lease durations, multi-region fencing, arbitrary exactly-once execution or arbitrary agent safety.

It uses real PostgreSQL coordination and a separate HTTP resource boundary to demonstrate one protocol invariant: stale ownership information must not remain sufficient to commit a protected effect after takeover.

## Verdict

**Worker A acquired token 1 and stalled. Worker B acquired token 2 and became the current coordinator owner. Without resource-side fencing, B and the resurrected A both committed effects, producing two effects. With monotonic fencing enforced at the HTTP mutation boundary, B committed with token 2 and A's stale token 1 was rejected with HTTP 409, preserving one effect.**

---

**RESONANCE Verified Report #020**  
**Status:** Reproducible stale-worker / split-brain run  
**Score:** 10/10  
**Unsafe effects:** 2  
**Fenced effects:** 1  
**Stale worker response:** HTTP 409 / fenced_out  
**Vulnerability claim:** No  
**External safety certification:** No
