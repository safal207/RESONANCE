# RESONANCE Idempotency State Durability / Service Restart v1.0

This benchmark extends Verified Report #015 from transport ambiguity into restart durability.

## Question

Does reusing the same `Idempotency-Key` remain safe after the external HTTP service restarts?

The benchmark separates two forms of remote memory:

```text
durable effect ledger
        !=
durable idempotency / dedupe ledger
```

A stable request key is useful only if the consumer still remembers that key across the failure window it is expected to protect.

## Topology

```text
PostgreSQL 17.6
  business state + outbox
          |
          v HTTP
Dockerized external service
  persistent SQLite effect ledger on Docker volume
  + either volatile or durable dedupe state
```

The HTTP process is destroyed and recreated between the first ambiguous delivery and recovery. A generated `boot_id` proves the service process changed while the mounted SQLite volume preserves remote effect state.

## Scenarios

1. **Unsafe volatile dedupe state**
   - POST with one stable key commits remote effect.
   - HTTP acknowledgement is dropped.
   - Service container is removed and recreated.
   - Durable effect ledger still reports one committed effect.
   - Volatile dedupe memory is gone.
   - Same key is redelivered and is applied again.
   - Final remote effect count: **2**.

2. **Safe durable dedupe state**
   - Effect and idempotency mapping are persisted in SQLite.
   - HTTP acknowledgement is dropped.
   - Service container is removed and recreated against the same volume.
   - Same key is redelivered.
   - Persistent idempotency record absorbs the redelivery.
   - Final remote effect count: **1**.

3. **Safe reconcile after restart**
   - Dedupe state is intentionally volatile.
   - Effect commits and acknowledgement is lost.
   - Service restarts, losing volatile dedupe memory.
   - Worker queries authoritative remote status before any second POST.
   - Remote status is `COMMITTED`, so replay is skipped.
   - Final remote effect count: **1**.

## Invariants

```text
STABLE KEY + VOLATILE DEDUPE STATE != IDEMPOTENT DELIVERY
REMOTE EFFECT DURABILITY != IDEMPOTENCY-MEMORY DURABILITY
DEDUPE STATE MUST SURVIVE THE FAILURE WINDOW IT PROTECTS
ACK_UNKNOWN + SERVICE RESTART -> RECONCILE BEFORE REPLAY
SERVICE RESTART IS A TRUST-MEMORY TRANSITION
```

## Scope

This is a local reproducible benchmark. The HTTP boundary and service restart are real, and the remote ledger is durable across container replacement via SQLite on a Docker named volume. It does not model production multi-region storage, replicated caches, provider SLAs, disk corruption, consensus, or universal exactly-once semantics.
