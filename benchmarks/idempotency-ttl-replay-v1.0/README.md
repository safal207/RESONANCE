# RESONANCE Idempotency TTL / Replay After Expiry v1.0

This benchmark extends Verified Report #016 from **restart durability** into **retention-time correctness**.

A stable idempotency key is not enough if the consumer forgets that key before a delayed recovery/replay can arrive.

## Core invariant

```text
DEDUPE RETENTION WINDOW
MUST COVER THE RECOVERY / REPLAY WINDOW
IT IS EXPECTED TO PROTECT
```

And after expiry:

```text
EXPIRED DEDUPE MEMORY != EFFECT ABSENT
```

## Topology

```text
PostgreSQL 17.6
business state + outbox
        ↓ HTTP
separate Docker service
        ↓
persistent SQLite
  effects + idempotency records
```

The HTTP service uses a deterministic logical clock supplied by the benchmark over `X-Logical-Time`. This avoids wall-clock sleeps while preserving explicit `created_at`, `expires_at`, retry-time and retention-window semantics.

## Scenarios

### 1. Unsafe short TTL

```text
T0 = 1,000,000
TTL = 60s
recovery delay = 120s

POST → remote effect commits → ACK lost
T0+120 → idempotency record expired, effect still durable
same key POST → applied again
```

Expected: two remote effects.

### 2. Safe retention window

```text
TTL = 300s
recovery delay = 120s
```

The same delayed POST remains inside the active dedupe window and must return `deduplicated` with one remote effect.

### 3. Safe reconcile after expiry

Use the short 60-second TTL again. After 120 seconds the dedupe record is expired, but recovery first queries authoritative remote operation status. If it sees `COMMITTED`, it closes the outbox without a second POST.

Expected: one remote effect.

## Score

10 points total:

- 2 — effect persists while dedupe record transitions active → expired;
- 2 — short TTL reproduces same-key duplicate after expiry;
- 2 — retention covering recovery window deduplicates delayed replay;
- 2 — authoritative reconcile after expiry prevents replay;
- 2 — final TTP time-memory-recovery invariant holds.

## Scope boundary

This is a local deterministic benchmark. It does not certify a production provider's TTL, exactly-once semantics, distributed clocks, multi-region storage, cache eviction, disaster recovery or arbitrary agent safety.
