# RESONANCE Verified Report #016

# Idempotency State Durability / Service Restart

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Idempotency State Durability / Service Restart v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP service with persistent SQLite effect ledger  
**GitHub Actions run:** `31466444029`  
**Evidence artifact:** `resonance-idempotency-state-durability-v1.0`  
**Artifact ID:** `9091692210`  
**Artifact digest:** `sha256:968fdc68906cfdb2603e3b130a0f0c487d1b406f2eb9d73d6f6f6224231cdd13`

## Result

# **10 / 10 — Idempotency-state durability protocol passes**

Verified Report #015 showed that one stable HTTP idempotency identity can absorb a real redelivery after an ambiguous acknowledgement. Report #016 tests the next failure boundary: what happens when the remote service itself restarts after the effect committed but before the client obtained certainty?

The benchmark separates two kinds of remote memory:

```text
remote effect durability
        !=
idempotency / dedupe memory durability
```

The remote effect ledger is always stored in SQLite on a Docker named volume. Only the dedupe state changes between the unsafe and safe cases.

## Restart evidence

The first volatile service instance reported:

```text
boot_id = 7fa5e591a3fa4077b6249dab0da1c624
hostname = ed944b074e1c
pid = 1
```

After the container was removed and recreated against the same persistent volume:

```text
boot_id = 2803e3ac7e96440187fd4fcb9ad347b3
hostname = b853c379da5a
pid = 1
```

The process identity changed, while the remote status still showed:

```text
status       = COMMITTED
effect_count = 1
post_requests = 1
```

The remote effect therefore survived the service restart.

## Unsafe: stable key, volatile dedupe state

The first request used:

```text
Idempotency-Key: restart-volatile-op:effect:v1
```

The remote effect was durably inserted, then the connection was closed before the response reached the client:

```text
client outcome = ACK_UNKNOWN
error          = RemoteDisconnected
remote effects = 1
```

The container was then destroyed and recreated. The SQLite effect ledger still contained effect #1, but the in-memory dedupe map was empty.

The worker reused the **same** idempotency key:

```text
POST #2
same Idempotency-Key
→ delivery = APPLIED
```

Final remote state:

```text
post_requests = 2
effect_count  = 2
status        = CONFLICT
```

The duplicate happened even though the client preserved request identity correctly.

# **STABLE KEY + VOLATILE DEDUPE STATE ≠ IDEMPOTENT DELIVERY**

## Safe: durable dedupe state

The safe service stores the idempotency mapping in the same persistent SQLite volume as the remote effect ledger.

Before restart:

```text
remote effects                = 1
durable idempotency records   = 1
client outcome                = ACK_UNKNOWN
```

The container was removed and recreated. Its boot id changed:

```text
36d472f40ed9442f8010203f4b636fd7
→
696deb30dd684a038670280c091dc814
```

After restart, before any retry:

```text
remote effects              = 1
durable idempotency records = 1
status                      = COMMITTED
```

A real second HTTP POST reused the same key:

```text
POST #2
same Idempotency-Key
→ delivery = DEDUPLICATED
```

Final remote state:

```text
post_requests = 2
effect_count  = 1
status        = COMMITTED
```

The safe path therefore preserved one effect across both ambiguous acknowledgement and service restart.

## Safe alternative: reconcile after restart

A third scenario deliberately used **volatile** dedupe memory again.

The first request committed one durable effect and ended in `ACK_UNKNOWN`. The service was restarted, losing the volatile dedupe map. Instead of redelivering, recovery queried authoritative remote state.

Observed after restart:

```text
status       = COMMITTED
effect_count = 1
post_requests = 1
```

The worker then made no second POST:

```text
second_post_made = false
```

Final state remained:

```text
remote effects = 1
outbox status  = DELIVERED
delivery attempts = 1
```

This demonstrates a second safe recovery path: durable dedupe state is powerful, but authoritative reconciliation can also stop replay when dedupe memory has been lost.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Service restart preserved durable effect ledger | PASS | 2/2 |
| Volatile dedupe memory loss reproduced duplicate | PASS | 2/2 |
| Durable idempotency state survived restart and deduped | PASS | 2/2 |
| Authoritative reconcile avoided replay after restart | PASS | 2/2 |
| Final TTP restart-memory invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **STABLE KEY + VOLATILE DEDUPE STATE ≠ IDEMPOTENT DELIVERY**

# **REMOTE EFFECT DURABILITY ≠ IDEMPOTENCY-MEMORY DURABILITY**

# **DEDUPE STATE MUST SURVIVE THE FAILURE WINDOW IT PROTECTS**

# **ACK_UNKNOWN + SERVICE RESTART → RECONCILE BEFORE REPLAY**

# **SERVICE RESTART IS A TRUST-MEMORY TRANSITION**

The last invariant matters beyond HTTP. Any safety decision that depends on remembered execution history is only as strong as the durability, freshness and recoverability of that memory.

## TTP memory-durability rule

```text
REMOTE EFFECT
   ↓
ACK_UNKNOWN
   ↓
SERVICE RESTART
   ↓
TRUST / DEDUPE MEMORY CHECK
   ├─ durable memory present → same key may be safely redelivered under contract
   ├─ memory unavailable     → reconcile authoritative effect state
   └─ effect state unknown   → HOLD / reconcile again / escalate
   ↓
PROVE
```

A stable request identity is necessary but not sufficient. The consumer must preserve the state that gives that identity meaning, or recovery must fall back to an authoritative effect ledger before replay.

## Interpretation boundary

The HTTP restart is real and the effect ledger is durable across container replacement through SQLite on a Docker named volume. The benchmark is still local and bounded.

It does **not** prove or certify:

- multi-region durability;
- replicated cache correctness;
- disk-loss or volume-corruption recovery;
- consensus or failover semantics;
- production payment-provider idempotency;
- exactly-once delivery in arbitrary distributed systems;
- durable remote state across total storage loss;
- arbitrary agent safety.

This is also **not yet a CML integration**. It is a protocol-level result about durable execution memory that can inform a future MEMORY/CML adapter.

## Reproducibility

Benchmark specification:

`benchmarks/idempotency-state-durability-v1.0/README.md`

External service:

`benchmarks/idempotency-state-durability-v1.0/external_service.py`

Harness:

`benchmarks/idempotency-state-durability-v1.0/run_restart_durability.py`

Workflow:

`.github/workflows/benchmark-idempotency-state-durability.yml`

Machine-readable result:

`reports/verified/016-idempotency-state-durability/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31466444029`

## Verdict

**The same stable idempotency key produced a second remote effect after service restart when the consumer's dedupe memory was volatile, even though the first effect survived durably. Persisting the idempotency mapping across restart caused the same real redelivery to be deduplicated, while authoritative reconciliation avoided replay entirely even when volatile dedupe memory was lost.**

---

**RESONANCE Verified Report #016**  
**Status:** Reproducible service-restart durability run  
**Score:** 10/10  
**Unsafe remote effects:** 2  
**Safe durable-dedupe effects:** 1  
**Safe reconcile effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
