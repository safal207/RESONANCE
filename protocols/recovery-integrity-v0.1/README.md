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

## Files

- `schema/recovery-integrity-record.schema.json` — structural JSON Schema.
- `validate.py` — semantic invariant validator with no third-party dependencies.
- `generation_crash_simulator.py` — deterministic Generation-N crash-state classifier and verdict simulator.
- `test_generation_crash_simulator.py` — regression tests for the generation matrix and fail-closed boundaries.
- `fixtures/codex-26990-sanitized.json` — first public sanitized fixture based only on public GitHub evidence.
- `fixtures/unsafe-fork-must-fail.json` — negative continuation control.
- `fixtures/generation-matrix.expected.txt` — pinned canonical simulator output.

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

The regression suite also verifies that:

- forcing `ALLOW_REBUILD` across this split is rejected;
- a valid projection rebuild does not grant `ALLOW_FORK`;
- unknown side effects and unproven current authority keep execution fail-closed.

## CI proof lane

`.github/workflows/recovery-integrity-v0.1.yml` runs the full boundary on relevant pull requests and `main` changes:

```text
sanitized public fixture must PASS
unsafe fork fixture must FAIL
Generation-N matrix must PASS
regression suite must PASS
```

This makes the negative control part of the acceptance contract rather than an optional manual check.

## Non-goals

This contract does not decide which store is authoritative for a product. That is a product-specific declaration backed by native evidence.

It also does not mutate any recovery target. The validator and simulator are read-only.
