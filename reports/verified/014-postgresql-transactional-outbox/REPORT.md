# RESONANCE Verified Report #014

# PostgreSQL Transactional Outbox / External Effect Boundary

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** PostgreSQL Transactional Outbox Boundary v1.0  
**Database:** PostgreSQL 17.6  
**Container image:** `postgres:17.6-alpine`  
**GitHub Actions run:** `31463869740`  
**Evidence artifact:** `resonance-postgresql-transactional-outbox-v1.0`  
**Artifact ID:** `9090766696`  
**Artifact digest:** `sha256:7732375332cfee2507eda5ec72df190cbe94c1ee18bd3f1bc86ec1a5884562e2`

## Result

# **10 / 10 — Transactional outbox cross-boundary protocol passes**

Reports #012 and #013 kept the consequential effect inside PostgreSQL. Report #014 crosses the next boundary: the database can commit correctly while an external effect lives in another transaction and its acknowledgement can disappear.

The question is:

> How do we preserve one logical business transition and one external effect when the database commit and external acknowledgement cannot share one transaction?

The benchmark separates two guarantees:

```text
Atomicity A: business state + durable outbox intent
Atomicity B: external effect + stable idempotency identity
```

The gap between them remains a recovery problem.

## Unsafe control: one DB transition, two external effects

The business transition committed once:

```text
operation = COMMITTED
version   = 101
```

Then the synthetic external service committed the first effect. Its acknowledgement was lost.

The recovery path generated a new request identity instead of preserving the logical operation identity:

```text
attempt 1 → unsafe:attempt:1 → APPLIED
ACK lost
attempt 2 → unsafe:attempt:2 → APPLIED
```

Observed result:

```text
business transitions = 1
external effects      = 2
```

The database state was correct. The cross-boundary trajectory was not.

## Transactional outbox: commit the intent with the state

The safe adapter writes the business transition and durable outbox row inside one PostgreSQL transaction.

A synthetic crash before commit proved rollback atomicity:

```text
state      = ABSENT
version    = 100
outbox rows = 0
```

A successful transaction then produced:

```text
state      = COMMITTED
version    = 101
outbox rows = 1
outbox      = PENDING
key         = op-1:external-effect:v1
```

This closes the database-side lost-intent gap: either both the state transition and delivery intent exist, or neither does.

## Safe redelivery: stable identity makes duplicate delivery harmless

The worker delivered the pending outbox record with the stable key:

```text
op-1:external-effect:v1
```

Attempt 1:

```text
external effect → APPLIED
ACK → lost
outbox → still PENDING
```

Recovery delivered the same logical message again with the same key:

```text
attempt 2 → DEDUPLICATED
external effects = 1
```

The external ledger then reconciled `COMMITTED`, and the outbox row moved to `DELIVERED`.

The benchmark therefore distinguishes:

```text
at-least-once delivery attempts
        ≠
multiple committed effects
```

when the external boundary enforces stable idempotency identity.

## Safer recovery: reconcile before a second external call

A second scenario made the recovery rule stronger.

After attempt 1 committed the external effect and its acknowledgement was lost, the worker first queried the external ledger by the stable key.

Observed:

```text
external status = COMMITTED
second external call made = false
external effects = 1
outbox = DELIVERED
```

This is the cross-boundary form of the earlier TTP recovery rule:

# **AMBIGUOUS EXTERNAL ACK → RECONCILE EXTERNAL STATE BEFORE RE-EXECUTION**

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe DB/external duplicate reproduced | PASS | 2/2 |
| Business state + outbox intent atomic | PASS | 2/2 |
| Stable idempotency key deduped redelivery | PASS | 2/2 |
| Ambiguous ACK reconciled before external retry | PASS | 2/2 |
| Final cross-boundary invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## TTP cross-boundary rule

The database can prove that a business transition and delivery intent committed together. It cannot by itself prove whether an external system applied a request whose acknowledgement was lost.

The adapter path becomes:

```text
OBSERVE / VERIFY / AUTHORIZE / BIND
              ↓
BUSINESS TRANSACTION
  state transition + outbox intent
              ↓
            COMMIT
              ↓
        OUTBOX WORKER
              ↓
   stable idempotency identity
              ↓
      EXTERNAL EFFECT
        ├─ ACK → mark delivered
        └─ UNKNOWN
             ↓
          RECONCILE
             ├─ COMMITTED → mark delivered
             ├─ ABSENT    → fresh delivery allowed
             └─ UNKNOWN   → hold / retry reconciliation
              ↓
            PROVE
```

## New invariants

# **DB COMMITTED ≠ EXTERNAL EFFECT ACKNOWLEDGED**

# **DB COMMITTED ≠ EXTERNAL EFFECT ABSENT**

# **OUTBOX INTENT MUST COMMIT WITH BUSINESS STATE**

# **REDELIVERY MUST PRESERVE LOGICAL EFFECT IDENTITY**

# **AMBIGUOUS EXTERNAL ACK → RECONCILE BEFORE BUSINESS RE-EXECUTION**

The durable outbox removes one failure gap. Stable idempotency plus external reconciliation closes another. Neither should be described as universal exactly-once delivery.

## Interpretation boundary

The external service in this benchmark is a synthetic `external_effects` ledger reached through a separate PostgreSQL transaction. This deliberately creates a transaction boundary, but it is not a real payment processor, message broker, blockchain, SaaS API or distributed service.

This report does **not** prove or certify:

- exactly-once delivery in arbitrary distributed systems;
- two-phase commit or distributed transaction correctness;
- broker delivery guarantees;
- production payment semantics;
- network partition behavior;
- external API idempotency implementations;
- failover or replication behavior;
- arbitrary agent safety.

The result validates one explicit TTP adapter contract under a local reproducible setup.

## Reproducibility

Benchmark specification:

`benchmarks/postgresql-transactional-outbox-v1.0/README.md`

Harness:

`benchmarks/postgresql-transactional-outbox-v1.0/run_transactional_outbox.py`

Workflow:

`.github/workflows/benchmark-postgresql-transactional-outbox.yml`

Machine-readable result:

`reports/verified/014-postgresql-transactional-outbox/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31463869740`

## Verdict

**A single committed PostgreSQL business transition produced two external effects when acknowledgement loss was followed by a new request identity. Committing the outbox intent with business state, preserving one stable idempotency identity across redelivery, and reconciling external status after ambiguous acknowledgement preserved one external effect in both safe trajectories.**

---

**RESONANCE Verified Report #014**  
**Status:** Reproducible PostgreSQL transactional-outbox boundary run  
**Score:** 10/10  
**Unsafe business transitions:** 1  
**Unsafe external effects:** 2  
**Safe external effects:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
