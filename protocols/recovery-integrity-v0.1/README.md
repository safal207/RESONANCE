# Recovery Integrity Protocol v0.1

Recovery Integrity v0.1 is a small, falsifiable contract for crash/restart recovery in agentic and stateful systems.

It separates:

```text
durable authority
≠
derived projection
≠
execution continuation
```

The protocol exists to prevent a common failure mode: several stores are each locally readable, but belong to different logical generations or imply different recovery decisions.

## Decisions

Projection recovery:

- `ALLOW_REBUILD`
- `NO_REBUILD`
- `HOLD`

Execution recovery:

- `ALLOW_FORK`
- `NO_CONTINUATION`
- `HOLD`

`ALLOW_REBUILD` never implies `ALLOW_FORK`.

## Minimum recovery states

Projection state:

- `HEALTHY`
- `MISSING`
- `STALE`
- `CORRUPT`
- `UNPROVABLE`

Integrity state:

- `VALID`
- `INVALID`
- `UNKNOWN`

Continuation proof:

- `PROVEN`
- `NOT_PROVEN`
- `CONTRADICTED`

## Load-bearing invariants

1. **Projection is not authority.** A cache, sidebar, index, or JSON projection must not silently redefine authoritative record existence.
2. **Readable is not current.** A parseable projection may still be stale.
3. **Missing, stale, and corrupt are distinct.**
4. **Evidence survives repair.** The disputed pre-recovery artifact must be preservable/addressable before mutation.
5. **Rebuild and continuation are separate decisions.**
6. **Safe continuation requires proof.** `ALLOW_FORK` requires `rollout.continuation_proof == PROVEN`.
7. **Ambiguous pending effects fail closed.** Unknown/ambiguous external side effects cannot produce `ALLOW_FORK`.
8. **Current authority dominates recovered authority.** When mutation authority is dynamic, recovery must revalidate it rather than resurrect it from a checkpoint.
9. **Observed outcome is recorded separately from the pre-recovery verdict.**
10. **Generation mismatch is explicit.** When both authority and projection generations are known and differ, the projection cannot be `HEALTHY`.
11. **Projection-newer-than-authority fails closed.** A projection at generation `N+1` with apparent durable authority at `N` is `UNPROVABLE`; recovery must not rebuild from the apparently older source until the contradiction is reconciled.
12. **Pre-commit crash must not invent a committed generation.** A transaction interrupted before durable authority commit remains at the prior generation.
13. **Post-commit projection lag is stale, not missing history.** Once authority generation `N+1` commits while projection remains at `N`, the projection is rebuildable but execution remains independently gated.
14. **Orphan temp state is evidence, not authority.** A fully fsynced temporary projection that was never renamed does not silently replace the last committed projection.

## Files

- `schema/recovery-integrity-record.schema.json` — structural JSON Schema.
- `validate.py` — semantic invariant validator with no third-party dependencies.
- `generation_crash_simulator.py` — deterministic Generation-N crash-state classifier and verdict simulator.
- `test_generation_crash_simulator.py` — regression tests for the generation matrix and fail-closed boundaries.
- `fault_injection_harness.py` — real SQLite + atomic JSON process-crash harness using child-process termination at durability boundaries.
- `test_fault_injection_harness.py` — regressions over the observed on-disk crash states.
- `fixtures/codex-26990-sanitized.json` — first public sanitized fixture based only on public GitHub evidence.
- `fixtures/unsafe-fork-must-fail.json` — negative continuation control.
- `fixtures/generation-matrix.expected.txt` — pinned canonical simulator output.
- `fixtures/process-crash-matrix.expected.txt` — pinned canonical on-disk process-crash matrix.

## Validate the public fixture

```bash
python protocols/recovery-integrity-v0.1/validate.py \
  protocols/recovery-integrity-v0.1/fixtures/codex-26990-sanitized.json
```

Expected:

```text
PASS recovery-integrity-v0.1
projection=STALE
projection_decision=ALLOW_REBUILD
execution_decision=HOLD
```

## Generation-N crash simulator

