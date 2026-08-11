# RESONANCE — Stale Worker Resurrection / Fencing Token Split-Brain v1.0

Purpose: test whether distributed ownership remains safe when an old worker resumes after a newer worker has taken over.

## Topology

- PostgreSQL 17.6 stores the coordination owner and monotonically increasing fencing token.
- Two logical workers, A and B, acquire the same resource sequentially.
- A is treated as stalled after acquiring token N.
- B acquires token N+1 and becomes the current owner.
- A then resumes and tries to mutate an external HTTP resource.

## Unsafe control

The external resource accepts writes based only on caller intent. B writes first and A later writes with its stale ownership context. Result: two effects.

## Safe control

Every mutation carries the fencing token. The external resource persists the largest accepted token for the protected resource and rejects any lower token with HTTP 409.

Expected trajectory:

```text
A acquires N
A stalls
B acquires N+1
B writes with N+1 → APPLIED
A resumes with N → FENCED_OUT
final effect count = 1
```

## Core invariant

**LEASE / OWNERSHIP CLAIM ≠ EXECUTION AUTHORITY UNLESS THE PROTECTED RESOURCE ENFORCES A MONOTONIC FENCE.**

## Scope boundary

This benchmark uses a real PostgreSQL coordination table and a separate Dockerized HTTP resource service with persistent SQLite state. It is not an etcd, ZooKeeper, NTP, consensus, or production distributed-lock certification.