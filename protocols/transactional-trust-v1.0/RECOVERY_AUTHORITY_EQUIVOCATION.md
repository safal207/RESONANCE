# TTP Extension — Recovery Authority Equivocation

## Law

> **AUTHENTIC RECOVERY RECORD ≠ UNIQUE RECOVERY HISTORY.**

A recovery authority may issue more than one authentic resolution for the same inherited dispute and recovery epoch. Consequential authorization therefore requires not only recovery-record authenticity, but consistency of the recovery history itself.

## Decision rule

```text
RECEIVE RECOVERY RECORD R
        ↓
AUTHENTICATE R
        ↓
LOOK FOR AUTHENTIC PEER RECOVERY VIEW
AT SAME NAMESPACE + RECOVERY EPOCH + DISPUTE SET
        ↓
same recovery issuer?
same recovery epoch?
same inherited dispute set?
different authentic recovery digest?
  ├─ yes → RECOVERY-AUTHORITY EQUIVOCATION
  │        → quarantine recovery issuer
  │        → hold all disputed resolution branches
  │        → 0 consequence
  └─ no
        ↓
CHECK RECOVERY CURRENTNESS
        ↓
VALIDATE MEMBERSHIP + QUORUM + HEAD + AUTHORITY VIEW
        ↓
FENCED CONSEQUENCE
```

## Invariants

### I115 — AUTHENTIC RECOVERY RECORD ≠ UNIQUE RECOVERY HISTORY

A valid recovery signature proves origin and integrity of one resolution record. It does not prove that the recovery issuer produced only one resolution for that epoch.

### I116 — SAME RECOVERY AUTHORITY + SAME RECOVERY EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC RESOLUTION DIGESTS = EQUIVOCATION EVIDENCE

Two authentic resolution branches for the same inherited dispute at one recovery epoch constitute a fork in recovery authority.

### I117 — RECOVERY-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED RESOLUTION BRANCHES AND QUARANTINE THE EQUIVOCATING RECOVERY ISSUER BEFORE CONSEQUENCE

A verifier must not select a recovery branch merely because that branch is locally authentic and carries a valid quorum.

### I118 — RECOVERY FROM RECOVERY-EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT RESOLUTION THAT BINDS EVERY CONFLICTING RECOVERY DIGEST

Recovery must advance through the fork explicitly. A fresh independent resolver or governance authority must bind all disputed recovery digests before live authority resumes.

## Recovery pattern

```text
R3-A ─┐
      ├─ same issuer / same recovery epoch / same dispute → CONFLICT
R3-B ─┘
      ↓
QUARANTINE RECOVERY ISSUER
      ↓
HOLD BOTH BRANCHES
      ↓
R4 FROM INDEPENDENT RESOLVER
- higher epoch
- binds digest(R3-A)
- binds digest(R3-B)
- fresh quorum
      ↓
RESUME
```

## Boundary

This rule does not define production governance, PKI, consensus finality, quorum-liveness assumptions, key revocation or a real incident-response authority. It defines the evidence invariant: **a recovery signature is not sufficient proof that recovery history is unique or globally consistent.**
