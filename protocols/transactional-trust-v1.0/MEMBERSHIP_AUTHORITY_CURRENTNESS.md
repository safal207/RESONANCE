# TTP Extension — Membership Authority Currentness / Anti-Replay

## Law

> **AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY.**

A witness-membership record can remain cryptographically valid after a successor membership has taken over. Consequential authorization therefore requires both membership authenticity and anti-rollback currentness evidence.

## Required evidence

A membership record that may authorize consequence should bind at least:

- membership namespace;
- witness-set identity;
- monotonic set epoch;
- exact member identities;
- threshold policy;
- membership digest;
- predecessor / successor relation or equivalent lineage evidence;
- issuance generation when relevant.

A verifier should retain a monotonic membership high-watermark or equivalent trusted anti-rollback evidence.

## Decision rule

```text
RECEIVE MEMBERSHIP M + QC
        ↓
AUTHENTICATE M
        ↓
READ TRUSTED MEMBERSHIP CHECKPOINT C
        ↓
M.epoch < C.epoch?
  ├─ yes → membership_authority_rollback_detected → HOLD
  └─ no
       ↓
M.epoch == C.epoch?
  ├─ yes → REQUIRE set_id + membership_digest + threshold == C
  └─ no
       ↓
     REQUIRE AUTHENTIC FORWARD LINEAGE
     BEFORE ADVANCING CHECKPOINT
       ↓
VALIDATE QC AGAINST CURRENT M
       ↓
CHECK QUORUM CONSISTENCY
       ↓
CHECK AUTHORITY HEAD / VIEW / PROOF
       ↓
FENCED CONSEQUENCE
```

## Invariants

### I107 — AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY

Cryptographic validity proves origin and integrity, not that the configuration still holds live authority.

### I108 — MEMBERSHIP CURRENTNESS MUST BIND TO A MONOTONIC SET-EPOCH / MEMBERSHIP-DIGEST CHECKPOINT OR EQUIVALENT ANTI-ROLLBACK EVIDENCE

The verifier needs evidence that membership history has not moved backward.

### I109 — AUTHENTIC MEMBERSHIP BELOW THE TRUSTED MEMBERSHIP HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE

Once epoch 2 has been observed, an authentic epoch-1 record is historical evidence, not current authority.

### I110 — FRESH CURRENT-MEMBERSHIP QUORUM EVIDENCE IS REQUIRED TO RESTORE LIVE AUTHORITY AFTER ROTATION

A current membership configuration must supply current quorum evidence before new consequences resume.

## Failure disposition

On stale membership replay:

```text
membership_authority_rollback_detected
→ no adoption
→ no external effect
→ retain trusted membership checkpoint
→ resolve current membership
→ require current-set quorum evidence
```

Do not overwrite a higher trusted membership epoch merely because an older record authenticates.

## Boundary

This rule does not specify production PKI, BFT membership governance, transparency logs, distributed checkpoint witnesses or synchrony assumptions. It states the narrower evidence invariant: **membership authenticity is insufficient without anti-rollback currentness.**
