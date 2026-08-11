# TTP v1.0 — Clock Authority / Skew Rule

**Status:** Canonical TTP v1.0 extension  
**Evidence:** RESONANCE Verified Report #018  
**Scope:** time-based safety decisions when distributed nodes disagree about expiry

## Purpose

A durable and unexpired safety record can still be interpreted differently by nodes with different clocks. TTP therefore treats decision time as evidence with an authority and uncertainty model.

## Invariants

```text
I31 SAME RETENTION RECORD + DIFFERENT CLOCKS CAN YIELD DIFFERENT SAFETY DECISIONS
I32 TIME-BASED SAFETY REQUIRES A DECLARED CLOCK AUTHORITY OR SKEW BOUND
I33 EXPIRY INSIDE CLOCK-UNCERTAINTY WINDOW ≠ SAFE REPLAY PERMISSION
I34 CLOCK DISAGREEMENT IS EVIDENCE CONFLICT
```

## Reference rule

```text
TIME-BASED EXECUTION PRECONDITION
        ↓
ESTABLISH CLOCK BASIS
   ├─ declared decision-time authority
   │      ↓
   │   evaluate retention against that time
   │
   └─ bounded uncertainty
          ↓
      compute [earliest_possible_now, latest_possible_now]
          ↓
      does expiry lie inside the interval?
          ├─ no  → ACTIVE or EXPIRED may be decided
          └─ yes → TIME_UNKNOWN
                     ↓
                  RECONCILE AUTHORITATIVE EFFECT STATE
                     ├─ COMMITTED → COMPLETE / NO REPLAY
                     ├─ ABSENT    → fresh replay decision
                     └─ UNKNOWN   → HOLD / RECONCILE AGAIN / ESCALATE
        ↓
PROVE
```

## Required evidence

```text
logical_effect_id
idempotency_key
created_at
expires_at
node_local_time(s)
clock_authority_identity when used
authority_time when used
skew / uncertainty bound when used
computed temporal state
transport outcome
remote authoritative status
final effect count
```

## Conformance requirement

An adapter that makes consequential replay decisions from expiry timestamps SHOULD declare what clock is authoritative for that decision or declare a bounded uncertainty model.

A node-local clock MUST NOT silently become replay authority merely because it is the worker currently executing recovery.

When the allowed temporal uncertainty crosses the expiry boundary, the temporal state SHOULD remain `TIME_UNKNOWN` until authoritative effect reconciliation or stronger time evidence resolves it.

## Evidence from Verified #018

One 60-second record was evaluated at two local times:

```text
expires_at = T0 + 60
Node A     = T0 + 50 → ACTIVE
Node B     = T0 + 70 → EXPIRED
```

Allowing Node B's local time to authorize same-key replay produced two effects. Evaluating replay at a declared authority time `T0 + 55` returned `DEDUPLICATED` and preserved one effect. A ±20-second uncertainty interval crossing the expiry boundary produced `TIME_UNKNOWN`; authoritative reconciliation found `COMMITTED`, so no second POST was made.

## Relationship to #016–#018

```text
#016 → memory durability
#017 → memory retention validity
#018 → time authority / uncertainty for that validity decision
```

Therefore:

```text
TEMPORAL TRUST MEMORY =
  durable state
+ retention policy
+ clock authority / skew model
+ recovery semantics
+ evidence
```

This extension does not prescribe NTP/PTP implementation, production skew limits or universal idempotency TTLs.