# RESONANCE Clock Rollback / Temporal ABA v1.0

This benchmark extends the TTP time/memory line through a rollback hazard:

```text
ACTIVE → EXPIRED → wall clock rolls backward → ACTIVE again?
```

The experiment uses:

- PostgreSQL 17.6 for local business/outbox state;
- a separate Dockerized HTTP effect service;
- persistent SQLite for remote effect and idempotency state;
- deterministic logical wall-clock values carried over HTTP;
- a monotonic temporal epoch advanced by expiry cleanup;
- a client-side monotonic time watermark as an independent safe control.

## Why this matters

A timestamp is a value. A history is not.

If a consequential decision says “this protection is active because local time is before `expires_at`”, a later clock rollback can make an already-crossed expiry boundary look un-crossed. If cleanup, revocation, lease rotation or another irreversible temporal transition already occurred, the old wall-clock value does not restore the old state.

## Scenarios

### 1. Temporal ABA visibility

One durable idempotency record is evaluated in this sequence:

```text
T0 + 50 → ACTIVE
T0 + 70 → EXPIRED
T0 + 50 → ACTIVE
```

The effect remains `COMMITTED / effect_count=1`. Only the reversible wall-clock interpretation changes.

### 2. Unsafe expiry cleanup + rollback

```text
remote effect committed
→ ACK_UNKNOWN
→ record expires
→ GC removes expired record
→ temporal epoch increments N → N+1
→ wall clock rolls back before original expires_at
→ caller treats old TTL window as safe replay territory
→ same Idempotency-Key POST without temporal fence
→ remote service no longer has dedupe record
→ second effect
```

Expected final result: `effect_count=2 / CONFLICT`.

### 3. Safe monotonic temporal epoch

The retry is bound to the temporal epoch observed before cleanup. GC advances the service epoch. A post-rollback request carrying the stale expected epoch is rejected with `409 / fenced_out`; recovery then reconciles the already committed effect.

Expected final result: one effect.

### 4. Safe monotonic time watermark

The recovery worker remembers the maximum time already observed for the decision trajectory:

```text
max_seen_time = T0 + 70
wall clock rolls back to T0 + 50

effective_now = max(max_seen_time, wall_clock_now)
              = T0 + 70
```

The temporal state therefore remains `EXPIRED`; recovery reconciles remote `COMMITTED` and does not issue a second POST.

Expected final result: one effect.

## Score

10 points total:

- temporal ABA visibility reproduced — 2;
- expiry cleanup + rollback duplicate reproduced — 2;
- monotonic temporal epoch fences stale replay — 2;
- monotonic time watermark prevents expired→active re-entry — 2;
- final one-effect invariant preserved by both safe controls — 2.

## Boundaries

This is a deterministic protocol experiment across real local PostgreSQL, Docker and HTTP boundaries. It does not test OS clock rollback, NTP/PTP/chrony, leap seconds, VM clock behavior, multi-region clock synchronization, arbitrary fencing systems or universal exactly-once delivery.

The benchmark values are test parameters, not production timing recommendations.
