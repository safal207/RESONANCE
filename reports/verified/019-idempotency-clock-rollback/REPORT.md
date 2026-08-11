# RESONANCE Verified Report #019

# Clock Rollback / Temporal ABA

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Clock Rollback / Temporal ABA v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP service with persistent SQLite effect/idempotency ledger  
**Clock model:** deterministic wall-clock rollback + monotonic temporal epoch / watermark controls  
**GitHub Actions run:** `31470122034`  
**Evidence artifact:** `resonance-idempotency-clock-rollback-v1.0`  
**Artifact ID:** `9093020263`  
**Artifact digest:** `sha256:6132fb3a357952eedcd54aac4d15b48cd429684f9630ed152f3c3b65674b9dce`

## Result

# **10 / 10 — Temporal ABA fencing / monotonic-time protocol passes**

Verified #018 showed that different clocks can disagree about whether the same retention record is active or expired. Report #019 asks the next question:

> What if time moves past expiry and then the wall clock moves backward, making the old value look valid again after history has already advanced?

The benchmark separates **clock value** from **temporal history**.

## Temporal ABA visibility

One durable record was evaluated in this sequence:

```text
expires_at = 7,000,060

7,000,050 → ACTIVE
7,000,070 → EXPIRED
7,000,050 → ACTIVE
```

Throughout the sequence the underlying effect remained:

```text
status = COMMITTED
effect_count = 1
```

The same wall-clock value can therefore reappear while the execution history is no longer the same.

# **SAME WALL-CLOCK VALUE ≠ SAME TEMPORAL STATE**

## Unsafe: expiry cleanup + rollback resurrects replay permission

The unsafe case created one remote effect and then dropped the HTTP acknowledgement:

```text
T0 = 8,000,000
expires_at = 8,000,060
ACK_UNKNOWN
effect_count = 1
```

At `8,000,070`, the record was expired. Maintenance then removed the expired dedupe record and advanced a monotonic temporal epoch:

```text
removed_records = 1
temporal_epoch = 1 → 2
```

The wall clock then rolled back to `8,000,050`, which is numerically before the original expiry:

```text
rollback_time < original_expires_at
→ local wall-clock rule says old TTL window is safe again
```

But the dedupe record had already been garbage-collected in a later temporal epoch. An un-fenced POST using the **same Idempotency-Key** was therefore accepted as a new effect:

```text
POST #2
same key
logical_time = 8,000,050
current temporal_epoch = 2
→ delivery = APPLIED
→ effect_count = 2
→ status = CONFLICT
```

The duplicate was not caused by a new logical identity. It was caused by allowing a reversible wall-clock scalar to resurrect permission after an irreversible retention-state transition.

## Safe A: monotonic temporal epoch / fencing token

The safe fencing scenario bound the recovery decision to the temporal epoch observed before expiry cleanup:

```text
bound temporal_epoch = 2
```

Cleanup then removed the expired record and advanced the epoch:

```text
temporal_epoch = 2 → 3
```

After the wall clock rolled back, a second same-key POST carried:

```text
expected_temporal_epoch = 2
current_temporal_epoch  = 3
```

The HTTP boundary rejected it:

```text
HTTP 409
error = temporal_epoch_mismatch
delivery = fenced_out
effect_count = 1
```

Recovery then reconciled authoritative remote state:

```text
status = COMMITTED
effect_count = 1
```

The old time value could return. The old execution epoch could not.

## Safe B: monotonic time watermark

A second safe control did not require a server fencing token. The recovery worker retained the largest time already observed in the trajectory:

```text
forward_time = 10,000,070
wall clock rolls back to 10,000,050

monotonic_watermark = 10,000,070
effective_now = max(wall_clock_now, monotonic_watermark)
              = 10,000,070
```

The idempotency record therefore remained `EXPIRED` rather than re-entering `ACTIVE`.

Recovery reconciled remote state:

