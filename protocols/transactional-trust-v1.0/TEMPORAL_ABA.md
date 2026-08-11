# TTP v1.0 — Temporal ABA / Monotonic Time Rule

**Status:** Canonical TTP v1.0 extension  
**Evidence:** RESONANCE Verified Report #019  
**Scope:** consequential time-based decisions after wall-clock rollback or equivalent temporal re-entry

## Purpose

A wall-clock timestamp is a value, not a history. If execution has already crossed an expiry, cleanup, revocation or lease-rotation boundary, a later clock rollback must not silently resurrect the earlier permission state.

## Invariants

```text
I35 SAME WALL-CLOCK VALUE ≠ SAME TEMPORAL STATE AFTER HISTORY ADVANCES
I36 EXPIRED / RETIRED SAFETY EPOCH MUST NOT BE RESURRECTED BY CLOCK ROLLBACK
I37 TIME-BASED EXECUTION AUTHORIZATION SHOULD BIND TO A MONOTONIC EPOCH OR MONOTONIC TIME BASIS
I38 CLOCK ROLLBACK AFTER IRREVERSIBLE TEMPORAL TRANSITION IS EVIDENCE CONFLICT
```

## Reference rule

```text
TIME-BASED PRECONDITION
        ↓
OBSERVE wall-clock value
        +
BIND temporal epoch / monotonic watermark
        ↓
HISTORY ADVANCES
(expiry / cleanup / revocation / rotation)
        ↓
wall clock moves backward?
   ├─ no  → normal evaluation
   └─ yes → compare monotonic history
              ├─ stale epoch → FENCE
              ├─ monotonic watermark says already expired → preserve EXPIRED
              └─ unresolved → TIME_CONFLICT
                                  ↓
                              RECONCILE
        ↓
PROVE
```

## Required evidence

```text
logical_effect_id
idempotency_key
created_at
expires_at
wall_clock_observations
last_seen_monotonic_time / temporal watermark
temporal_epoch bound to the decision
current temporal_epoch at execution
history-changing event (cleanup / revocation / rotation)
fence result or temporal-conflict classification
remote authoritative status
final effect count
```

## Conformance requirement

An adapter that authorizes consequential execution from wall-clock predicates SHOULD preserve a monotonic history signal that cannot move backward with the wall clock.

A previously expired or retired decision MUST NOT become valid again solely because a later wall-clock observation numerically returns to an earlier value.

When execution is bound to a temporal epoch, a mismatch between the bound epoch and the current epoch SHOULD be treated as a precondition failure / fencing event, followed by fresh observation and reconciliation rather than blind replay.

## Evidence from Verified #019

The same durable retention record was observed as:

```text
T0 + 50 → ACTIVE
T0 + 70 → EXPIRED
T0 + 50 → ACTIVE
```

After expiry cleanup removed the dedupe record and advanced the benchmark temporal epoch from `1 → 2`, an un-fenced same-key POST at the rolled-back time created a second effect.

In the safe fencing case, recovery bound itself to epoch `2`; cleanup advanced the service to epoch `3`; the post-rollback retry was rejected with `HTTP 409 / temporal_epoch_mismatch / fenced_out`, preserving one effect.

A separate monotonic-watermark control retained `T0+70` as the maximum observed time. When the wall clock returned to `T0+50`, the effective decision time remained `T0+70`, so the state stayed `EXPIRED` and recovery reconciled `COMMITTED` without a second POST.

## Relationship to #016–#019

```text
#016 → memory durability
#017 → retention validity
#018 → clock authority / skew
#019 → temporal-history monotonicity / anti-resurrection
```

Therefore:

```text
TEMPORAL TRUST MEMORY =
  durable state
+ retention policy
+ clock authority / skew model
+ monotonic epoch / watermark
+ recovery semantics
+ evidence
```

This extension does not prescribe NTP/PTP behavior, operating-system clock handling, a universal fencing mechanism or production timing values.
