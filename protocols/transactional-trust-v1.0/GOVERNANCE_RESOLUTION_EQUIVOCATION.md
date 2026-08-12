# TTP Extension — Governance Resolution Equivocation / Conflicting Finality

## Purpose

A governance-resolution signature can authenticate one finality record without proving that the governance issuer produced only one record for that epoch. Consequential authorization therefore needs cross-view consistency evidence at the governance/finality layer.

## Invariants

### I119 — AUTHENTIC GOVERNANCE RESOLUTION ≠ UNIQUE FINALITY

Authenticity proves origin and integrity of one governance resolution. It does not prove uniqueness of the issuer's history.

### I120 — SAME GOVERNANCE AUTHORITY + SAME GOVERNANCE EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC FINALITY DIGESTS = EQUIVOCATION EVIDENCE

Two authentic records resolving the same inherited dispute at the same governance epoch are a fork.

### I121 — GOVERNANCE-RESOLUTION EQUIVOCATION MUST HOLD ALL DISPUTED FINALITY BRANCHES AND QUARANTINE THE EQUIVOCATING GOVERNANCE ISSUER BEFORE CONSEQUENCE

Do not select a branch because it arrived first, has a valid local quorum, or appears operationally plausible.

### I122 — RECOVERY FROM GOVERNANCE EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT CONSTITUTIONAL RESOLUTION THAT BINDS EVERY CONFLICTING GOVERNANCE DIGEST

Recovery must explicitly preserve and resolve the fork evidence before live authority resumes.

## Decision path

```text
RECEIVE GOVERNANCE RESOLUTION G
        ↓
AUTHENTICATE G
        ↓
LOOK FOR PEER GOVERNANCE VIEW
AT SAME NAMESPACE + GOVERNANCE EPOCH + DISPUTE SET
        ↓
same issuer + same epoch + same dispute + different digest?
  ├─ yes → GOVERNANCE RESOLUTION EQUIVOCATION
  │        → quarantine governance issuer
  │        → hold every disputed finality branch
  │        → 0 consequence
  └─ no
        ↓
CHECK GOVERNANCE CURRENTNESS
        ↓
VALIDATE MEMBERSHIP + QUORUM + AUTHORITY HEAD
        ↓
FENCED CONSEQUENCE

RECOVERY FROM FINALITY FORK:
  higher governance/finality epoch
+ independent constitutional/root resolver
+ bind every conflicting governance digest
+ fresh quorum
→ resume
```

## Scope boundary

This rule does not make a constitutional/root authority intrinsically trustworthy or non-equivocating. Root-authority replay, rollback and equivocation remain separate verification surfaces.
