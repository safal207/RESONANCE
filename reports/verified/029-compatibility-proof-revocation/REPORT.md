# RESONANCE Verified Report #029

# Compatibility Proof Revocation / Stale Compatibility Certificate

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Compatibility Proof Revocation v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**GitHub Actions run:** `31587611585`  
**Evidence artifact:** `resonance-compatibility-proof-revocation-v1.0`  
**Artifact ID:** `9137771205`  
**Artifact digest:** `sha256:5782654655249341994236b6d68ca875f74ceb1d8d22fd4eacc53454e7100e80`

## Result

# **10 / 10 — Compatibility proof revocation protocol passes**

Verified #028 established that an older-model artifact may be safely reused when a scoped compatibility proof binds the exact models, artifact, rule, and current state. Report #029 asks the next temporal trust question:

> What if that compatibility proof was valid when issued, but its rule authority is revoked or advances before adoption?

# **PROOF VALID THEN ≠ PROOF AUTHORIZED NOW**

## Isolation: the output stays correct

The benchmark deliberately keeps semantic compatibility true:

```text
model-v1: y = min(limit, 2 × price)
model-v2: y = min(limit, 2 × price + tax_rate)

price = 20
limit = 30
tax_rate = 8

v1 output = 30
v2 output = 30
predicate = true
```

The historical artifact remains semantically correct. The failure surface is proof authorization, not result correctness.

## Rule authority timeline

At issuance:

```text
R1 = cap-equivalence-r1
status = ACTIVE
authority_epoch = 1
proof P1 issued
```

Before adoption:

```text
R1 status → REVOKED
R1 authority_epoch → 2
successor → R2

R2 status → ACTIVE
R2 authority_epoch → 2
```

The old proof still contains valid model bindings, artifact identity, current-values fingerprint, and a true compatibility predicate.

## Unsafe: cached proof contents authorize after revocation

A verifier that checks only proof contents but does not resolve live rule authority observes:

```text
from_model = true
to_model = true
artifact = true
current values = true
predicate = true

→ adoption rows = 1
→ HTTP 200 / applied
→ effect_count = 1
→ output = 30
```

But the live registry says:

```text
R1 status = REVOKED
R1 authority_epoch = 2
proof authority_epoch = 1
```

The numeric result is correct. The consequence is nevertheless unauthorized by current proof authority.

## Safe: live registry rejects the same proof

The safe verifier resolves current authority before adoption:

```text
proof rule = R1 / epoch 1
current R1 = REVOKED / epoch 2

→ compatibility_proof_revoked
→ adoption rows = 0
→ external effects = 0
```

This prevents a stale certificate from inheriting authority merely because its internal statements remain self-consistent.

## Successor proof can re-authorize the same artifact

Revocation of P1 does not imply that the historical artifact must be discarded. A fresh proof under active successor R2 can bind the same artifact again:

```text
R2 status = ACTIVE
R2 authority_epoch = 2
fresh proof binds:
- R2 digest
- epoch 2
- model-v1 digest
- model-v2 digest
- exact artifact digest
- current values
- true predicate

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

The artifact survived. Its authorization was renewed through current evidence.

## Authority-epoch drift without revocation

The benchmark then kept R2 `ACTIVE` but advanced its authority epoch:

```text
proof issued at R2 epoch 2
registry advances R2 epoch 2 → 3
status remains ACTIVE
```

All semantic proof checks still passed, but the live authority epoch no longer matched:

```text
→ compatibility_proof_authority_conflict
→ adoption rows = 0
→ external effects = 0
```

Current status alone is therefore insufficient. Proof authorization needs current authority identity/epoch.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Active R1 proof authorizes reuse before revocation | PASS | 2/2 |
| Cached verifier accepts revoked but semantically correct proof | PASS | 2/2 |
| Live registry rejects revoked proof with zero effects | PASS | 2/2 |
| Active successor R2 proof re-authorizes same historical artifact | PASS | 2/2 |
| Active-rule authority epoch advance invalidates older proof | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I75 — PROOF VALID THEN ≠ PROOF AUTHORIZED NOW**

A proof being internally valid and authorized at issuance does not establish that its rule authority is still current at consequence time.

# **I76 — CONSEQUENTIAL PROOF AUTHORITY MUST BE RESOLVED AGAINST CURRENT RULE AUTHORITY AT ADOPTION OR COMMIT TIME**

For consequential reuse, verify live rule status, rule identity/digest, and authority epoch rather than trusting issuance-time status.

# **I77 — REVOCATION OR AUTHORITY-EPOCH ADVANCE INVALIDATES HISTORICAL PROOF AUTHORIZATION EVEN WHEN THE SEMANTIC PREDICATE STILL HOLDS**

A correct output does not repair stale authority.

# **I78 — A SUCCESSOR PROOF MAY REAUTHORIZE THE SAME ARTIFACT ONLY THROUGH FRESH CURRENT-AUTHORITY BINDING**

Reauthorization must bind the exact artifact, model identities, compatibility rule, current state/scope, and current proof-authority epoch.

## TTP proof-authority rule

```text
ARTIFACT + COMPATIBILITY PROOF P_then
              ↓
VERIFY STATIC PROOF BINDINGS
              ↓
RESOLVE CURRENT RULE AUTHORITY R_now
              ↓
COMPARE
- rule identity / digest
- status = ACTIVE
- authority epoch
              ↓
   current?
  ├─ no → HOLD / REPROVE / RECOMPUTE
  └─ yes
       ↓
   EVALUATE SCOPE NOW
       ↓
   CURRENT OWNER ADOPTS
       ↓
   FENCED COMMIT
       ↓
PROVE ISSUANCE → AUTHORITY HISTORY → CURRENTNESS → ARTIFACT → EFFECT
```

## Relationship to #027–#029

```text
#027 → is the artifact's causal model still authoritative?
#028 → if model changed, can scoped compatibility be proved?
#029 → is that compatibility proof itself still authorized now?
```

The broader model becomes:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

This benchmark models proof authority with a deterministic PostgreSQL registry. It does not define a universal governance system for real production proofs, automatically determine when a compatibility theorem should be revoked, or certify external AI systems.

The unsafe path intentionally produces a numerically correct effect to isolate authorization drift from semantic drift.

This is not production safety certification or a vulnerability claim against PostgreSQL or another external product.

## Reproducibility

Benchmark: `benchmarks/compatibility-proof-revocation-v1.0/`  
Workflow: `.github/workflows/benchmark-compatibility-proof-revocation.yml`  
Machine result: `reports/verified/029-compatibility-proof-revocation/result.json`  
GitHub Actions: `31587611585`

## Verdict

**A compatibility proof issued under active rule R1 remained internally valid and semantically correct after R1 was revoked. A cached verifier still adopted it and committed output 30, while a live-authority verifier rejected the same proof with zero effects. A fresh successor R2 proof re-authorized the same historical artifact safely, and a later authority-epoch advance invalidated an older R2 proof even though the rule remained ACTIVE.**
