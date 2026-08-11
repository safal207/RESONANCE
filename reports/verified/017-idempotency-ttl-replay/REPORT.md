# RESONANCE Verified Report #017

# Idempotency TTL / Replay After Expiry

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Idempotency TTL / Replay After Expiry v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP service with persistent SQLite effect/idempotency ledger  
**Clock:** deterministic logical epoch supplied over HTTP  
**GitHub Actions run:** `31467526532`  
**Evidence artifact:** `resonance-idempotency-ttl-replay-v1.0`  
**Artifact ID:** `9092068450`  
**Artifact digest:** `sha256:9e3da946190c6ab6e3b9ab26d0b18d0f5856c740a3f532bae70b7ca0dbdbfc26`

## Result

# **10 / 10 — Idempotency-retention window protocol passes**

Verified Report #016 established that idempotency memory must survive the failure window it is expected to protect. Report #017 asks the temporal version of the same question:

> What if the idempotency record is durable, but expires before a delayed recovery or replay arrives?

The benchmark uses one persistent external effect ledger and one persistent idempotency ledger. The only variable is the relationship between the idempotency TTL and the modeled recovery window.

```text
recovery / replay delay = 120 seconds
unsafe TTL             = 60 seconds
safe TTL               = 300 seconds
```

The clock is deterministic: the HTTP service evaluates explicit logical epochs supplied by the harness. No wall-clock waiting is used.

## Unsafe: memory expires before recovery finishes

At logical time:

```text
T0 = 1,000,000
```

the worker sent:

```text
POST /effects
Idempotency-Key: ttl-unsafe-op:effect:v1
TTL: 60 seconds
```

The remote service durably committed one effect and stored an idempotency record:

```text
created_at = 1,000,000
expires_at = 1,000,060
effect_count = 1
active_idempotency_records = 1
```

The HTTP acknowledgement was then lost and the client observed `RemoteDisconnected / ACK_UNKNOWN`.

Recovery did not arrive until:

```text
T1 = 1,000,120
```

At that moment the authoritative remote snapshot showed:

```text
effect_count = 1
status = COMMITTED
active_idempotency_records = 0
```

The effect still existed, but the protection record had expired.

The worker then replayed the **same logical effect with the same key**. Because the record was outside its retention window, the service treated the key as available again:

```text
POST #2
same Idempotency-Key
→ delivery = APPLIED
```

Final remote state:

```text
post_requests = 2
effect_count = 2
status = CONFLICT
```

# **STABLE IDENTITY + EXPIRED DEDUPE MEMORY ≠ IDEMPOTENT DELIVERY**

## Safe: retention covers the recovery window

The safe case used the same 120-second recovery delay but a 300-second idempotency TTL.

```text
T0 = 2,000,000
expires_at = 2,000,300
retry_at = 2,000,120
```

At retry time the idempotency record was still active:

```text
active_idempotency_records = 1
effect_count = 1
```

A real second HTTP POST reused the same key and returned:

```text
delivery = DEDUPLICATED
```

Final remote state:

```text
post_requests = 2
effect_count = 1
status = COMMITTED
```

The same delayed replay therefore changed from unsafe to safe solely because the memory retention window covered the modeled recovery window.

## Safe alternative: reconcile after TTL expiry

A third scenario intentionally used the unsafe 60-second TTL again.

The first remote effect committed and the HTTP acknowledgement was lost. Recovery occurred 120 seconds later, after the idempotency record had expired:

```text
active_idempotency_records = 0
```

Instead of replaying, the worker queried authoritative remote operation status.

Observed:

```text
status = COMMITTED
effect_count = 1
post_requests = 1
```

Therefore:

```text
second_post_made = false
```

Final remote effect count remained one.

This matters because TTL expiry is not evidence about the underlying business effect. It is only evidence that the dedupe guarantee provided by that record is no longer available.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Effect persists while idempotency record transitions active → expired | PASS | 2/2 |
| TTL shorter than recovery window reproduces same-key duplicate | PASS | 2/2 |
| Retention covering recovery window deduplicates delayed retry | PASS | 2/2 |
| Authoritative reconcile after expiry prevents replay | PASS | 2/2 |
| Final TTP time-memory-recovery invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **DEDUPE RETENTION WINDOW MUST COVER THE RECOVERY / REPLAY WINDOW IT PROTECTS**

# **EXPIRED DEDUPE MEMORY ≠ EFFECT ABSENT**

# **STABLE IDENTITY + EXPIRED MEMORY CAN STILL DUPLICATE A DURABLE EFFECT**

# **AFTER IDEMPOTENCY EXPIRY, RECONCILE AUTHORITATIVE EFFECT STATE BEFORE CONSEQUENTIAL REPLAY**

# **TIME + MEMORY + RECOVERY POLICY FORM ONE SAFETY BOUNDARY**

## TTP time-memory rule

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
   │   same-key redelivery may be deduplicated under contract
   │
   └─ record expired / unavailable
          ↓
      RECONCILE AUTHORITATIVE EFFECT STATE
          ├─ COMMITTED → COMPLETE / NO REPLAY
          ├─ ABSENT    → fresh replay decision
          └─ UNKNOWN   → HOLD / reconcile again / escalate
   ↓
PROVE
```

The retention window is therefore part of the execution contract, not an implementation footnote.

## Why this is different from #016

Report #016 tested **durability across service restart**: the question was whether dedupe memory survives process replacement.

Report #017 keeps the service and persistent storage alive but advances logical time past the idempotency record's expiry. The new failure is temporal:

```text
memory exists durably
but no longer authorizes deduplication
```

This distinguishes:

```text
DURABLE MEMORY
      !=
MEMORY VALID FOR THIS DECISION TIME
```

## Interpretation boundary

The network boundary and SQLite persistence are real local components. Time progression is deterministic benchmark time rather than wall-clock waiting.

This report does **not** prove or certify:

- a universal production idempotency TTL;
- real provider retention policies;
- distributed-clock correctness or clock synchronization;
- multi-region cache eviction semantics;
- queue retention or dead-letter behavior;
- exactly-once delivery in arbitrary distributed systems;
- arbitrary agent safety.

The values `60s`, `120s` and `300s` are benchmark parameters, not recommended production defaults.

## Reproducibility

Benchmark specification:

`benchmarks/idempotency-ttl-replay-v1.0/README.md`

External HTTP service:

`benchmarks/idempotency-ttl-replay-v1.0/external_service.py`

Harness:

`benchmarks/idempotency-ttl-replay-v1.0/run_ttl_replay.py`

Workflow:

`.github/workflows/benchmark-idempotency-ttl-replay.yml`

Machine-readable result:

`reports/verified/017-idempotency-ttl-replay/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31467526532`

## Verdict

**A durable remote effect was duplicated by a delayed retry using the same idempotency key after the key's 60-second dedupe record expired before a 120-second recovery window completed. Extending retention to 300 seconds caused the same delayed retry to be deduplicated, while authoritative reconciliation after expiry prevented replay entirely.**

---

**RESONANCE Verified Report #017**  
**Status:** Reproducible deterministic time-window run  
**Score:** 10/10  
**Unsafe remote effects:** 2  
**Safe retention effects:** 1  
**Safe reconcile effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
