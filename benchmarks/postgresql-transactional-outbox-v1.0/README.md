# PostgreSQL Transactional Outbox Boundary v1.0

This benchmark extends RESONANCE Transactional Trust Protocol v1.0 beyond a single database mutation boundary.

## Question

What happens when PostgreSQL has already committed the business transition, but the external effect acknowledgement is lost and delivery is retried?

The benchmark separates two guarantees:

```text
Atomicity A: business state + durable outbox intent
Atomicity B: external effect + stable idempotency identity
```

The network/process boundary between them can still produce `UNKNOWN`.

## Real component

- PostgreSQL 17.6 service container in GitHub Actions
- independent database transactions for business/outbox state and the synthetic external service ledger
- psycopg 3.2.9

The `external_effects` table is a local synthetic stand-in for an external service that supports idempotency by key. It is deliberately reached in a separate transaction so it is outside the business-state transaction.

## Scenarios

1. **Unsafe boundary duplicate**
   - business state commits;
   - external effect commits;
   - acknowledgement is lost;
   - recovery generates a new request identity;
   - redelivery commits a second external effect.

2. **Transactional outbox atomicity**
   - business state transition and outbox row are written in one PostgreSQL transaction;
   - a synthetic pre-commit crash rolls both back;
   - a successful commit persists both together.

3. **Safe redelivery with stable idempotency**
   - outbox uses a stable idempotency key;
   - first external effect commits but ACK is lost;
   - redelivery reuses the same key;
   - the external boundary deduplicates the second delivery;
   - reconciliation marks the outbox row delivered.

4. **Reconcile before retry**
   - first external effect commits but ACK is lost;
   - recovery queries external state by stable key before a second external call;
   - `COMMITTED` closes the outbox without re-executing the effect.

## Invariants

```text
DB COMMITTED ≠ EXTERNAL EFFECT ACKNOWLEDGED
DB COMMITTED ≠ EXTERNAL EFFECT ABSENT
OUTBOX INTENT MUST COMMIT WITH BUSINESS STATE
REDELIVERY MUST REUSE STABLE EFFECT IDENTITY
AMBIGUOUS ACK → RECONCILE BEFORE BUSINESS RE-EXECUTION
```

Reference path:

```text
BUSINESS TX
  → state transition + outbox intent
  → COMMIT
  → worker delivery
  → external idempotency boundary
  → ACK or UNKNOWN
  → reconcile external status
  → mark outbox delivered
  → prove one business transition + one external effect
```

## Score

10 points total:

- unsafe DB/external boundary duplicate reproduced — 2
- state + outbox intent atomicity — 2
- stable idempotency key dedupes redelivery — 2
- ambiguous ACK reconciles before external retry — 2
- final cross-boundary invariant proved — 2

## Boundary

This is not a claim of exactly-once delivery in arbitrary distributed systems. The external service is synthetic, the idempotency contract is explicitly modeled, and no production API, payment rail, queue, broker, cloud service or external credential is used.
