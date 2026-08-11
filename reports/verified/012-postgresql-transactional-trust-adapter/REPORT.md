# RESONANCE Verified Report #012

# PostgreSQL Transactional Trust Adapter

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** PostgreSQL Transactional Trust Adapter v1.0  
**Database:** PostgreSQL 17.6  
**Container image:** `postgres:17.6-alpine`  
**Image digest observed by GitHub Actions:** `sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94`  
**GitHub Actions run:** `31461002473`  
**Evidence artifact:** `resonance-postgresql-transactional-trust-adapter-v1.0`  
**Artifact ID:** `9089776304`  
**Artifact digest:** `sha256:4a9ed5a039c624acd1f0f5c0feef07c47ade79128a62050977089b0109cebaf1`

## Result

# **10 / 10 — PostgreSQL atomic state-version adapter passes**

Report #010 established the atomic-transition rule in an in-memory synthetic store. Report #011 composed the wider Transactional Trust Protocol end-to-end. Report #012 replaces the critical shared-state mutation with a real PostgreSQL service and two independent database connections.

The question is narrow and important:

> Can two actors both make a correct read of the same legal state, while the database still guarantees that only one stale-version-bound mutation creates the effect?

In this run, yes.

## Unsafe control

Two connections both observed:

```text
state   = ABSENT
version = 100
```

They then synchronized and each performed an unconditional mutation plus effect insert.

Observed database result:

```text
Node A → unconditional commit → version 101
Node B → unconditional commit → version 102
final effects = 2
```

Both initial reads were correct. The duplicate appeared because the earlier read was not enforced as a mutation precondition.

## Safe PostgreSQL adapter

The safe path used the observed version as part of the mutation predicate:

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

Only a connection receiving a returned row was allowed to insert the corresponding effect, in the same database transaction.

Both workers first observed `ABSENT / version=100` through independent connections.

The actual race resolved as:

```text
Node A
expected version = 100
→ UPDATE matched
→ COMMITTED / version 101
→ effect #1
→ transaction committed

Node B
expected version = 100
→ UPDATE matched 0 rows
→ PRECONDITION_FAILED
→ reread
→ COMMITTED / version 101 / effects=1
```

Final database state:

```text
state   = COMMITTED
version = 101
effects = 1
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Real PostgreSQL service observed | PASS | 2/2 |
| Unsafe two-connection duplicate reproduced | PASS | 2/2 |
| Conditional update allowed exactly one winner | PASS | 2/2 |
| Stale writer reconciled `COMMITTED / version=101 / effects=1` | PASS | 2/2 |
| Final database invariant proved | PASS | 2/2 |
| **Total** |  | **10/10** |

## What moved from model to database

The TTP mapping is now concrete:

```text
OBSERVE   → SELECT state, version
BIND      → expected_version = 100
COMPARE   → UPDATE ... WHERE state='absent' AND version=100
COMMIT    → conditional UPDATE + effect INSERT in one transaction
RECONCILE → zero-row writer rereads authoritative state
PROVE     → final state/version + effect count + worker outcomes
```

The key invariant survived the move from an in-memory model to PostgreSQL:

# **TWO VALID READERS ≠ TWO VALID WRITERS**

and the database adapter rule becomes:

# **COMPARE + TRANSITION + EFFECT MUST SHARE THE SAME ENFORCED TRANSACTION BOUNDARY**

A zero-row conditional update is not necessarily an operational failure. In this context it is the database proving that the world changed after observation and preventing the stale transition.

## Why this matters

The distinction is practical for agent systems that mutate payments, jobs, approvals, orders, wallets, reservations or other shared business state.

An application can correctly verify:

```text
state = ABSENT
```

and still be wrong by the time it writes. Carrying `version=100` into the mutation predicate allows the storage authority to decide whether that observation is still current at the transition boundary.

This is the PostgreSQL form of the TTP rule:

```text
READ
→ VERIFY
→ BIND VERSION
→ CONDITIONAL MUTATION
→ CONFLICT OR COMMIT
→ REREAD / RECONCILE
→ PROVE
```

## Important boundary

This report does **not** prove or certify:

- exactly-once delivery in arbitrary systems;
- cross-database atomicity;
- distributed consensus or global linearizability;
- correctness under every PostgreSQL isolation level;
- failover, replication lag or network partition behavior;
- transaction behavior across external APIs plus PostgreSQL;
- production payment or blockchain semantics;
- arbitrary agent safety.

The operation and effect tables are synthetic. PostgreSQL itself is real and was run as a GitHub Actions service container with two independent client connections.

This is an adapter validation for one TTP invariant, not a PostgreSQL security claim.

## Reproducibility

Benchmark specification:

`benchmarks/postgresql-transactional-trust-adapter-v1.0/README.md`

Harness:

`benchmarks/postgresql-transactional-trust-adapter-v1.0/run_postgresql_adapter.py`

Workflow:

`.github/workflows/benchmark-postgresql-transactional-trust-adapter.yml`

Machine-readable result:

`reports/verified/012-postgresql-transactional-trust-adapter/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31461002473`

## Verdict

**Two real PostgreSQL connections both observed the same legal `ABSENT / version=100` snapshot. Unconditional writes reproduced two committed effects. Binding the transition to that version inside PostgreSQL allowed exactly one winner, converted the stale writer into a zero-row precondition failure, and let the loser reconcile the authoritative `COMMITTED / version=101 / effects=1` state.**

The RESONANCE rule now has a real database adapter:

# **observe → bind version → condition the mutation → commit effect in the same transaction → reconcile stale writers → prove the final invariant**

---

**RESONANCE Verified Report #012**  
**Status:** Reproducible PostgreSQL adapter run  
**Score:** 10/10  
**Unsafe effects:** 2  
**Safe effects:** 1  
**Independent DB connections:** 2  
**Vulnerability claim:** No  
**External safety certification:** No
