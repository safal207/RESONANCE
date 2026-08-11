# PostgreSQL Isolation-Level Matrix v1.0

This benchmark validates how the RESONANCE Transactional Trust Protocol (TTP) classifies a stale concurrent writer across PostgreSQL isolation levels.

## Matrix

- `READ COMMITTED`
- `REPEATABLE READ`
- `SERIALIZABLE`

Each safe scenario uses two independent PostgreSQL connections. Both begin a transaction at the same isolation level, observe the same `ABSENT / version=100` row, synchronize, and race on the same conditional mutation:

```sql
UPDATE operations
SET state = 'committed',
    version = version + 1
WHERE id = 'op-1'
  AND state = 'absent'
  AND version = 100
RETURNING state, version;
```

Only a transaction receiving a returned row may insert the corresponding effect in that same transaction.

The losing transaction does not blindly replay the write. It aborts/ends the stale transaction, opens a fresh observation path, and reconciles current state before any possible retry decision.

## Expected signal classes

The benchmark treats the exact PostgreSQL signal as evidence, not as an interchangeable generic error:

- `READ COMMITTED`: a concurrent update may cause the conditional `UPDATE` to match zero rows after PostgreSQL re-evaluates the row against the current committed version.
- `REPEATABLE READ`: a transaction attempting to modify a row changed since its snapshot may be aborted with `serialization_failure` / SQLSTATE `40001`.
- `SERIALIZABLE`: applications must also be prepared for `serialization_failure` / SQLSTATE `40001` and retry a transaction from the beginning if a retry remains legal.

The canonical result is the observed CI artifact. If PostgreSQL produces a different signal on the pinned environment, the benchmark fails rather than rewriting the expected result after the fact.

## TTP rule

```text
DB CONFLICT SIGNAL
        ↓
ABORT / END STALE TRANSACTION
        ↓
RE-OBSERVE AUTHORITATIVE STATE
        ↓
RE-VERIFY + RE-BIND
        ↓
RETRY ONLY IF STILL ABSENT + LEGAL
```

A serialization failure is retryable at the database transaction layer; it is not proof that the business operation should be executed again.

## Scope

This is a real PostgreSQL concurrency benchmark over synthetic local operation/effect tables. It is not a certification of all PostgreSQL isolation behavior, distributed failover, replication, external side effects, or arbitrary agent safety.
