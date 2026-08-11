# RESONANCE HTTP Idempotency Boundary v1.0

This benchmark extends Transactional Trust Protocol (TTP) v1.0 across a real HTTP network boundary.

## Topology

```text
PostgreSQL 17.6
  business state + outbox intent
            ↓
       outbox worker
            ↓ HTTP
separate Docker container
  external effect service
```

The external service owns effect state in its own process memory. PostgreSQL cannot commit, roll back or inspect that state directly.

## Failure injection

The external service supports a deterministic synthetic failure:

```text
POST /effects
  ↓
remote effect committed
  ↓
TCP/HTTP connection closed before response
  ↓
client observes ACK_UNKNOWN
```

The effect therefore exists remotely even though the worker did not receive an HTTP acknowledgement.

## Scenarios

1. **Unsafe retry with a new identity**
   - business state + outbox are committed once;
   - first POST applies a remote effect, then drops the response;
   - retry generates a new idempotency key;
   - second POST applies a second remote effect.

2. **Safe redelivery with one stable identity**
   - first POST applies the remote effect, then drops the response;
   - worker performs a real second POST with the same `Idempotency-Key`;
   - remote service returns `deduplicated`;
   - remote effect count remains one.

3. **Safe reconcile before retry**
   - first POST applies the remote effect, then drops the response;
   - worker calls `GET /status/{operation_id}`;
   - remote status is `committed`;
   - no second POST is issued.

## Core invariants

```text
HTTP ACK LOST ≠ REMOTE EFFECT ABSENT

SAME LOGICAL EFFECT
→ SAME IDEMPOTENCY IDENTITY

ACK_UNKNOWN
→ RECONCILE REMOTE STATE
→ RE-POST ONLY IF STILL ABSENT + LEGAL
```

## Scope

The benchmark uses:

- a real PostgreSQL 17.6 service container;
- a separate Dockerized Python HTTP service;
- real localhost TCP/HTTP requests between the benchmark worker and that container;
- synthetic local business data only.

It does not claim universal exactly-once delivery, production payment correctness, broker guarantees, network-partition coverage or arbitrary agent safety.

## Run

The canonical GitHub Actions workflow is:

`.github/workflows/benchmark-http-idempotency-boundary.yml`
