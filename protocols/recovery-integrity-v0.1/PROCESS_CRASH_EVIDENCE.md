# Recovery Integrity v0.1 — Process-Crash Evidence

This note records the first executable on-disk crash evidence for Recovery Integrity v0.1.

## Subject

A real local fixture composed of:

```text
SQLite authority store
+
atomic JSON projection
```

The authority store runs with SQLite WAL and `synchronous=FULL`.

The projection path is:

```text
projection.json.tmp
  → flush
  → fsync(temp)
  → os.replace(..., projection.json)
  → fsync(directory) where supported
```

A child process advances generation 1 → 2 and terminates with `os._exit(91)` at a selected boundary. A fresh verifier then inspects the actual post-crash files and SQLite state.

## Observed boundaries

```text
crash point                         auth proj projection rebuild          temp
--------------------------------------------------------------------------------
before_authority_commit             1    1    HEALTHY    NO_REBUILD       false
after_authority_commit              2    1    STALE      ALLOW_REBUILD    false
after_projection_temp_fsync         2    1    STALE      ALLOW_REBUILD    true
after_projection_commit             2    2    HEALTHY    NO_REBUILD       false
```

All four observations are converted into `RecoveryIntegrityRecord` objects and pass the semantic validator while keeping `execution_continuation=HOLD`.

## What this proves

The harness mechanically distinguishes:

1. a transaction interrupted before authority commit from a committed generation;
2. a committed authority generation from a lagging projection;
3. an fsynced temporary projection candidate from the committed projection path;
4. restored generation alignment after the projection commit completes.

It also demonstrates the recovery rule:

```text
authority commit succeeded
+
projection commit did not
→ projection STALE
→ ALLOW_REBUILD
→ execution HOLD
```

## What this does not prove

This is process-crash evidence, not arbitrary physical power-loss proof.

```text
os._exit process crash
≠
storage-controller power failure
≠
filesystem guarantee under every platform
≠
torn-sector simulation
```

The harness is intentionally bounded. A future storage/power-loss lane should introduce a VM, filesystem, or product-native failure injector with explicit durability semantics.

## Reproduce

```bash
cd protocols/recovery-integrity-v0.1
python fault_injection_harness.py matrix
python -m unittest -v test_fault_injection_harness.py
```

CI runs both commands as part of the Recovery Integrity acceptance contract.
