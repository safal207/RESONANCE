# RESONANCE Benchmark — Incomplete Causal Graph v1.0

Verified #025 showed that applicability can be scoped to the state subgraph that causally justifies a result. This benchmark tests the failure immediately underneath that idea: **what if the declared subgraph is incomplete?**

## Claim under test

> **A CORRECT FINGERPRINT OVER AN INCOMPLETE DEPENDENCY SET IS STILL UNSAFE.**

Synthetic business rule:

```text
output = min(limit, 2 × price + tax_rate)
```

The unsafe artifact incorrectly declares only:

```text
price + limit
```

while the authoritative dependency contract is:

```text
price + limit + tax_rate
```

`theme` is intentionally irrelevant.

## Scenarios

1. **Omitted dependency drift** — `tax_rate` changes from 2 to 8. The artifact's declared fingerprint over `price + limit` remains identical, but the correct output changes from 22 to 28.
2. **Blind declared-set adoption** — current owner B trusts only the artifact's declared dependency fingerprint and commits stale output 22.
3. **Manifest-aware rejection** — adoption compares the artifact dependency manifest with the authoritative dependency contract and returns zero rows before consequence.
4. **Complete recomputation** — B recomputes with `price + limit + tax_rate`, adopts under the current contract, and commits output 28 exactly once.
5. **Irrelevant drift control** — changing only `theme` preserves the complete dependency fingerprint and remains applicable.

## Scope

This benchmark uses PostgreSQL for business/adoption state and reuses the separate Dockerized HTTP effect boundary from Verified #025. The authoritative dependency contract is declared by the benchmark; this does not perform automatic causal discovery.
