# RESONANCE Verified Report #028

# Model Compatibility Proof / Backward-Compatible Migration

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Model Compatibility Proof v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**GitHub Actions run:** `31585859218`  
**Evidence artifact:** `resonance-model-compatibility-proof-v1.0`  
**Artifact ID:** `9137064805`  
**Artifact digest:** `sha256:eccd83344d2f34caa7a1b933500a32389572408c04bd1de3172340dd625e3b7e`

## Result

# **10 / 10 — Model compatibility proof protocol passes**

Verified #027 established a conservative rule: when the authoritative causal model changes, a historical artifact should not silently inherit current applicability. Report #028 tests the safe exception:

> Can an artifact from an older model be reused without recomputation when the old and new models are provably equivalent for this specific artifact and current state?

# **MODEL VERSION MISMATCH ≠ AUTOMATIC INCOMPATIBILITY — COMPATIBILITY ITSELF MUST BE PROVED**

## Models

```text
model-v1:
y = min(limit, 2 × price)

model-v2:
y = min(limit, 2 × price + tax_rate)
```

These models are not globally equivalent.

But under the scoped predicate:

```text
tax_rate >= 0
AND
2 × price >= limit
```

both models necessarily evaluate to `limit`.

Compatibility rule identity:

```text
rule_id = cap-dominates-tax-extension-v1
rule_digest = sha256:8d7a5c65924b77a058778c99c4defbe13699ec49a58f36176981be49639105f6
```

## Safe compatibility reuse

State:

```text
price = 20
limit = 30
tax_rate = 8
```

Historical v1 artifact:

```text
v1 output = min(30, 40) = 30
```

Current v2 semantics:

```text
v2 output = min(30, 48) = 30
```

The compatibility proof bound:

- exact v1 model version + digest
- exact v2 model version + digest
- exact compatibility rule identity
- exact artifact digest
- exact current values fingerprint
- evaluated scope predicate
- current adoption authority

All proof checks passed:

```text
rule_identity = true
from_model = true
to_model = true
artifact_binding = true
current_values = true
predicate = true
transition = true

→ adoption rows = 1
→ HTTP 200 / applied
→ effect_count = 1
→ output = 30
```

The old artifact was reused without recomputation because equivalence was proved for the current scope.

## Unsafe: global compatibility flag

A blanket claim that `model-v1 → model-v2` is backward compatible was then tested at:

```text
price = 10
limit = 30
tax_rate = 8
```

Now:

```text
v1 output = 20
v2 output = 28
```

The scoped predicate is false, but the unsafe global flag ignores scope:

```text
compatible(v1, v2) = true
→ adoption rows = 1
→ HTTP 200 / applied
→ committed output = 20
```

Current correct output was `28`.

A version-pair compatibility flag is therefore not sufficient evidence for every artifact or every point in state space.

## Safe: out-of-scope rejection

The real proof was evaluated on the same incompatible state:

```text
predicate_holds = false
→ compatibility_scope_conflict
→ adoption rows = 0
→ external effects = 0
```

Worker B then recomputed under model-v2:

```text
output = 28
→ current-model adoption rows = 1
→ HTTP 200 / applied
→ final effect_count = 1
```

## Proof binding tamper

Even when the semantic predicate itself was true, two tampered proofs were rejected:

```text
wrong target-model digest
→ compatibility_proof_binding_conflict

wrong artifact digest
→ compatibility_proof_binding_conflict

external effects = 0
```

A compatibility theorem without exact identity binding is not sufficient consequence evidence.

## Current-model control

A current model-v2 artifact at the incompatible-state values committed normally:

```text
output = 28
adoption rows = 1
effect_count = 1
```

Compatibility proof is required only to justify reuse across model identities, not ordinary current-model execution.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Scoped proof reuses old artifact when v1 and v2 are equivalent for current state | PASS | 2/2 |
| Global compatibility flag commits stale result outside proven scope | PASS | 2/2 |
| Out-of-scope proof rejects old artifact; v2 recompute commits once | PASS | 2/2 |
| Proof must bind exact target-model and artifact identity | PASS | 2/2 |
| Current-model artifact commits normally | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I71 — MODEL VERSION MISMATCH DOES NOT BY ITSELF PROVE INCOMPATIBILITY; COMPATIBILITY MUST BE PROVED**

Different model identities may still produce equivalent consequences for a bounded domain, but that equivalence is a claim requiring evidence.

# **I72 — COMPATIBILITY PROOF MUST BIND EXACT MODEL IDENTITIES, ARTIFACT IDENTITY, AND CURRENT STATE/SCOPE**

A reusable proof must identify the historical model, current model, artifact, compatibility rule, and state assumptions under which equivalence holds.

# **I73 — A GLOBAL COMPATIBILITY FLAG IS NOT EQUIVALENCE EVIDENCE FOR EVERY ARTIFACT**

Compatibility may be conditional on input ranges, invariants, caps, branches, policy state, feature flags, or other domain predicates.

# **I74 — FAILED OR UNKNOWN COMPATIBILITY PROOF REQUIRES HOLD, REVALIDATION, OR RECOMPUTATION BEFORE CONSEQUENCE**

A proof that is out of scope, identity-mismatched, stale, tampered, or unavailable must not silently authorize historical output.

## TTP model-compatibility rule

```text
ARTIFACT BOUND TO M_then
          ↓
RESOLVE CURRENT M_now
          ↓
M_then == M_now ?
  ├─ yes → normal current-model applicability checks
  └─ no
       ↓
   RESOLVE COMPATIBILITY PROOF C
       ↓
   VERIFY C BINDS
   - from-model identity
   - to-model identity
   - artifact identity
   - rule identity
   - current state/scope
       ↓
   EVALUATE PROOF PREDICATE NOW
     ├─ false / unknown → HOLD / RECOMPUTE
     └─ true
          ↓
      CURRENT OWNER ADOPTS
          ↓
      FENCED COMMIT
          ↓
      PROVE MODEL HISTORY → COMPATIBILITY → ARTIFACT → EFFECT
```

## Relationship to #026–#028

```text
#026 → prove the causal model is complete enough
#027 → prove the artifact's model is still current, or stop
#028 → if model changed, prove scoped semantic compatibility before reuse
```

The broader model becomes:

```text
CAUSAL APPLICABILITY =
  model identity
+ model currentness
+ model completeness evidence
+ compatibility proof when identities differ
+ dependency-value evidence
+ current authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

This benchmark supplies a deterministic compatibility theorem for two simple functions. It does not automatically prove compatibility for arbitrary production models, infer proof predicates, or certify semantic equivalence of real AI systems.

A successful compatibility proof is scoped evidence, not a global statement that two model versions are interchangeable.

This is not production safety certification, arbitrary agent safety, or a vulnerability claim against PostgreSQL or another external product.

## Reproducibility

Benchmark: `benchmarks/model-compatibility-proof-v1.0/`  
Workflow: `.github/workflows/benchmark-model-compatibility-proof.yml`  
Machine summary: `reports/verified/028-model-compatibility-proof/result.json`  
GitHub Actions: `31585859218`

## Verdict

**A model-v1 artifact was safely reused under model-v2 without recomputation when a state-scoped proof established semantic equivalence and bound exact model, artifact, rule, and current-state identities. The same version-pair treated as globally compatible committed stale output 20 where v2 required 28. Scoped proof rejected that out-of-domain reuse with zero effects, after which recomputation under v2 committed 28 exactly once.**
