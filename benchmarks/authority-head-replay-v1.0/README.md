# RESONANCE Authority Head Replay / Authority Rollback v1.0

Verified #031 proves that forged freshness watermarks must be authenticated. This benchmark isolates the next failure: replay of an **older but still authentic** authority head.

## Main law

> **AUTHENTIC HEAD ≠ LATEST HEAD**

## Setup

The proof-authority history contains two authentic signed heads:

```text
H7: generation 7 / R1 ACTIVE
H9: generation 9 / R2 ACTIVE / supersedes R1
```

Both H7 and H9 have valid deterministic HMAC-SHA256 authentication envelopes. Region B can be stale at R1/generation 7 even after the verifier has already observed authentic H9.

## Unsafe replay

An attacker replays authentic H7. Signature/MAC validation succeeds. A verifier that treats `authentic == current` sees region B generation 7 and head generation 7, declares the view fresh, and authorizes one effect.

## Safe anti-rollback rule

The verifier persists a monotonic trusted checkpoint:

```text
max_authenticated_generation_seen = 9
```

Then:

```text
replayed authentic head generation 7
7 < 9
→ authority_head_rollback_detected
→ HOLD
→ zero effects
```

The checkpoint is stored durably and is re-read after verifier restart.

## Score

1. Authentic generation-7 control succeeds before any later generation is known — 2.
2. Replayed authentic generation-7 head fools an authentication-only verifier after generation 9 exists — 2.
3. Monotonic trusted checkpoint rejects the replay with zero effects — 2.
4. Durable anti-rollback checkpoint survives verifier restart and still rejects H7 — 2.
5. Authentic current generation-9 head plus synchronized R2 succeeds once — 2.

Total: **10/10**.

## Boundary

HMAC is a deterministic test fixture, not production PKI. The benchmark models one verifier-local durable high-watermark. Production systems may derive monotonic currentness from trusted checkpoints, witnesses, transparency logs, quorum/consensus, hardware monotonic state, or another mechanism. This benchmark does not claim one universal architecture.