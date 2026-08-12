# TTP Extension — Membership Authority Equivocation

## Law

> **SAME AUTHORITY + SAME MEMBERSHIP EPOCH + DIFFERENT AUTHENTIC MEMBERSHIP DIGESTS = EQUIVOCATION EVIDENCE.**

A valid membership signature proves origin and integrity of one membership record. It does not prove that the issuer produced only one record for the same epoch.

## Required comparison surface

For membership records that may authorize consequence, compare at least:

- membership namespace;
- issuer identity / key authority;
- set epoch;
- predecessor membership digest;
- membership digest;
- set identity;
- member set;
- threshold policy.

## Decision rule

```text
AUTHENTICATE MEMBERSHIP M
        ↓
LOOK FOR AUTHENTIC PEER VIEW M_peer
AT SAME MEMBERSHIP NAMESPACE + EPOCH
        ↓
same issuer?
same epoch?
same predecessor?
different membership digest?
        ↓
all true?
  ├─ yes → membership_authority_equivocation_detected
  │        → quarantine issuer
  │        → hold every disputed branch
  │        → no adoption
  │        → no external effect
  └─ no
       ↓
CHECK MEMBERSHIP CURRENTNESS / ANTI-ROLLBACK
       ↓
VALIDATE QUORUM + AUTHORITY HEAD + VIEW
       ↓
FENCED CONSEQUENCE
```

## Invariants

### I111 — SAME AUTHORITY + SAME MEMBERSHIP EPOCH + DIFFERENT AUTHENTIC MEMBERSHIP DIGESTS = EQUIVOCATION EVIDENCE

Two authentic records for one logical membership epoch are not two harmless candidates. The conflict is evidence that the membership authority produced incompatible histories.

### I112 — AUTHENTIC MEMBERSHIP RECORD ≠ UNIQUE MEMBERSHIP HISTORY

Cryptographic validity is local to a record. Uniqueness requires cross-view consistency evidence.

### I113 — MEMBERSHIP-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED BRANCHES AND QUARANTINE THE EQUIVOCATING ISSUER BEFORE CONSEQUENCE

Do not select a disputed membership merely because its witness quorum is locally valid.

### I114 — RECOVERY REQUIRES A FRESH HIGHER-EPOCH MEMBERSHIP FROM NON-EQUIVOCATING AUTHORITY OR EXPLICIT GOVERNANCE RESOLUTION BINDING ALL CONFLICTING BRANCH DIGESTS

Recovery must preserve the fork as evidence, name every branch it resolves, and advance authority before consequential work resumes.

## Recovery shape

```text
CONFLICT:
M2-A / digest A
M2-B / digest B

RECOVERY M3:
set_epoch > 2
trusted recovery authority / explicit governance resolution
predecessor_membership_digests = [A, B]
resolves_equivocation_digests = [A, B]
fresh current-set quorum

→ resume only after all checks succeed
```

## Failure disposition

On membership-authority equivocation:

```text
membership_authority_equivocation_detected
→ no branch selection
→ no adoption
→ no external effect
→ preserve both records
→ quarantine issuer
→ obtain explicit higher-epoch resolution
```

## Boundary

This extension does not define production PKI, BFT reconfiguration, governance voting, transparency-log architecture, consensus finality or key-revocation policy. It states the evidence invariant: **same-epoch authentic membership forks must fail closed before consequence.**
