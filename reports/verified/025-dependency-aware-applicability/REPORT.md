# RESONANCE Verified Report #025

# Dependency-Aware Applicability / Relevant vs Irrelevant State Drift

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Dependency-Aware Applicability v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource with persistent SQLite effect state  
**GitHub Actions run:** `31582719421`  
**Evidence artifact:** `resonance-dependency-aware-applicability-v1.0`  
**Artifact ID:** `9135817141`  
**Artifact digest:** `sha256:b0f6a68a5cb0a2aaff3672fb28b734645a10c65f4d100da7250a45c3fdf66505`

## Result

# **10 / 10 — Dependency-aware applicability protocol passes**

Verified #024 established that integrity, provenance and current authority do not prove current applicability. Report #025 asks the next question:

> Must every global state-version change invalidate a result, or only changes in the state that causally justified that result?

The benchmark separates **global drift** from **relevant dependency drift**.

# **STATE CHANGED ≠ RELEVANT STATE CHANGED**

## Causal model

```text
result
├─ depends_on → price
├─ depends_on → limit
└─ does_not_depend_on → theme
```

The deterministic computation is:

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

The artifact records a dependency fingerprint over only the declared causal inputs `price` and `limit`.

## Irrelevant drift: global version changed, result did not

The benchmark changed only:

```text
theme: light → dark
global_version: 100 → 101
```

But the dependency fingerprint stayed identical and the expected result remained `20`.

A strict global-version rule returned:

```text
updated_rows = 0
reason = global_version_conflict
```

The dependency-aware rule instead observed that the state subgraph that justified the result was unchanged:

```text
dependency fingerprint: unchanged
adoption rows = 1
HTTP 200 / applied
final effect_count = 1
committed output = 20
```

This demonstrates that a global version mismatch can be a useful conservative signal without being proof that the result is invalid.

## Relevant drift: blind adoption commits a stale result

Next, the benchmark changed a causal input:

```text
price: 10 → 20
global_version: 100 → 101
```

The dependency fingerprint changed and the current expected output became:

```text
min(30, 2 × 20) = 30
```

Blind current-owner adoption ignored the dependency mismatch:

```text
old artifact output = 20
current expected output = 30
adoption rows = 1
HTTP 200 / applied
committed output = 20
```

The owner and fence were current. The artifact was still intact. The failure was causal applicability.

## Safe: compare the causal dependency fingerprint

For the same price drift, dependency-aware adoption returned:

```text
updated_rows = 0
reason = dependency_conflict
external effects before recompute = 0
```

The current owner then recomputed against the current dependency set:

```text
price = 20
limit = 30
output = 30
fresh dependency fingerprint = current fingerprint
```

The fresh artifact was adopted and committed exactly once:

```text
fresh adoption rows = 1
HTTP 200 / applied
final effect_count = 1
final output = 30
```

## Second relevant dependency: limit drift

The benchmark also changed:

```text
limit: 30 → 15
price remains 10
```

Current expected output became `15`. The fingerprint changed and the old artifact was rejected:

```text
updated_rows = 0
reason = dependency_conflict
external effects = 0
```

The guard therefore tracks the declared causal subgraph, not one hand-picked field.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Irrelevant theme drift changed global version but preserved dependency fingerprint and applicability | PASS | 2/2 |
| Strict global-version equality rejected a still-applicable artifact | PASS | 2/2 |
| Blind adoption after relevant price drift committed stale output 20 instead of current 30 | PASS | 2/2 |
| Dependency fingerprint rejected both price and limit drift | PASS | 2/2 |
| Recompute on current dependencies committed one current effect | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I59 — STATE CHANGED DOES NOT IMPLY RELEVANT STATE CHANGED**

A state transition outside the result's causal dependency set does not automatically invalidate the result.

# **I60 — APPLICABILITY SHOULD BIND TO THE STATE SUBGRAPH THAT CAUSALLY JUSTIFIED THE RESULT**

For consequential state-sensitive work, the proof SHOULD preserve a declared dependency set and a stable identity/fingerprint of the dependency values used for computation.

# **I61 — GLOBAL VERSION MISMATCH MAY BE A CONSERVATIVE SIGNAL, NOT PROOF OF INVALIDITY**

A coarse global version is useful for detecting that something changed. A more precise applicability decision may require determining whether the changed state intersects the result's causal dependencies.

# **I62 — RELEVANT DEPENDENCY DRIFT REQUIRES REVALIDATION, RECOMPUTATION, OR DOMAIN PROOF BEFORE CONSEQUENCE**

If the current dependency identity differs from the one that justified computation, blind adoption is not sufficient.

## TTP dependency-aware applicability rule

```text
DECLARE RESULT DEPENDENCIES
price + limit
        ↓
CAPTURE DEPENDENCY VALUES
        ↓
COMPUTE DEPENDENCY FINGERPRINT F
        ↓
COMPUTE ARTIFACT D
        ↓
GLOBAL STATE CHANGES
        ↓
OBSERVE CURRENT DEPENDENCY SUBGRAPH
        ↓
COMPARE F
   ├─ same → artifact may remain applicable
   └─ different / unknown → REVALIDATE / RECOMPUTE / HOLD
        ↓
CURRENT AUTHORITY ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE DEPENDENCIES → ARTIFACT → APPLICABILITY → EFFECT
```

## Relationship to #024–#025

```text
#024 → current applicability must be proved against current state
#025 → applicability can be scoped to the causal state subgraph that actually justified the result
```

The broader rule becomes:

```text
CAUSAL APPLICABILITY =
  declared dependency set
+ dependency-value identity / fingerprint
+ current dependency comparison
+ current-owner adoption
+ current fencing authority
+ end-to-end evidence
```

## Interpretation boundary

The dependency set in this benchmark is explicitly declared by the test. The fingerprint proves equality of the **declared dependency values**; it does not prove that the dependency model is complete or correct.

This benchmark does **not** provide:

- automatic causal-dependency discovery;
- proof that omitted state cannot affect the result;
- a universal invalidation algorithm;
- production safety certification;
- a vulnerability claim against PostgreSQL or another external product;
- arbitrary agent safety.

That limitation is important: a perfectly computed fingerprint over an incomplete dependency set can still authorize an invalid result.

## Reproducibility

Benchmark: `benchmarks/dependency-aware-applicability-v1.0/`  
Workflow: `.github/workflows/benchmark-dependency-aware-applicability.yml`  
Machine-readable summary: `reports/verified/025-dependency-aware-applicability/result.json`  
GitHub Actions: `31582719421`

## Verdict

**Changing an irrelevant field (`theme`) advanced the global state version without changing the dependency fingerprint or correct output; a strict global-version rule rejected useful work while dependency-aware adoption safely preserved it. Changing relevant inputs (`price` or `limit`) changed the dependency fingerprint; blind adoption committed a stale result, while dependency-aware adoption rejected it and recomputation committed the current result exactly once.**

---

**RESONANCE Verified Report #025**  
**Score:** 10/10  
**Irrelevant drift:** global 100 → 101 / output remains 20 / dependency-aware adoption succeeds  
**Relevant price drift:** expected 20 → 30 / blind commit = 20 / safe stale-adoption rows = 0  
**Relevant limit drift:** expected 20 → 15 / safe stale-adoption rows = 0  
**Vulnerability claim:** No  
**External safety certification:** No
