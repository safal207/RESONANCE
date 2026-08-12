# Transactional Trust Protocol v1.0 — Model Compatibility Proof

## Purpose

Model-currentness checks should fail closed when an artifact was computed under a superseded causal model. But exact model identity is conservative: two model versions may remain semantically equivalent for a bounded region of state space.

This extension defines the evidence required to reuse historical work across model identities without silently treating version mismatch as either universal incompatibility or universal compatibility.

## Core law

> **MODEL VERSION MISMATCH ≠ AUTOMATIC INCOMPATIBILITY — COMPATIBILITY ITSELF MUST BE PROVED.**

## Compatibility proof object

A compatibility proof should bind at least:

```text
from_model_version
from_model_digest

to_model_version
to_model_digest

compatibility_rule_id
compatibility_rule_digest

artifact_digest
current_state_or_dependency_fingerprint

predicate / scope
predicate_evaluation

adoption authority / fence
proof digest or evidence reference
```

A bare `compatible=true` flag is insufficient for consequential reuse.

## Canonical decision

```text
READ ARTIFACT MODEL M_then
          ↓
RESOLVE CURRENT MODEL M_now
          ↓
M_then == M_now ?
  ├─ yes → ordinary current-model applicability checks
  └─ no
       ↓
   RESOLVE COMPATIBILITY PROOF C
       ↓
   VERIFY C BINDS
   from-model + to-model
   + artifact
   + rule identity
   + current scope/state
       ↓
   EVALUATE PREDICATE NOW
     ├─ false / unknown → HOLD / REVALIDATE / RECOMPUTE
     └─ true
          ↓
      CURRENT AUTHORITY ADOPTS
          ↓
      RESOURCE-SIDE FENCED COMMIT
          ↓
      PROVE COMPATIBILITY TRAJECTORY
```

## Invariants

### I71 — MODEL VERSION MISMATCH DOES NOT BY ITSELF PROVE INCOMPATIBILITY; COMPATIBILITY MUST BE PROVED

Different model versions may be equivalent for a bounded domain. That equivalence must be represented as evidence rather than assumed from version labels.

### I72 — COMPATIBILITY PROOF MUST BIND EXACT MODEL IDENTITIES, ARTIFACT IDENTITY, AND CURRENT STATE/SCOPE

A theorem or migration claim detached from the exact historical model, current model, artifact, and state assumptions cannot safely authorize consequence.

### I73 — A GLOBAL COMPATIBILITY FLAG IS NOT EQUIVALENCE EVIDENCE FOR EVERY ARTIFACT

Compatibility may depend on branch conditions, input ranges, limits, caps, invariant regions, feature flags, policy state, or other predicates.

### I74 — FAILED OR UNKNOWN COMPATIBILITY PROOF REQUIRES HOLD, REVALIDATION, OR RECOMPUTATION BEFORE CONSEQUENCE

Out-of-scope, stale, incomplete, tampered, identity-mismatched, or unavailable proof must fail closed for consequential adoption.

## Verified example

```text
model-v1: y = min(limit, 2 × price)
model-v2: y = min(limit, 2 × price + tax_rate)

proof predicate:
tax_rate >= 0 AND 2 × price >= limit
```

When the predicate holds, both models are capped at `limit` and an older v1 artifact may be reusable after exact proof binding.

When the predicate does not hold, model-v1 and model-v2 may diverge; a blanket compatibility flag is unsafe.

Verified Report #028 demonstrates both paths with PostgreSQL state, explicit proof identity, and a Dockerized fenced external effect boundary.

## Evidence rule

Proof should preserve the chain:

```text
M_then
→ artifact
→ model transition
→ compatibility rule
→ current predicate evaluation
→ current adoption authority
→ fenced effect
```

Compatibility evidence is therefore not merely documentation about a migration. It is part of the transactional trust trajectory for the individual consequential artifact.

## Boundary

This extension does not define a universal semantic-equivalence algorithm. Domain-specific compatibility proofs may be formal proofs, checked predicates, equivalence tests, migration certificates, invariant-preservation arguments, or independently verified evidence bundles, depending on the system.
