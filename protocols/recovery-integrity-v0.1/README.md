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

## Files

- `schema/recovery-integrity-record.schema.json` — structural JSON Schema.
- `validate.py` — semantic invariant validator with no third-party dependencies.
- `fixtures/codex-26990-sanitized.json` — first public sanitized fixture based only on public GitHub evidence.

## Validate

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

## Non-goals

This contract does not decide which store is authoritative for a product. That is a product-specific declaration backed by native evidence.

It also does not mutate any recovery target. The validator is read-only.
