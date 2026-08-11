# TTP v1.0 — Stale Worker / Fencing Rule

**Status:** Canonical TTP v1.0 extension  
**Evidence:** RESONANCE Verified Report #020  
**Scope:** distributed ownership transfer and stale-worker resurrection

## Invariants

```text
I39 LEASE / OWNERSHIP CLAIM ≠ EXTERNAL EXECUTION AUTHORITY
I40 NEW OWNER MUST RECEIVE A STRICTLY MONOTONIC FENCING TOKEN
I41 PROTECTED RESOURCE MUST COMPARE THE FENCE AT THE MUTATION BOUNDARY
I42 STALE WORKER RESURRECTION IS AN AUTHORITY-LIFECYCLE TRANSITION
```

## Reference rule

```text
ACQUIRE
  ↓
receive fence N
  ↓
BIND intended mutation to N
  ↓
worker stalls / lease expires / ownership transfers
  ↓
new owner receives N+1
  ↓
MUTATE PROTECTED RESOURCE
  ↓
resource compares presented fence against highest accepted fence
  ├─ stale → FENCED_OUT / no mutation
  └─ current/newer → evaluate ordinary mutation preconditions
  ↓
RECONCILE
  ↓
PROVE
```

## Why recheck alone is not enough

A worker can reread the coordinator and still become stale before the external mutation. A fresh coordinator check is useful prevention, but the protected resource is the final place that can reject an old ownership epoch at commit time.

## Required evidence

- resource identity
- worker identity
- ownership source
- bound fencing token
- current coordinator owner/token when observed
- highest accepted fence at the protected resource
- mutation response
- final effect count
- reconciliation result

## Evidence from Verified #020

Worker A acquired token 1 and stalled. Worker B acquired token 2 and became current owner. Without external fencing, B and the resurrected A both wrote and produced two effects. With fencing enabled, B's token 2 committed and A's token 1 returned HTTP 409 `fenced_out`, leaving one effect.

## Scope boundary

This extension defines protocol semantics, not a universal lease implementation. It does not prescribe etcd, ZooKeeper, Kubernetes, Redis, lock TTLs, consensus algorithms or a production fencing-token storage design.