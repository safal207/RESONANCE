# Transactional Trust Protocol v1.0 — Quorum Consistency

## Law

> **LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM.**

A threshold certificate can be locally valid and still conflict with another locally valid threshold certificate for the same witness-set epoch and logical round.

## Invariants

### I99 — LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM

Local threshold satisfaction is not proof that another incompatible threshold certificate does not exist elsewhere.

### I100 — QUORUM CERTIFICATE MUST BIND WITNESS-SET IDENTITY, SET EPOCH, LOGICAL ROUND, HEAD IDENTITY, AND DISTINCT SIGNERS

Without this common decision identity, quorum certificates cannot be safely compared as competing claims about the same trust transition.

### I101 — CONFLICTING LOCALLY VALID QUORUM CERTIFICATES FOR THE SAME SET EPOCH AND ROUND REQUIRE INTERSECTION / EQUIVOCATION CHECK AND HOLD BEFORE CONSEQUENCE

Do not choose a branch merely because it independently meets threshold. Compare the certificates, compute their signer intersection, and preserve conflicting authentic statements as evidence.

### I102 — EQUIVOCATING INTERSECTION MEMBERS MUST BE QUARANTINED; RESUME ONLY WITH A NON-CONFLICTING THRESHOLD CERTIFICATE THAT EXCLUDES QUARANTINED AUTHORITY

Conflict recovery must remove the authority contribution that made both incompatible certificates possible before consequence can resume.

## Decision rule

```text
RECEIVE QUORUM CERTIFICATE QC
        ↓
AUTHENTICATE DISTINCT MEMBER STATEMENTS
        ↓
BIND SET ID + SET EPOCH + ROUND + HEAD
        ↓
CHECK THRESHOLD
        ↓
GOSSIP / CROSS-CHECK CERTIFICATE VIEW
        ↓
CONFLICTING VALID QC FOR SAME SET EPOCH + ROUND?
  ├─ yes
  │    ↓
  │  COMPUTE QUORUM INTERSECTION
  │    ↓
  │  FIND AUTHENTIC CONFLICTING SIGNATURES
  │    ↓
  │  QUARANTINE EQUIVOCATORS
  │    ↓
  │  HOLD / 0 CONSEQUENCE
  └─ no
        ↓
VERIFY HEAD + AUTHORITY VIEW + PROOF
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE QC → GLOBAL CONSISTENCY → HEAD → EFFECT
```

## Evidence requirements

Preserve at minimum:

- witness-set identity and epoch,
- threshold and member identities,
- logical decision round,
- exact authenticated member statements,
- quorum-certificate signer set,
- bound authority-head digest/generation,
- any competing quorum certificate,
- signer intersection,
- exact conflicting statements for intersecting identities,
- quarantine disposition,
- recovery certificate,
- resulting adoption and external-effect evidence.

## Boundary

This rule specifies an experimental verification requirement, not a complete Byzantine consensus algorithm. Production quorum safety depends on membership governance, threshold assumptions, key management, network delivery, reconfiguration, fault model, and the mechanism used to surface conflicting certificates across views.
