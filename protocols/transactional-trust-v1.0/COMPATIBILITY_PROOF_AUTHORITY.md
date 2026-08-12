# TTP Extension — Compatibility Proof Authority / Revocation

## Canonical law

**PROOF VALID THEN ≠ PROOF AUTHORIZED NOW.**

A compatibility proof that was valid and authorized at issuance does not automatically remain authorized at adoption or consequence time.

## Required bindings

A consequential compatibility proof should bind at least:

- historical model version + digest
- current model version + digest
- exact artifact identity/digest
- compatibility rule identity/digest
- current state/scope evidence
- proof-authority status/epoch at issuance
- current execution/adoption authority

Before consequence, resolve current proof-rule authority and compare it with the proof's authority identity/epoch.

## Invariants

### I75 — PROOF VALID THEN ≠ PROOF AUTHORIZED NOW

Internal proof validity and issuance-time authorization do not establish current authorization.

### I76 — CONSEQUENTIAL PROOF AUTHORITY MUST BE RESOLVED AGAINST CURRENT RULE AUTHORITY AT ADOPTION OR COMMIT TIME

Check current rule status, rule identity/digest, and authority epoch before trusting the proof for a consequential transition.

### I77 — REVOCATION OR AUTHORITY-EPOCH ADVANCE INVALIDATES HISTORICAL PROOF AUTHORIZATION EVEN WHEN THE SEMANTIC PREDICATE STILL HOLDS

A semantically correct artifact is not enough to repair revoked proof authority.

### I78 — A SUCCESSOR PROOF MAY REAUTHORIZE THE SAME ARTIFACT ONLY THROUGH FRESH CURRENT-AUTHORITY BINDING

Fresh reauthorization should rebind the exact artifact, model identities, rule identity, current state/scope, and current proof-authority epoch.

## Decision flow

```text
ARTIFACT + PROOF P_then
        ↓
VERIFY STATIC BINDINGS
        ↓
RESOLVE CURRENT RULE AUTHORITY
        ↓
CHECK
- rule id/digest
- ACTIVE status
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
PROVE AUTHORITY HISTORY → CURRENTNESS → EFFECT
```

## Boundary

This rule does not define who should govern a real compatibility-proof registry or what real-world evidence is sufficient to revoke a theorem. It defines the protocol requirement that consequential reuse must not silently inherit authority from a stale certificate.
