# RESONANCE Verified Report #018

# Clock Skew / Expiry Disagreement

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Idempotency Clock Skew / Expiry Disagreement v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP service with persistent SQLite effect/idempotency ledger  
**Clock model:** deterministic node-local logical epochs + declared authoritative clock / skew-bound policy  
**GitHub Actions run:** `31468827381`  
**Evidence artifact:** `resonance-idempotency-clock-skew-v1.0`  
**Artifact ID:** `9092529978`  
**Artifact digest:** `sha256:de18c97b164742f55dcb2725af83637abe8d51014930c56d26363e6340b2a345`

## Result

# **10 / 10 — Clock-authority / skew-bound protocol passes**

Verified Report #017 showed that a durable idempotency record can expire before recovery arrives. Report #018 asks the distributed-time version of the problem:

> What if two nodes evaluate the same durable retention record using different clocks and disagree about whether replay protection is still active?

The benchmark fixes one 60-second retention record and evaluates it at two node-local logical times:

```text
created_at = T0
expires_at = T0 + 60

Node A = T0 + 50 → ACTIVE
Node B = T0 + 70 → EXPIRED
```

The underlying remote effect remains `COMMITTED / effect_count=1` for both observations. Only the temporal interpretation changes.

## Unsafe: node-local expiry becomes replay permission

The first HTTP request committed one durable effect and then dropped the response. The client observed `RemoteDisconnected / ACK_UNKNOWN`.

For the same record:

```text
expires_at = 4,000,060

Node A evaluation_time = 4,000,050
active_idempotency_records = 1

effect_count = 1
status = COMMITTED
```

Node B evaluated the same record at:

```text
evaluation_time = 4,000,070
active_idempotency_records = 0

effect_count = 1
status = COMMITTED
```

Node B then replayed the **same logical effect with the same idempotency key** using its later local clock. Because the service treated the record as expired at that supplied decision time, the request was applied again:

```text
POST #2
same Idempotency-Key
→ delivery = APPLIED
→ effect_count = 2
→ status = CONFLICT
```

# **SAME RETENTION RECORD + DIFFERENT CLOCKS CAN YIELD DIFFERENT SAFETY DECISIONS**

The duplicate is not caused by a new request identity. It is caused by allowing a local clock interpretation to decide that previously durable replay protection has expired.

## Safe path A: declared clock authority

The second scenario preserved the same local disagreement:

```text
Node A local time = T0 + 50 → ACTIVE
Node B local time = T0 + 70 → EXPIRED
```

But replay evaluation did not use either node's local clock. The declared decision clock was:

```text
authority time = T0 + 55
expires_at     = T0 + 60
```

The authoritative view therefore remained active:

```text
active_idempotency_records = 1
effect_count = 1
```

A real second HTTP POST reused the same idempotency key and was evaluated at the authority time:

```text
delivery = DEDUPLICATED
post_requests = 2
effect_count = 1
status = COMMITTED
```

The local clocks still disagreed. The protocol remained safe because one declared time authority controlled the replay decision.

## Safe path B: skew guard preserves TIME_UNKNOWN

A third scenario did not assume a perfectly authoritative clock. Instead, recovery declared a maximum clock error of 20 seconds.

The observed local time sat exactly on the expiry boundary:

```text
observed local time = T0 + 60
max clock error     = ±20
uncertainty window  = [T0 + 40, T0 + 80]
expiry              = T0 + 60
```

The expiry boundary lies inside the uncertainty interval. The safe policy therefore classified temporal state as:

```text
TIME_UNKNOWN
```

not `EXPIRED`.

Recovery reconciled authoritative remote effect state instead of replaying:

```text
remote status = COMMITTED
effect_count  = 1
second_post_made = false
```

Final remote effect count remained one.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Same durable record yields ACTIVE and EXPIRED under clock disagreement | PASS | 2/2 |
| Caller/node-local expiry reproduces same-key duplicate | PASS | 2/2 |
| Declared clock authority deduplicates despite local disagreement | PASS | 2/2 |
| Skew interval crossing expiry preserves TIME_UNKNOWN and reconciles | PASS | 2/2 |
| Final TTP clock-authority invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **SAME RETENTION RECORD + DIFFERENT CLOCKS CAN YIELD DIFFERENT SAFETY DECISIONS**

# **TIME-BASED SAFETY REQUIRES A DECLARED CLOCK AUTHORITY OR SKEW BOUND**

# **EXPIRY INSIDE CLOCK-UNCERTAINTY WINDOW ≠ SAFE REPLAY PERMISSION**

# **CLOCK DISAGREEMENT IS EVIDENCE CONFLICT**

## TTP clock rule

```text
ACK_UNKNOWN / DELAYED RECOVERY
        ↓
TIME-BASED PRECONDITION
        ↓
ESTABLISH CLOCK BASIS
   ├─ declared authority time
   │      ↓
   │   evaluate retention once
   │
   └─ bounded clock uncertainty
          ↓
      does uncertainty cross expiry?
          ├─ no  → evaluate ACTIVE / EXPIRED
          └─ yes → TIME_UNKNOWN
                     ↓
                  RECONCILE
                     ├─ COMMITTED → COMPLETE / NO REPLAY
                     ├─ ABSENT    → fresh replay decision
                     └─ UNKNOWN   → HOLD / ESCALATE
        ↓
PROVE
```

Time is therefore evidence with an authority and uncertainty model. It is not a free scalar supplied by whichever worker happens to execute the retry.

## Relationship to #016 and #017

```text
#016: did safety memory survive the failure?
#017: is surviving safety memory still valid at recovery time?
#018: whose time decides that validity, and how much uncertainty is allowed?
```

The sequence becomes:

```text
MEMORY DURABILITY
      +
RETENTION VALIDITY
      +
CLOCK AUTHORITY / SKEW
      +
RECOVERY
      =
TEMPORAL TRUST MEMORY
```

## Interpretation boundary

This benchmark uses deterministic logical clocks delivered across a real local HTTP boundary. The clock values are synthetic and intentionally separated so the decision semantics are reproducible.

It does **not** test or certify:

- NTP, PTP, chrony or operating-system clock synchronization;
- real hardware-clock drift;
- leap-second behavior;
- distributed consensus time;
- a universal acceptable clock-skew bound;
- production payment-provider idempotency semantics;
- multi-region time correctness;
- exactly-once delivery in arbitrary distributed systems;
- arbitrary agent safety.

The 20-second disagreement, 60-second TTL and ±20-second uncertainty bound are benchmark parameters, not production recommendations.

## Reproducibility

Benchmark specification:

`benchmarks/idempotency-clock-skew-v1.0/README.md`

External HTTP service:

`benchmarks/idempotency-clock-skew-v1.0/external_service.py`

Harness:

`benchmarks/idempotency-clock-skew-v1.0/run_clock_skew.py`

Workflow:

`.github/workflows/benchmark-idempotency-clock-skew.yml`

Machine-readable result:

`reports/verified/018-idempotency-clock-skew/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31468827381`

## Verdict

**Two nodes evaluated the same durable idempotency record on opposite sides of its expiry boundary while the original effect remained committed. Treating the later node-local clock as replay authority caused a same-key duplicate. A declared decision clock deduplicated the replay, while a bounded-skew policy preserved TIME_UNKNOWN and reconciled instead of replaying when the expiry boundary fell inside temporal uncertainty.**

---

**RESONANCE Verified Report #018**  
**Status:** Reproducible deterministic clock-disagreement run  
**Score:** 10/10  
**Unsafe remote effects:** 2  
**Safe authority effects:** 1  
**Safe skew-guard effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
