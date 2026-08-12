# RESONANCE Dependency Contract Drift / Model Version Race v1.0

Verified #026 showed that an applicability fingerprint is unsafe if its dependency model is incomplete. #027 asks the temporal question underneath that rule:

> What if the dependency model was authoritative and valid when the artifact was computed, but the authoritative model changes before adoption?

## Core invariant

**MODEL VALID THEN ≠ MODEL VALID NOW**

## Deterministic model transition

Business state is held constant:

```text
price = 10
limit = 30
tax_rate = 2
theme = light
```

At artifact production time the authoritative model is:

```text
model-v1
manifest = price + limit
output = min(limit, 2 × price) = 20
```

Before adoption, only the authoritative causal contract changes:

```text
model-v2
manifest = price + limit + tax_rate
output = min(limit, 2 × price + tax_rate) = 22
```

No business input changed. The artifact remains intact and was valid under model-v1 when produced.

## Unsafe path

Validate the old artifact only against the model identity carried by the artifact itself. Since `price` and `limit` are unchanged, its v1 dependency fingerprint still matches and the current owner can commit output `20` even though the current authoritative model requires `22`.

## Safe path

At adoption, compare the artifact's bound model identity/version/digest against the **current authoritative model** before comparing dependency values. A mismatch is model drift evidence and must yield HOLD / REVALIDATE / RECOMPUTE unless an explicit compatibility proof exists.

## Score

Five checks × 2 points:

1. v1 artifact was valid at production; only model identity changes before adoption.
2. Artifact-bound validation accepts the old model and commits stale output `20`.
3. Current-model validation rejects old model identity with zero effects.
4. Recompute under v2 commits current output `22` exactly once.
5. Control: when model-v1 remains current, normal current-model adoption succeeds.

This benchmark is deterministic and local. It uses PostgreSQL as the coordination/model registry and a separate Dockerized HTTP resource as the consequential effect boundary.