```text
status = COMMITTED
effect_count = 1
second_post_made = false
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Same record visibly re-enters ACTIVE after wall-clock rollback | PASS | 2/2 |
| Expiry cleanup + rollback reproduces same-key duplicate | PASS | 2/2 |
| Monotonic temporal epoch fences stale post-rollback retry | PASS | 2/2 |
| Monotonic time watermark prevents EXPIRED → ACTIVE re-entry | PASS | 2/2 |
| Final TTP Temporal ABA invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **SAME WALL-CLOCK VALUE ≠ SAME TEMPORAL STATE AFTER HISTORY ADVANCES**

# **EXPIRED / RETIRED SAFETY EPOCH MUST NOT BE RESURRECTED BY CLOCK ROLLBACK**

# **TIME-BASED EXECUTION AUTHORIZATION SHOULD BIND TO A MONOTONIC EPOCH OR MONOTONIC TIME BASIS**

# **CLOCK ROLLBACK AFTER IRREVERSIBLE TEMPORAL TRANSITION IS EVIDENCE CONFLICT**

## TTP Temporal ABA rule

```text
TIME-BASED DECISION
      ↓
OBSERVE wall-clock time
      +
BIND monotonic temporal epoch / watermark
      ↓
HISTORY ADVANCES
(expiry / cleanup / revocation / lease rotation)
      ↓
wall clock moves backward?
   ├─ no  → normal time evaluation
   └─ yes → do not resurrect old permission
              ↓
        compare temporal epoch / watermark
          ├─ stale → FENCE
          └─ uncertain → RECONCILE
              ↓
            PROVE
```

## Relationship to #016–#019

```text
#016 → did safety memory survive failure?
#017 → is that memory still valid at recovery time?
#018 → whose time decides validity, and with what skew?
#019 → can a reversible clock value resurrect an already-retired temporal state?
```

This yields:

```text
TEMPORAL TRUST MEMORY =
  durable memory
+ retention validity
+ clock authority / skew
+ monotonic epoch / watermark
+ recovery semantics
+ evidence
```

## Interpretation boundary

The benchmark uses deterministic logical wall-clock values across a real local HTTP boundary. Expiry cleanup and temporal-epoch transitions are real mutations in the benchmark HTTP service's persistent SQLite state; PostgreSQL holds the local business/outbox state.

It does **not** test or certify:

- operating-system clock rollback behavior;
- NTP, PTP, chrony or leap-second handling;
- real hardware-clock drift;
- distributed consensus time;
- a universal fencing-token design;
- production provider idempotency semantics;
- multi-region temporal correctness;
- exactly-once delivery in arbitrary distributed systems;
- arbitrary agent safety.

The 60-second TTL and logical timestamps are benchmark parameters, not production recommendations.

## Reproducibility

Benchmark specification:

`benchmarks/idempotency-clock-rollback-v1.0/README.md`

External HTTP service:

`benchmarks/idempotency-clock-rollback-v1.0/external_service.py`

Harness:

`benchmarks/idempotency-clock-rollback-v1.0/run_clock_rollback.py`

Workflow:

`.github/workflows/benchmark-idempotency-clock-rollback.yml`

Machine-readable result:

`reports/verified/019-idempotency-clock-rollback/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31470122034`

## Verdict

**The same idempotency record visibly transitioned ACTIVE → EXPIRED → ACTIVE when a reversible wall-clock value moved backward. After expiry cleanup advanced the temporal epoch, an un-fenced same-key replay at the rolled-back time produced a second remote effect. Binding execution to a monotonic temporal epoch rejected the stale retry with HTTP 409, while a monotonic time watermark preserved EXPIRED and reconciled without a second POST.**

---

**RESONANCE Verified Report #019**  
**Status:** Reproducible deterministic clock-rollback run  
**Score:** 10/10  
**Unsafe remote effects:** 2  
**Temporal-epoch fenced effects:** 1  
**Monotonic-watermark effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
