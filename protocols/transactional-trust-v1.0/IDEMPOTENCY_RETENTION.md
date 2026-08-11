# TTP v1.0 — Idempotency Retention Rule

**Status:** Canonical TTP v1.0 extension  
**Evidence:** RESONANCE Verified Report #017  
**Scope:** delayed recovery and replay after idempotency/deduplication state expiry

## Purpose

A safety record can be durable and still become invalid before recovery needs it. TTP therefore treats idempotency retention as a time-bounded execution precondition rather than a storage detail.

## Invariants

```text
I27 DEDUPE RETENTION WINDOW MUST COVER THE RECOVERY / REPLAY WINDOW IT PROTECTS
I28 EXPIRED DEDUPE MEMORY ≠ EFFECT ABSENT
I29 AFTER IDEMPOTENCY EXPIRY, RECONCILE AUTHORITATIVE EFFECT STATE BEFORE CONSEQUENTIAL REPLAY
I30 TIME + MEMORY + RECOVERY POLICY FORM ONE SAFETY BOUNDARY
```

## Reference rule

```text
REMOTE EFFECT
   ↓
ACK_UNKNOWN
   ↓
RECOVERY DELAY
   ↓
CHECK IDEMPOTENCY RETENTION
   ├─ record active
   │      ↓
   │   same-key redelivery may be deduplicated under the declared contract
   │
   └─ record expired / unavailable
          ↓
      RECONCILE AUTHORITATIVE EFFECT STATE
          ├─ COMMITTED → COMPLETE / NO REPLAY
          ├─ ABSENT    → fresh replay decision
          └─ UNKNOWN   → HOLD / RECONCILE AGAIN / ESCALATE
   ↓
PROVE
```

## Required evidence when retention matters

```text
logical_effect_id
idempotency_key
idempotency_created_at
idempotency_expires_at
recovery_or_retry_time
retention_policy / TTL
transport outcome
remote authoritative status
final effect count
```

## Conformance requirement

When an adapter relies on idempotency memory to absorb replay, it SHOULD declare the retention window that gives that guarantee meaning. A retry arriving outside that window MUST NOT assume the old key still protects the effect.

If the key is expired or its retention state cannot be established, recovery SHOULD reconcile authoritative effect state before another consequential request.

## Evidence from Verified #017

The benchmark fixed a 120-second delayed recovery window and varied only the idempotency retention period:

```text
TTL 60s  < recovery 120s → record expired → same key APPLIED → 2 effects
TTL 300s > recovery 120s → record active  → same key DEDUPLICATED → 1 effect
TTL 60s expired + authoritative reconcile → COMMITTED → no second POST → 1 effect
```

The benchmark uses deterministic logical time supplied across a real local HTTP boundary. The numeric values are test parameters, not production recommendations.

## Relationship to Verified #016

```text
#016 asks: did safety memory survive the failure?
#017 asks: is surviving safety memory still valid at recovery time?
```

Therefore:

```text
DURABLE MEMORY ≠ MEMORY VALID FOR THIS DECISION TIME
```

This extension is part of the RESONANCE TTP v1.0 research line and does not claim exactly-once delivery or universal production retention semantics.
