# TTP Extension — Causal Model Completeness

Verified Report #026 extends the Transactional Trust Protocol from dependency-aware applicability to verification of the dependency model itself.

## Invariants

### I63 — A CORRECT FINGERPRINT OVER AN INCOMPLETE DEPENDENCY SET IS STILL UNSAFE

A deterministic or cryptographic fingerprint only proves identity of the values included in it. It does not prove that all causally relevant inputs were included.

### I64 — DEPENDENCY-SET IDENTITY IS PART OF APPLICABILITY EVIDENCE

Consequential artifacts SHOULD preserve the identity, version or digest of the dependency manifest/model used to select their causal inputs.

### I65 — ADOPTION MUST VALIDATE THE DEPENDENCY MANIFEST, NOT ONLY THE FINGERPRINT VALUES

Before relying on a dependency-value fingerprint, the adopter SHOULD verify that the artifact's dependency manifest matches an authoritative or independently validated dependency contract for the decision.

### I66 — OMITTED OR UNKNOWN CAUSAL INPUT REQUIRES REVALIDATION, RECOMPUTATION, OR HOLD BEFORE CONSEQUENCE

If dependency-model completeness is unknown or contradicted, a matching value fingerprint MUST NOT by itself authorize a consequential action.

## Rule

```text
RESOLVE DEPENDENCY CONTRACT M
        ↓
BIND MODEL IDENTITY hash(M)
        ↓
CAPTURE DEPENDENCY VALUES
        ↓
COMPUTE VALUE FINGERPRINT F
        ↓
COMPUTE ARTIFACT D
        ↓
ADOPTION-TIME MODEL CHECK
   ├─ model mismatch / unknown → HOLD / REVALIDATE MODEL
   └─ model match              → COMPARE VALUES
                                  ├─ value mismatch → RECOMPUTE / PROVE
                                  └─ values match   → eligible to adopt
        ↓
CURRENT AUTHORITY
        ↓
FENCED COMMIT
        ↓
PROVE MODEL → VALUES → ARTIFACT → EFFECT
```

## Core distinction

```text
VALUE INTEGRITY ≠ MODEL COMPLETENESS
```

A perfect fingerprint can perfectly certify the wrong slice of reality.

## Evidence

Verified Report #026: `reports/verified/026-incomplete-causal-graph/REPORT.md`

GitHub Actions run: `31583719848`
