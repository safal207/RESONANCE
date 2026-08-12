# TTP Extension — Checkpoint Rollback Resistance

Verified #032 introduced verifier-local monotonic authority-head checkpoints. Verified #033 extends the protocol to the recovery boundary where the checkpoint storage itself may be restored to an older state.

## Core law

**DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT.**

Durability across restart is weaker than monotonicity across recovery. A database can faithfully restore an old value.

## Invariants

### I91 — DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT

A checkpoint that survives ordinary process restart may still regress after backup restore, snapshot rollback, replica rewind, disaster recovery, or administrative state replacement.

### I92 — VERIFIER STATE RECOVERY MUST NOT MOVE TRUST HISTORY BACKWARD

Before consequential verification resumes after recovery, restored verifier state must be reconciled against a trusted monotonic reference outside the restored state domain.

### I93 — A LOCAL CHECKPOINT BELOW AN AUTHENTICATED INDEPENDENT HIGH-WATERMARK IS STORAGE-ROLLBACK EVIDENCE

If an independently authenticated reference proves generation `G_ext` while restored local state says `G_local < G_ext`, the verifier must treat its local trust history as rolled back rather than treating the lower value as merely current local state.

### I94 — AFTER CHECKPOINT ROLLBACK, RECONSTRUCT TRUST STATE FROM INDEPENDENT EVIDENCE BEFORE AUTHORIZING CONSEQUENCE

Consequential verification remains on hold until the verifier has reconstructed or reconciled a monotonic checkpoint from trusted evidence.

## Decision rule

```text
RECOVER / START VERIFIER
        ↓
READ LOCAL CHECKPOINT G_local
        ↓
RESOLVE AUTHENTICATED INDEPENDENT CHECKPOINT G_ext
        ↓
VERIFY WITNESS / CHECKPOINT AUTHENTICITY + SCOPE
        ↓
G_local >= G_ext ?
  ├─ no
  │    ↓
  │  checkpoint_storage_rollback_detected
  │    ↓
  │  HOLD CONSEQUENCE
  │    ↓
  │  RECONSTRUCT / RECONCILE TRUST HISTORY
  │    ↓
  │  PERSIST MONOTONIC CHECKPOINT
  │
  └─ yes
        ↓
RECEIVE AUTHORITY HEAD H
        ↓
AUTHENTICATE H
        ↓
H.generation >= trusted checkpoint ?
  ├─ no → authority_head_rollback_detected → HOLD
  └─ yes
        ↓
VERIFY AUTHORITY VIEW / RULE / PROOF / SCOPE
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE RECOVERY → STORAGE CURRENTNESS → HEAD CURRENTNESS → PROOF → EFFECT
```

## Recovery contract

A safe verifier recovery path should preserve evidence of:

- restored local checkpoint identity and generation;
- recovery/snapshot identity if available;
- independent checkpoint or witness identity;
- authentication result for the independent evidence;
- scope/namespace binding;
- exact head digest or log position bound by the witness;
- rollback comparison result;
- reconstruction/reconciliation action;
- reconstructed checkpoint identity;
- subsequent authority-head anti-rollback result;
- any resulting external effect.

## Failure semantics

```text
local checkpoint < authenticated independent checkpoint
→ checkpoint_storage_rollback_detected
→ HOLD
→ no consequential write
```

Unknown, missing, conflicting, unauthenticated, or out-of-scope independent recovery evidence must not be silently interpreted as permission to trust the restored local checkpoint.

## Composition with #032

Checkpoint rollback resistance sits before ordinary authority-head anti-rollback:

```text
CHECKPOINT STORAGE CURRENTNESS
        ↓
AUTHORITY HEAD AUTHENTICITY
        ↓
AUTHORITY HEAD ANTI-ROLLBACK
        ↓
AUTHORITY VIEW CURRENTNESS
        ↓
PROOF AUTHORITY / APPLICABILITY
        ↓
CONSEQUENCE
```

A correct head anti-rollback comparison is only as trustworthy as the high-watermark supplied to it.

## Boundary

Verified #033 uses a PostgreSQL row restore and a deterministic HMAC witness fixture. It does not prescribe a production checkpoint architecture. Production implementations may use external transparency logs, multiple independent witnesses, quorum checkpoints, secure hardware monotonic counters, remote attestation, append-only storage, or other mechanisms.

This extension does not yet solve witness rollback, witness equivocation, quorum disagreement, first-contact/bootstrap trust, malicious recovery administrators, or simultaneous rollback of both verifier and witness state.
