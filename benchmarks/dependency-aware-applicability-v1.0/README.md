# RESONANCE Dependency-Aware Applicability Benchmark v1.0

Verified Report #025 tests whether an artifact can remain applicable across **irrelevant** state drift while being rejected when a **causal dependency** changes.

## Causal model

```text
result
├─ depends_on → price
├─ depends_on → limit
└─ does_not_depend_on → theme
```

Computation is deliberately simple:

```text
output = min(limit, 2 × price)
```

Initial state:

```text
global_version = 100
price = 10
limit = 30
theme = light
output = 20
```

The artifact stores both a global state version and a dependency fingerprint over only `price` and `limit`.

## Scenarios

1. **Irrelevant drift:** `theme: light → dark`, global version `100 → 101`. Dependency fingerprint is unchanged. Strict global-version equality rejects useful work; dependency-aware adoption accepts it.
2. **Relevant drift:** `price: 10 → 20`, global version `101 → 102`. Dependency fingerprint changes and current expected output becomes `30`. Blind adoption commits stale output `20`; dependency-aware adoption rejects it.
3. **Second relevant dependency:** `limit: 30 → 15` with price unchanged. Dependency fingerprint changes and old artifact is rejected.
4. **Recompute:** current owner recomputes from the current dependency set, adopts, and commits one current effect.

## Invariants under test

- **STATE CHANGED ≠ RELEVANT STATE CHANGED.**
- **APPLICABILITY SHOULD BIND TO THE STATE SUBGRAPH THAT CAUSALLY JUSTIFIED THE RESULT.**
- **GLOBAL VERSION MISMATCH MAY BE A CONSERVATIVE SIGNAL, NOT PROOF OF INVALIDITY.**
- **DEPENDENCY FINGERPRINT MISMATCH REQUIRES REVALIDATION, RECOMPUTATION, OR DOMAIN PROOF BEFORE CONSEQUENCE.**

This is a deterministic local protocol benchmark, not a universal dependency-discovery algorithm or production safety certification.
