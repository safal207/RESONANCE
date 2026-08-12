# TTP Extension — Constitutional Root Currentness / Anti-Replay

## Law

> **ROOT AUTHORITY ≠ TIMELESS AUTHORITY.**

The highest configured authority is still temporal state. A root signature proves origin and integrity of one root record; it does not prove that an older root record remains current after a newer root epoch has been observed.

## Invariants

### I123 — ROOT AUTHORITY ≠ TIMELESS AUTHORITY

Root status is a position in the trust topology, not an exemption from currentness.

### I124 — AUTHENTIC ROOT RECORD BELOW A TRUSTED ROOT HIGH-WATERMARK = ROOT-AUTHORITY ROLLBACK EVIDENCE

If a verifier has already observed root epoch `E`, an authentic root record with epoch `< E` must fail closed for new consequences.

### I125 — ROOT CURRENTNESS MUST BIND A MONOTONIC ROOT EPOCH AND ROOT-RECORD DIGEST BEFORE CONSEQUENTIAL AUTHORIZATION

The verifier should persist at least:

```text
root namespace
max root epoch
root-record digest at that epoch
```

Epoch prevents backward movement. Digest prevents same-epoch content substitution.

### I126 — A RETIRED ROOT RECORD MAY REMAIN HISTORICALLY VALID BUT MUST NOT REGAIN LIVE AUTHORITY AFTER A NEWER ROOT EPOCH IS OBSERVED

Historical authenticity and current authorization are separate properties.

## Rule

```text
RECEIVE ROOT RECORD R
        ↓
AUTHENTICATE R
        ↓
VALIDATE ROOT-BOUND QUORUM / HEAD
        ↓
READ TRUSTED ROOT HIGH-WATERMARK H*
        ↓
R.epoch < H*.epoch ?
  ├─ yes → root_authority_rollback_detected
  │        → HOLD
  │        → 0 consequence
  └─ no
       ↓
R.epoch == H*.epoch
AND digest(R) != H*.digest ?
  ├─ yes → root_authority_same_epoch_conflict
  │        → HOLD
  └─ no
       ↓
ADVANCE HIGH-WATERMARK MONOTONICALLY WHEN NEEDED
       ↓
CURRENT ROOT AUTHORITY
       ↓
FENCED CONSEQUENCE
```

## Scope boundary

This rule assumes the high-watermark itself has not been rolled back. Checkpoint-storage rollback is a separate layer (Verified #033). Same-epoch root equivocation is also a separate layer. The benchmark uses deterministic HMAC fixtures and does not claim production PKI, constitutional governance, hardware trust-root security or consensus finality.
