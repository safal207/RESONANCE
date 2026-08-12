# TTP Extension — Authority Head Anti-Rollback

## Purpose

Authenticated authority heads are necessary but not sufficient for currentness. An older head may remain cryptographically valid after newer authority history exists.

> **AUTHENTIC HEAD ≠ LATEST HEAD**

## Rule

Before an authority head can be used to authorize a consequential transition:

1. Authenticate signer/key identity, authority namespace, canonical payload, and integrity/signature.
2. Read a trusted monotonic checkpoint `G*` representing the highest authenticated authority generation already accepted by this verifier or reconstructed from trusted witness evidence.
3. Reject or hold any head whose generation is below `G*`.
4. Advance `G*` monotonically when a newer authenticated head is accepted.
5. Only then compare regional authority view, rule status/digest/generation, proof scope, and execution authority.
6. Persist or reconstruct anti-rollback state across verifier restart.

## Decision chain

```text
AUTHORITY HEAD H
      ↓
AUTHENTICATE H
      ↓
READ TRUSTED HIGH-WATERMARK G*
      ↓
H.generation >= G* ?
  ├─ no → authority_head_rollback_detected → HOLD
  └─ yes
       ↓
   ADVANCE G* MONOTONICALLY
       ↓
   VERIFY AUTHORITY VIEW CURRENTNESS
       ↓
   VERIFY RULE / PROOF / SCOPE
       ↓
   CURRENT AUTHORITY ADOPTS
       ↓
   FENCED CONSEQUENCE
       ↓
   PROVE HEAD → HISTORY → VIEW → PROOF → EFFECT
```

## Invariants

- **I87 — AUTHENTIC HEAD ≠ LATEST HEAD.**
- **I88 — CURRENTNESS MUST BIND TO MONOTONIC ANTI-ROLLBACK STATE OR AN EQUIVALENT TRUSTED CHECKPOINT.**
- **I89 — AN AUTHENTIC HEAD BELOW THE TRUSTED HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE.**
- **I90 — ANTI-ROLLBACK STATE MUST SURVIVE VERIFIER RESTART OR BE RECONSTRUCTED FROM TRUSTED WITNESS/CHECKPOINT EVIDENCE.**

## Why authentication alone is insufficient

A signature or MAC answers: *was this statement issued by the trusted authority and left unmodified?*

It does not answer: *is this the newest statement that authority has issued?*

Replay therefore remains possible without a monotonic history mechanism.

## Evidence model

A verifier should preserve or obtain evidence for:

```text
head identity
+ authenticated payload
+ generation
+ prior accepted high-watermark
+ high-watermark update
+ regional authority view
+ proof/rule binding
+ execution authority
+ consequential effect
```

## Recovery

If monotonic checkpoint state is missing, lower than expected, conflicting, or cannot be reconstructed from trusted evidence:

```text
CURRENTNESS UNKNOWN
→ HOLD
→ RECOVER / RECONCILE CHECKPOINT HISTORY
→ DO NOT CHOOSE THE PERMISSIVE HEAD
```

## Interpretation boundary

The Verified #032 benchmark uses a verifier-local PostgreSQL high-watermark and deterministic HMAC fixture. This extension does not mandate that architecture. Production anti-rollback may use transparency logs, independent witnesses, quorum/consensus, hardware monotonic counters, or other trusted checkpoint mechanisms.

A local durable database that can itself be restored to an older snapshot is not automatically rollback-resistant. That is a separate trust surface.

See `reports/verified/032-authority-head-replay/REPORT.md`.
