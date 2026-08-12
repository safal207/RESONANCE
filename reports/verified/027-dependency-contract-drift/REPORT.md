# RESONANCE Verified Report #027

# Dependency Contract Drift / Model Version Race

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Dependency Contract Drift v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**GitHub Actions run:** `31584552547`  
**Evidence artifact:** `resonance-dependency-contract-drift-v1.0`  
**Artifact ID:** `9136540015`  
**Artifact digest:** `sha256:1feadce415460da2149452ba614c8bea6dd5001df423bea2e603edb97c2413bd`

## Result

# **10 / 10 — Dependency contract drift protocol passes**

Verified #026 showed that a correct fingerprint can still be unsafe when the causal dependency set is incomplete. Report #027 asks the temporal version of that problem:

> What if the causal model was authoritative and valid when the artifact was produced, but the authoritative model changes before adoption?

# **MODEL VALID THEN ≠ MODEL VALID NOW**

## Isolation: business state did not change

The benchmark holds all business inputs constant:

```text
price = 10
limit = 30
tax_rate = 2
theme = light
owner = worker-B
fence = 2
```

Only the authoritative causal model changes.

At production time:

```text
model-v1
manifest = price + limit
formula = min(limit, 2 × price)
output = 20
```

The artifact binds:

```text
model_version = model-v1
model_digest = sha256:b6a3af2455410ab4efeafdd6eb7efed2d5595303c305e127129ff508f3c7622d
dependency_fingerprint = sha256:7022bd8c6b33b4835be0601879c04a0f96ce9d651f25df9ebb3b44e340118e6b
```

Before adoption, the authoritative model changes to:

```text
model-v2
manifest = price + limit + tax_rate
formula = min(limit, 2 × price + tax_rate)
output = 22
model_digest = sha256:8c1045c3ec1b05d84953b8d0d0862ea0135c09503fe593ef5829ff6308f01aef
```

No business value changed. The old artifact was valid under v1 when produced. It is no longer automatically applicable under the current model.

## Unsafe: validate against the artifact's own historical model

The unsafe path evaluates current state using the dependency model embedded in the artifact itself.

Because `price` and `limit` are unchanged, the old v1 fingerprint still matches its own historical contract:

```text
artifact model = v1
current price = 10
current limit = 30
v1 fingerprint still matches

→ adoption rows = 1
→ HTTP 200 / applied
→ committed output = 20
```

But the current authoritative model v2 requires output `22`.

The failure is not stale business data, artifact corruption, stale ownership, or missing fencing. It is **stale model authority**.

## Safe: compare artifact model identity to current model authority first

The safe path checks model identity before dependency values:

```text
artifact model_version = model-v1
current model_version = model-v2

artifact model_digest != current model_digest

→ model_version_conflict
→ adoption rows = 0
→ external effects = 0
```

Worker B then recomputes under the current model v2:

```text
price = 10
limit = 30
tax_rate = 2
output = 22
```

The v2 artifact is adopted and committed exactly once:

```text
adoption rows = 1
HTTP 200 / applied
final effect_count = 1
final output = 22
```

## No-drift control

When model-v1 remains the current authoritative model, a current v1 artifact passes the same current-model guard and commits output `20` exactly once.

The rule therefore does not disable normal adoption. It rejects only unproven model drift.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| v1 artifact valid at production; only model identity changes before adoption | PASS | 2/2 |
| Artifact-bound validation accepts historical v1 and commits stale output 20 | PASS | 2/2 |
| Current-model guard rejects old model identity with zero effects | PASS | 2/2 |
| Recompute under v2 commits current output 22 exactly once | PASS | 2/2 |
| No-model-drift v1 control succeeds normally | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I67 — MODEL VALID THEN ≠ MODEL VALID NOW**

An artifact being valid under the authoritative causal model at production time does not prove that the same model is still authoritative at adoption or consequence time.

# **I68 — ARTIFACT MUST BIND THE CAUSAL-MODEL IDENTITY THAT AUTHORIZED ITS COMPUTATION**

For consequential state-sensitive work, preserve model version/digest together with dependency identity and values.

# **I69 — ADOPTION MUST COMPARE ARTIFACT MODEL IDENTITY WITH CURRENT MODEL AUTHORITY BEFORE VALUE FINGERPRINT**

A historical model can continue to validate its own inputs perfectly after it has been superseded. Self-consistency is not current authority.

# **I70 — MODEL DRIFT OR UNKNOWN COMPATIBILITY REQUIRES HOLD, REVALIDATION, RECOMPUTATION, OR EXPLICIT COMPATIBILITY PROOF BEFORE CONSEQUENCE**

Exact model mismatch may be conservatively rejectable. Reuse across model versions requires explicit evidence that the old result remains valid under the new model.

## TTP model-currentness rule

```text
RESOLVE CURRENT CAUSAL MODEL M_now
            ↓
READ ARTIFACT-BOUND MODEL M_then
            ↓
COMPARE MODEL IDENTITY
   ├─ same → compare dependency values
   └─ different / unknown
          ↓
      COMPATIBILITY PROOF?
        ├─ yes → revalidate against M_now
        └─ no  → HOLD / RECOMPUTE
            ↓
CURRENT AUTHORITY ADOPTS
            ↓
FENCED COMMIT
            ↓
PROVE MODEL HISTORY → CURRENTNESS → VALUES → ARTIFACT → EFFECT
```

## Relationship to #024–#027

```text
#024 → is the result current for current state?
#025 → which state actually matters?
#026 → is the causal dependency model complete enough?
#027 → is that causal model still the current authoritative model?
```

The broader model becomes:

```text
CAUSAL APPLICABILITY =
  model identity
+ model currentness / compatibility evidence
+ model completeness evidence
+ dependency-value fingerprint
+ current dependency comparison
+ current authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The benchmark supplies deterministic model-v1 and model-v2 definitions. It does not automatically discover causal models, establish that a production model update is scientifically correct, or define a universal compatibility relation between model versions.

A model-version mismatch does not prove that an old result is unusable; it proves that reuse requires additional compatibility evidence rather than silent trust in historical self-consistency.

This is not production safety certification, arbitrary agent safety, or a vulnerability claim against PostgreSQL or another external product.

## Reproducibility

Benchmark: `benchmarks/dependency-contract-drift-v1.0/`  
Workflow: `.github/workflows/benchmark-dependency-contract-drift.yml`  
Machine summary: `reports/verified/027-dependency-contract-drift/result.json`  
GitHub Actions: `31584552547`

## Verdict

**The artifact was valid under authoritative model-v1 and all business inputs remained unchanged. After the authoritative model advanced to v2, artifact-bound self-validation still accepted the old v1 result and committed output 20, while the current model required 22. Comparing artifact model identity with current model authority rejected the stale-model artifact with zero effects; recomputation under v2 then committed output 22 exactly once.**
