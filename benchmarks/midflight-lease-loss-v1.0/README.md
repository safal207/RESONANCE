# RESONANCE Benchmark — Mid-flight Lease Loss / Long-Running Action v1.0

This benchmark tests whether execution authority remains valid when a worker starts a long-running action under one lease epoch but loses ownership before the irreversible commit.

## Core question

```text
Worker A acquires lease / fence N
→ start authorization succeeds
→ A begins long-running work
→ lease expires
→ Worker B takes over / fence N+1
→ B commits
→ A finishes old work
→ can A still commit using the old start authorization?
```

## Unsafe path

A checks authority only at action start. After B takes over and commits, A finishes using the stale start proof. An external resource that does not enforce fencing accepts both effects.

Expected result: `effect_count = 2`.

## Safe path A — commit-time revalidation

Before the consequential mutation, A re-checks the exact ownership epoch used at start:

```text
resource_id
+ owner
+ fencing token
+ lease version
+ lease validity at commit time
```

After B has taken over, the old A epoch no longer matches, so no external call is made.

## Safe path B — resource-side fencing

Even if A skips commit-time coordinator revalidation, it must present its fencing token to the protected resource. Once B's higher token has been accepted, A's lower token is rejected with `HTTP 409 / fenced_out`.

## Control

A long-running action that starts and finishes before expiry is still allowed to commit normally. The protocol does not ban long work; it requires authority to remain valid at the irreversible boundary.

## Invariants

1. **AUTHORIZED AT START ≠ AUTHORIZED AT COMMIT.**
2. **LONG-RUNNING CONSEQUENTIAL WORK MUST REVALIDATE OR PRESENT A CURRENT FENCING EPOCH AT THE COMMIT BOUNDARY.**
3. **LEASE LOSS WHILE WORK IS IN FLIGHT IS AN AUTHORITY-LIFECYCLE TRANSITION.**
4. **RESOURCE-SIDE FENCING IS THE FINAL GUARD AGAINST A STALE COMPLETION.**

## Interpretation boundary

This is a deterministic local benchmark using PostgreSQL as the lease coordinator and a separate Dockerized HTTP service with a persistent SQLite effect ledger as the protected resource. Logical time is injected by the harness. It does not test Kubernetes, etcd, a cloud lease service, real network partition detection, arbitrary exactly-once execution, or production safety certification.
