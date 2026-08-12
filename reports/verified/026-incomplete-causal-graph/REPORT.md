# RESONANCE Verified Report #026

# Missing Dependency / Incomplete Causal Graph

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Incomplete Causal Graph v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**GitHub Actions run:** `31583719848`  
**Evidence artifact:** `resonance-incomplete-causal-graph-v1.0`  
**Artifact ID:** `9136209133`  
**Artifact digest:** `sha256:6bbe0b9a78e19ea9933f3389b3c9d99e7931b2d5d87b183b9d950aaaf8930f48`

## Result

# **10 / 10 — Incomplete causal graph protocol passes**

Verified #025 showed that applicability can be narrowed from coarse global state to the causal dependency subgraph that actually justifies a result. Report #026 tests the assumption underneath that optimization:

> What if the dependency subgraph itself is wrong because a real causal input was omitted?

# **A CORRECT FINGERPRINT OVER AN INCOMPLETE DEPENDENCY SET IS STILL UNSAFE**

## Ground-truth computation

```text
output = min(limit, 2 × price + tax_rate)
```

Authoritative dependency contract:

```text
price + limit + tax_rate
```

Unsafe artifact manifest:

```text
price + limit
```

`tax_rate` is omitted. `theme` is irrelevant.

## Omitted dependency drift

Initial state:

```text
price = 10
limit = 30
tax_rate = 2
theme = light
output = 22
```

The artifact correctly fingerprints its declared dependency set `price + limit`.

Then only the omitted causal input changes:

```text
tax_rate: 2 → 8
global_version: 100 → 101
```

The incomplete fingerprint remains exactly unchanged because neither `price` nor `limit` changed. But the authoritative fingerprint changes and the correct output becomes:

```text
min(30, 2 × 10 + 8) = 28
```

The artifact is internally consistent with its declared model. The model is incomplete.

## Unsafe: trust the declared fingerprint only

Current owner B/fence 2 compares only the artifact's declared dependency fingerprint against current values for the declared fields.

```text
artifact manifest = price + limit
artifact fingerprint = current fingerprint
→ adoption rows = 1
→ HTTP 200 / applied
→ committed output = 22
```

Current correct output was already `28`.

This is a model-completeness failure, not a hash failure, integrity failure, stale-owner failure or resource-fencing failure.

## Safe: validate dependency-set identity first

The safe path treats the dependency manifest itself as applicability evidence.

Before comparing values, adoption compares:

```text
artifact dependency manifest
against
authoritative dependency contract
```

For the stale/incomplete artifact:

```text
artifact:      price + limit
authoritative: price + limit + tax_rate

→ dependency_manifest_conflict
→ adoption rows = 0
→ external effects = 0
```

The current owner then recomputes using the complete dependency contract:

```text
price = 10
limit = 30
tax_rate = 8
output = 28
```

The complete artifact is adopted under B/fence 2 and committed once:

```text
adoption rows = 1
HTTP 200 / applied
final effect_count = 1
final output = 28
```

## Irrelevant-drift control

A complete artifact using `price + limit + tax_rate` was also tested against a change in only:

```text
theme: light → dark
global_version: 100 → 101
```

The authoritative dependency fingerprint remained unchanged, adoption succeeded and output `22` committed once. The manifest-aware rule therefore does not collapse back into coarse global invalidation.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Omitted tax drift preserved incomplete fingerprint while correct output changed 22 → 28 | PASS | 2/2 |
| Declared-only guard accepted incomplete model and committed stale output 22 | PASS | 2/2 |
| Authoritative dependency manifest rejected omitted causal input with zero effects | PASS | 2/2 |
| Complete recomputation committed current output 28 exactly once | PASS | 2/2 |
| Complete model remained applicable across irrelevant theme drift | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I63 — A CORRECT FINGERPRINT OVER AN INCOMPLETE DEPENDENCY SET IS STILL UNSAFE**

Cryptographic or deterministic correctness of a fingerprint says nothing about causal completeness of the fields included in it.

# **I64 — DEPENDENCY-SET IDENTITY IS PART OF APPLICABILITY EVIDENCE**

A consequential artifact should preserve not only dependency values, but also the identity/version/digest of the dependency model that selected those values.

# **I65 — ADOPTION MUST VALIDATE THE DEPENDENCY MANIFEST, NOT ONLY THE FINGERPRINT VALUES**

If the artifact's declared causal inputs do not match an authoritative or independently validated dependency contract, a matching value fingerprint is insufficient authorization for consequence.

# **I66 — OMITTED OR UNKNOWN CAUSAL INPUT REQUIRES REVALIDATION, RECOMPUTATION, OR HOLD BEFORE CONSEQUENCE**

Unknown model completeness should fail closed for consequential adoption unless domain-specific evidence proves the omission cannot affect the result.

## TTP causal-model completeness rule

```text
DECLARE / RESOLVE DEPENDENCY CONTRACT M
            ↓
CAPTURE MANIFEST IDENTITY hash(M)
            ↓
CAPTURE DEPENDENCY VALUES
            ↓
COMPUTE VALUE FINGERPRINT F
            ↓
COMPUTE ARTIFACT D
            ↓
AT ADOPTION:
COMPARE MANIFEST IDENTITY
   ├─ mismatch / unknown → HOLD / REVALIDATE MODEL
   └─ match              → COMPARE DEPENDENCY VALUES
                              ├─ mismatch → RECOMPUTE / PROVE
                              └─ match    → eligible to adopt
            ↓
CURRENT AUTHORITY ADOPTS
            ↓
FENCED COMMIT
            ↓
PROVE MODEL → VALUES → ARTIFACT → EFFECT
```

## Relationship to #024–#026

```text
#024 → prove current applicability
#025 → scope applicability to the relevant causal subgraph
#026 → prove that the causal subgraph itself is complete enough for the decision
```

The broader model becomes:

```text
CAUSAL APPLICABILITY =
  dependency-model identity
+ dependency-model validity / completeness evidence
+ dependency-value fingerprint
+ current dependency comparison
+ current authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The authoritative dependency contract in this benchmark is supplied by the test. This is **not automatic causal discovery** and does not prove a production model is complete. Rather, the benchmark demonstrates why model identity/completeness must be treated as a separate verification surface.

It does not claim production safety certification, arbitrary agent safety, exactly-once execution, or a vulnerability in PostgreSQL or another external product.

## Reproducibility

Benchmark: `benchmarks/incomplete-causal-graph-v1.0/`  
Workflow: `.github/workflows/benchmark-incomplete-causal-graph.yml`  
Machine summary: `reports/verified/026-incomplete-causal-graph/result.json`  
GitHub Actions: `31583719848`

## Verdict

**The omitted causal input `tax_rate` changed from 2 to 8 while the artifact's declared `price + limit` fingerprint stayed identical. A declared-only applicability guard therefore adopted and committed output 22 even though the current correct output was 28. Binding adoption first to the authoritative dependency manifest rejected the incomplete artifact with zero effects; recomputation over the complete causal contract then committed output 28 exactly once.**
