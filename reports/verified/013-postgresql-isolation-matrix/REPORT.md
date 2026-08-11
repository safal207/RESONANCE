# RESONANCE Verified Report #013

# PostgreSQL Isolation-Level Matrix

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** PostgreSQL Isolation-Level Matrix v1.0  
**Database:** PostgreSQL 17.6  
**GitHub Actions run:** `31463056442`  
**Evidence artifact:** `resonance-postgresql-isolation-matrix-v1.0`  
**Artifact ID:** `9090495818`  
**Artifact digest:** `sha256:b22f5d36ed8a8aee6d751c639f48f8b760b2237ed7edf0e86c4a455f449743a0`

## Result

# **10 / 10 — PostgreSQL isolation-level TTP matrix passes**

Report #012 showed that a version-bound PostgreSQL mutation can turn two valid readers into one valid writer. Report #013 asks the next operational question:

> When the same stale-writer race is executed under different PostgreSQL isolation levels, what signal does the losing transaction receive — and what should an agent do with it?

The answer is not one generic “retryable error”. The database signal changes with isolation level, while the TTP recovery rule stays stable.

## Unsafe baseline

Two independent `READ COMMITTED` connections both observed:

```text
state   = ABSENT
version = 100
```

They then performed unconditional mutations.

Observed result:

```text
Node A → unconditional commit → version 101 → effect #1
Node B → unconditional commit → version 102 → effect #2
```

Final state:

```text
COMMITTED / version=102 / effects=2
```

This reproduces the same missing-precondition hazard as Report #012.

## Safe matrix

Every safe case used two independent connections at the same isolation level. Both transactions first observed the same legal snapshot:

```text
ABSENT / version=100
```

Both then raced on the same version-bound mutation:

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

Only a transaction receiving a returned row was allowed to insert the corresponding effect in the same database transaction.

### READ COMMITTED

Observed loser signal:

```text
transition = PRECONDITION_FAILED
SQLSTATE   = none
UPDATE     = 0 rows
```

The winning transaction committed:

```text
COMMITTED / version=101 / effects=1
```

The stale writer then performed a fresh authoritative reread and observed the same committed state.

### REPEATABLE READ

Observed loser signal:

```text
transition = SERIALIZATION_FAILURE
SQLSTATE   = 40001
```

The stale transaction was rolled back. A fresh reconciliation connection then observed:

```text
COMMITTED / version=101 / effects=1
```

### SERIALIZABLE

Observed loser signal:

```text
transition = SERIALIZATION_FAILURE
SQLSTATE   = 40001
```

Again, the failed transaction was rolled back and reconciliation through a fresh transaction observed:

```text
COMMITTED / version=101 / effects=1
```

## Matrix

| Isolation level | Winning writer | Losing signal | SQLSTATE | Final effects |
|---|---|---|---|---:|
| READ COMMITTED | commit | conditional update matched 0 rows | — | 1 |
| REPEATABLE READ | commit | serialization failure | `40001` | 1 |
| SERIALIZABLE | commit | serialization failure | `40001` | 1 |

All three safe paths preserved the same final invariant while exposing different conflict signals.

## The retry law

A database-level serialization failure is not equivalent to business-level permission to repeat the consequential action.

The TTP handling rule is:

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

In this benchmark, every losing path reconciled to `COMMITTED / version=101 / effects=1`, so no business retry was legal or necessary.

This distinction matters because PostgreSQL documentation correctly tells applications using Repeatable Read or Serializable to retry failed transactions from the beginning. TTP adds the application-level rule that the beginning of that retry must include fresh state/evidence/authorization, rather than blindly replaying the mutation payload.

## New invariant

# **RETRYABLE TRANSACTION ≠ RETRYABLE BUSINESS ACTION**

and:

# **DATABASE CONFLICT SIGNAL → RECONCILE BUSINESS STATE BEFORE RE-EXECUTION**

The signal may be:

```text
0 rows updated
```

or:

```text
SQLSTATE 40001
```

but neither signal alone establishes that the intended effect is absent.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Real PostgreSQL + unsafe duplicate baseline | PASS | 2/2 |
| READ COMMITTED → one winner + zero-row stale writer | PASS | 2/2 |
| REPEATABLE READ → one winner + `40001` | PASS | 2/2 |
| SERIALIZABLE → one winner + `40001` | PASS | 2/2 |
| TTP reconciliation preserved one effect across matrix | PASS | 2/2 |
| **Total** |  | **10/10** |

## Interpretation boundary

This report validates one deterministic concurrency shape against PostgreSQL 17.6. It does **not** prove or certify:

- every concurrency pattern at these isolation levels;
- every PostgreSQL release or configuration;
- transaction retry correctness for arbitrary application logic;
- failover, replication lag, distributed transactions or network partitions;
- external API effects coordinated with PostgreSQL;
- exactly-once semantics in arbitrary systems;
- arbitrary agent safety.

The operation and effect tables are synthetic. PostgreSQL and the concurrent connections are real.

## Reproducibility

Benchmark specification:

`benchmarks/postgresql-isolation-matrix-v1.0/README.md`

Harness:

`benchmarks/postgresql-isolation-matrix-v1.0/run_isolation_matrix.py`

Workflow:

`.github/workflows/benchmark-postgresql-isolation-matrix.yml`

Machine-readable result:

`reports/verified/013-postgresql-isolation-matrix/result.json`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31463056442`

PostgreSQL reference documentation:

`https://www.postgresql.org/docs/17/transaction-iso.html`

## Verdict

**PostgreSQL 17.6 exposed two different stale-writer signal classes for the same TTP race: READ COMMITTED produced a zero-row conditional update, while REPEATABLE READ and SERIALIZABLE produced SQLSTATE 40001 serialization failures. In every safe path, fresh reconciliation observed `COMMITTED / version=101 / effects=1`, showing that a retryable database transaction does not by itself make the consequential business action retryable.**

---

**RESONANCE Verified Report #013**  
**Status:** Reproducible PostgreSQL isolation-level matrix  
**Score:** 10/10  
**Unsafe effects:** 2  
**Safe effects per isolation level:** 1  
**Vulnerability claim:** No  
**External safety certification:** No
