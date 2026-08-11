# RESONANCE PostgreSQL Transactional Trust Adapter v1.0

This benchmark tests whether the core TTP execution invariant survives contact with a real transactional database instead of an in-memory state machine.

## Question

Can two independent PostgreSQL connections both observe the same legal `ABSENT / version=100` state, while the database still guarantees that only one version-bound transition commits?

## Unsafe control

Both workers:

1. read `ABSENT / version=100`;
2. synchronize on a barrier;
3. perform an unconditional state update and insert an effect.

Expected result: two committed effects.

## Safe adapter

Both workers:

1. read `ABSENT / version=100` through independent connections;
2. bind the decision to `expected_version=100`;
3. synchronize on a barrier;
4. execute the mutation authority predicate:

```sql
UPDATE operations
SET state = 'committed',
    version = version + 1,
    updated_at = clock_timestamp()
WHERE id = 'op-1'
  AND state = 'absent'
  AND version = 100
RETURNING state, version;
```

Only the worker receiving a returned row may insert the corresponding effect in the same transaction. A zero-row result is treated as `PRECONDITION_FAILED`, followed by reread/reconciliation.

Expected result:

- exactly one winner;
- exactly one stale writer rejected;
- final state `COMMITTED / version=101`;
- exactly one committed effect;
- losing worker rereads the winner's committed state.

## Scope

The benchmark uses a PostgreSQL service container in GitHub Actions and two independent client connections. It does not claim distributed consensus, cross-database linearizability, exactly-once delivery, or production certification.

## TTP mapping

```text
OBSERVE  -> SELECT state, version
BIND     -> expected_version=100
COMPARE  -> UPDATE ... WHERE state='absent' AND version=100
COMMIT   -> UPDATE + effect INSERT in one DB transaction
RECONCILE-> stale writer rereads authoritative row
PROVE    -> final row + effect count + worker outcomes
```

The critical database rule is:

**the state comparison and state transition are evaluated by the same mutation authority inside one transaction boundary.**
