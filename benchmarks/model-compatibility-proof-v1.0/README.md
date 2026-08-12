# RESONANCE Model Compatibility Proof Benchmark v1.0

Verified #027 established that an artifact valid under an older causal model cannot silently inherit authority after the authoritative model changes. This benchmark asks when an older artifact may still be safely reused without recomputation.

## Models

```text
model-v1: y = min(limit, 2 × price)
model-v2: y = min(limit, 2 × price + tax_rate)
```

The models are **not globally equivalent**. But for a scoped state satisfying:

```text
tax_rate >= 0
AND
2 × price >= limit
```

both models necessarily return `limit`.

## Compatibility proof object

A compatibility proof binds:

- `from_model_version` + digest
- `to_model_version` + digest
- proof rule identity + digest
- exact artifact digest
- current dependency/value fingerprint
- evaluated predicate result
- current owner/fencing epoch at adoption

A bare `compatible=true` flag is intentionally insufficient.

## Cases

1. **Scoped compatibility success** — v1 artifact output `30`, current v2 state also implies `30`; proof predicate holds, adoption succeeds without recompute, exactly one effect.
2. **Unsafe global compatibility claim** — same v1→v2 pair on state where predicate is false; old output `20` is silently committed while v2 requires `28`.
3. **Safe out-of-scope rejection** — proof predicate false → zero-row adoption, zero effects; recomputation under v2 commits `28` once.
4. **Proof-binding tamper** — wrong target model digest or wrong artifact digest is rejected even when the semantic predicate would otherwise hold.
5. **No-drift/current-model control** — a current v2 artifact commits normally.

## Core law

> **MODEL VERSION MISMATCH ≠ AUTOMATIC INCOMPATIBILITY — COMPATIBILITY ITSELF MUST BE PROVED.**

The benchmark is deterministic protocol research, not production safety certification.