The simulator makes generation drift falsifiable without depending on a vendor implementation.

Canonical matrix:

```text
case             projection    rebuild          execution
healthy          HEALTHY       NO_REBUILD       HOLD
stale            STALE         ALLOW_REBUILD    HOLD
corrupt          CORRUPT       ALLOW_REBUILD    HOLD
split-generation UNPROVABLE    HOLD             HOLD
```

Run:

```bash
cd protocols/recovery-integrity-v0.1
python generation_crash_simulator.py
python -m unittest -v test_generation_crash_simulator.py
```

The split-generation case is intentionally asymmetric:

```text
authority generation 41
projection generation 42
        ↓
UNPROVABLE
        ↓
HOLD
```

The verifier does **not** assume the projection is wrong and overwrite it from the apparently older authority. That contradiction must be reconciled first.

## Real process-crash fault injection

`fault_injection_harness.py` advances a real SQLite authority row and an atomically written JSON projection from generation 1 to generation 2. The mutation runs in a child process and calls `os._exit(91)` at selected boundaries. A fresh parent verifier then inspects the actual files and SQLite state left on disk.

The SQLite lane uses WAL plus `synchronous=FULL`. The projection lane uses:

```text
write projection.json.tmp
        ↓
flush + fsync(temp)
        ↓
os.replace(temp, projection.json)
        ↓
fsync(directory) where supported
```

Canonical observed matrix:

```text
crash point                         authority projection state    rebuild
before authority commit             1         1          HEALTHY  NO_REBUILD
after authority commit              2         1          STALE    ALLOW_REBUILD
after projection temp fsync         2         1          STALE    ALLOW_REBUILD
after full projection commit        2         2          HEALTHY  NO_REBUILD
```

The temp-fsync case additionally requires the orphan `projection.json.tmp` candidate to remain observable while the committed projection stays at generation 1.

Run:

```bash
cd protocols/recovery-integrity-v0.1
python fault_injection_harness.py matrix
python -m unittest -v test_fault_injection_harness.py
```

Every observed state is converted into a `RecoveryIntegrityRecord` and passed through the same semantic validator. The harness performs classification only; it does not rebuild the projection or allow execution continuation.

### Evidence boundary

This is **process-crash fault injection**, not proof of arbitrary physical power-loss durability. `os._exit()` proves behavior across abrupt process termination with real SQLite/filesystem operations. It does not model drive write caches, controller reordering, filesystem-specific power-fail behavior, torn sectors, or all Windows directory-fsync semantics.

Therefore:

```text
process-crash PASS
≠
power-loss durability proven
```

A stronger future lane needs VM/filesystem/storage fault injection or a product-native crash harness with explicit durability guarantees.

## Regression boundaries

The suites verify that:

- forcing `ALLOW_REBUILD` across a projection-newer-than-authority split is rejected;
- a valid projection rebuild does not grant `ALLOW_FORK`;
- unknown side effects and unproven current authority keep execution fail-closed;
- a pre-commit SQLite crash does not advance authority generation;
- a post-commit/pre-projection crash becomes `STALE`, not `HEALTHY`;
- an fsynced-but-unrenamed temp projection does not become the committed projection;
- a fully committed projection restores generation alignment.

## CI proof lane

`.github/workflows/recovery-integrity-v0.1.yml` runs the full boundary on relevant pull requests and `main` changes:

```text
sanitized public fixture must PASS
unsafe fork fixture must FAIL
Generation-N matrix must PASS
generation regressions must PASS
SQLite + atomic JSON process-crash matrix must PASS
process-crash regressions must PASS
```

This makes both negative controls and real crash-boundary observations part of the acceptance contract rather than optional manual checks.

## Non-goals

This contract does not decide which store is authoritative for a product. That is a product-specific declaration backed by native evidence.

It does not claim full power-loss safety, distributed consensus, hardware fault tolerance, or vendor adoption. The semantic validator, generation simulator, and recovery verifier are read-only; the fault-injection child mutates only its isolated test fixture and never a product recovery target.
