# TTP Extension — Model Currentness / Dependency Contract Drift

Verified Report #027 adds a temporal rule for causal models used in consequential adoption.

## Core law

# **MODEL VALID THEN ≠ MODEL VALID NOW**

A result can be perfectly valid under the model that authorized its computation and still become unsafe to apply after the authoritative model changes.

## Invariants

### I67 — MODEL VALID THEN ≠ MODEL VALID NOW

Historical validity under `M_then` does not prove current applicability under `M_now`.

### I68 — ARTIFACT MUST BIND THE CAUSAL-MODEL IDENTITY THAT AUTHORIZED ITS COMPUTATION

Evidence should preserve at least:

```text
model_version
model_digest
manifest / dependency-set identity
value fingerprint
artifact digest
```

### I69 — ADOPTION MUST COMPARE ARTIFACT MODEL IDENTITY WITH CURRENT MODEL AUTHORITY BEFORE VALUE FINGERPRINT

Do not let a superseded model validate its own artifact merely because its historical dependency values still match.

### I70 — MODEL DRIFT OR UNKNOWN COMPATIBILITY REQUIRES HOLD, REVALIDATION, RECOMPUTATION, OR EXPLICIT COMPATIBILITY PROOF BEFORE CONSEQUENCE

A model mismatch is not automatically proof that an old artifact is unusable. It is proof that reuse requires explicit evidence rather than silent historical self-consistency.

## Canonical chain

```text
COMPUTE UNDER M_then
      ↓
BIND MODEL IDENTITY + VALUES + ARTIFACT
      ↓
MODEL AUTHORITY MAY CHANGE
      ↓
RESOLVE M_now
      ↓
COMPARE M_then ↔ M_now
  ├─ same → compare current dependency values
  └─ different / unknown
          ↓
      compatibility evidence?
       ├─ no  → HOLD / RECOMPUTE
       └─ yes → REVALIDATE UNDER M_now
          ↓
CURRENT OWNER ADOPTS
          ↓
FENCED COMMIT
          ↓
PROVE MODEL HISTORY → CURRENTNESS → ARTIFACT → EFFECT
```

## Minimal adoption rule

```text
IF artifact.model_digest == current_model.digest
   AND artifact.dependency_fingerprint == current_fingerprint(current_model)
   AND current_execution_authority_is_valid
THEN artifact may be eligible for adoption
ELSE HOLD / REVALIDATE / RECOMPUTE / prove compatibility
```

## Important boundary

Exact model identity is a conservative default, not a universal semantic compatibility algorithm. A newer model can be backward-compatible with an older result, but that compatibility must itself become evidence.

## Relationship

```text
#026 → prove the causal graph is complete enough
#027 → prove that graph is still the authoritative graph now
```

This extension is based on deterministic local protocol evidence. It is not production safety certification.