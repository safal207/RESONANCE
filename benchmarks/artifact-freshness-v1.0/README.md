# RESONANCE Artifact Freshness / Stale-but-Valid Result Benchmark v1.0

Verified #023 separated useful stale-worker output from current execution authority. #024 asks a different question: even when the current owner explicitly adopts an immutable artifact, is the artifact still applicable to the state that exists now?

## Core invariant

**INTEGRITY + PROVENANCE ≠ CURRENT APPLICABILITY.**

An artifact can have a correct digest, known producer provenance and a valid current adopter while still being computed against a superseded input-state version.

## Deterministic model

- PostgreSQL stores current business state, ownership lease and result artifacts.
- Business state starts at version `100` with value `10`.
- Worker A is authorized and computes an artifact from v100: `output = 2 * value = 20`.
- Before adoption, business state advances to version `101` with value `20`.
- The currently applicable output is therefore `40`.
- Artifact A remains byte-for-byte valid and retains exact producer/input provenance, but its `input_state_version=100` is stale.
- A Dockerized HTTP resource records consequential commits.

## Unsafe path

Current owner B adopts the exact stale artifact by checking digest/provenance/ownership but **not** current input-state version.

```text
state v100 / value 10
      ↓
A computes D100 / output 20
      ↓
state advances to v101 / value 20
      ↓
B adopts D100 without applicability comparison
      ↓
commit output 20 against current v101
      ↓
STALE CONSEQUENCE
```

Integrity succeeds. Provenance succeeds. Current-owner authority succeeds. Applicability fails.

## Safe path

Adoption compares the artifact's bound input state to the current authoritative state inside the adoption transaction.

```text
artifact.input_version = 100
current.version = 101
→ adoption rows = 0
→ APPPLICABILITY_CONFLICT
→ no external effect
→ recompute D101
→ adopt D101 under current owner
→ commit output 40 once
```

The benchmark also binds the input snapshot digest, not version alone.

## Control

When business state has not advanced, an artifact computed on the current version is adopted and committed normally.

## Score

Five checks × 2 points = 10.

1. Artifact is integrity/provenance-valid and explicitly bound to input state v100.
2. State advances to v101 and blind adoption of D100 commits a stale consequence.
3. Applicability-aware adoption rejects D100 with zero rows and no effect.
4. Recompute on v101 produces/adopts/commits the currently applicable result once.
5. Unchanged-state control succeeds normally.

## Interpretation boundary

This is a deterministic local protocol benchmark. It does not claim that every version change invalidates every artifact. Domain-specific systems may prove that a result remains applicable across selected state changes. The safety requirement is that such applicability be explicit and evidenced rather than inferred from artifact integrity or provenance alone.
