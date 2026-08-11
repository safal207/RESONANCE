# RESONANCE Idempotency Clock Skew / Expiry Disagreement v1.0

Verified Report #018 tests the next TTP time-memory boundary after #017: two nodes can evaluate the same durable idempotency record at different local times and reach opposite safety decisions.

## Core race

```text
created_at = T0
expires_at = T0 + 60s

Node A local time = T0 + 50s → ACTIVE
Node B local time = T0 + 70s → EXPIRED
```

If replay authority trusts the caller-local clock, Node B can reuse the same stable idempotency key after an ambiguous acknowledgement and create a second durable effect while Node A would still classify the protection record as active.

## Safe models

1. **Declared clock authority** — replay evaluation uses one authoritative decision time rather than requester-local clocks.
2. **Skew guard** — when the allowed clock-uncertainty interval crosses the expiry boundary, the temporal state is `TIME_UNKNOWN`; recovery reconciles authoritative effect state instead of replaying.

## Expected scenarios

- unsafe node-clock disagreement reproduces ACTIVE vs EXPIRED on one record and a duplicate effect;
- authoritative clock keeps the same delayed replay inside the active retention window and deduplicates it;
- bounded-skew policy detects an expiry boundary inside the uncertainty interval and reconciles to `COMMITTED` without another POST.

## Invariants

```text
SAME RETENTION RECORD + DIFFERENT CLOCKS CAN YIELD DIFFERENT SAFETY DECISIONS
TIME-BASED SAFETY REQUIRES A DECLARED CLOCK AUTHORITY OR SKEW BOUND
EXPIRY INSIDE CLOCK-UNCERTAINTY WINDOW ≠ SAFE REPLAY PERMISSION
CLOCK DISAGREEMENT IS EVIDENCE CONFLICT
```

The benchmark uses deterministic logical epochs over a real local HTTP boundary. Numeric skew/TTL values are test parameters, not production recommendations.