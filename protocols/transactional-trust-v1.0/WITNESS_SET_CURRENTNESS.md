# TTP Extension — Witness-Set Currentness

## Law

> **VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY.**

A quorum certificate may remain cryptographically correct after the membership that formed it has been superseded. Consequential authorization therefore requires both quorum validity and current membership authority.

## Required bindings

A quorum certificate that may authorize consequence should bind at least:

- witness-set identity;
- witness-set epoch;
- membership digest;
- threshold policy;
- logical round;
- authority-head identity / generation;
- distinct signer identities.

At adoption or commit time, the verifier resolves the current authenticated membership authority and compares the certificate's membership binding with that current record.

## Decision rule

```text
QC valid under historical membership?
  ├─ no → REJECT
  └─ yes
       ↓
RESOLVE CURRENT MEMBERSHIP M_now
       ↓
QC.set_id == M_now.set_id
QC.set_epoch == M_now.set_epoch
QC.membership_digest == digest(M_now)
QC.threshold == M_now.threshold
       ↓
all true?
  ├─ no → witness_set_authority_conflict → HOLD
  └─ yes
       ↓
CHECK CROSS-VIEW QUORUM CONSISTENCY
       ↓
CHECK AUTHORITY HEAD / VIEW / PROOF
       ↓
FENCED CONSEQUENCE
```

## Invariants

### I103 — VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY

Historical validity does not preserve live execution authority across membership rotation.

### I104 — QUORUM CERTIFICATE MUST BIND WITNESS-SET IDENTITY, SET EPOCH, MEMBERSHIP DIGEST, THRESHOLD POLICY, ROUND, HEAD IDENTITY, AND DISTINCT SIGNERS

The membership configuration is part of the authorization evidence, not metadata around it.

### I105 — ADOPTION MUST RESOLVE CURRENT WITNESS-SET AUTHORITY AND REJECT SUPERSEDED MEMBERSHIP BEFORE CONSEQUENCE

A verifier must not authorize a new effect solely from signatures of a set that no longer holds current authority.

### I106 — MEMBERSHIP ROTATION REQUIRES FRESH CURRENT-SET QUORUM EVIDENCE; OLD MEMBERS REMAIN HISTORICAL EVIDENCE, NOT LIVE AUTHORITY

Rotation advances authority while preserving the old certificate for audit and provenance.

## Failure disposition

On membership mismatch:

```text
witness_set_authority_conflict
→ no adoption
→ no external effect
→ resolve current membership
→ obtain fresh current-set quorum evidence
```

Do not silently reinterpret an old membership certificate as current, and do not select a historical set merely because its signatures are still valid.

## Boundary

This rule does not specify production membership governance, BFT reconfiguration, PKI, key revocation, synchrony or quorum-liveness assumptions. It only states the evidence invariant: **the quorum's membership authority must be current at consequence time.**
