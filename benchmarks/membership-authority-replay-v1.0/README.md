# RESONANCE Membership Authority Replay / Stale Rotation View v1.0

## Question

Can a verifier safely treat an authenticated witness-membership record as current merely because its signature is valid?

## Law

> **AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY.**

## Deterministic scenario

Historical membership:

```text
M1
set-A / epoch 1
members = W1 W2 W3
threshold = 2
```

Current membership:

```text
M2
set-B / epoch 2
members = W4 W5 W6
threshold = 2
predecessor = digest(M1)
```

The verifier has already authenticated M2 and persisted a monotonic membership checkpoint:

```text
max_membership_epoch_seen = 2
membership_digest = digest(M2)
```

An attacker or stale cache later presents the old but authentic M1 together with a historically valid W1+W2 quorum for H7.

Unsafe verifier:

```text
M1 signature valid
QC-old valid under M1
H7 authentic
regional R1 / generation 7 / ACTIVE

→ accepts stale membership as current
→ commits one external effect
```

Safe verifier:

```text
M1 authentic = true
presented set_epoch = 1
trusted membership checkpoint = 2

1 < 2
→ membership_authority_rollback_detected
→ 0 effects
```

Fresh M2 plus a current W4+W5 quorum for H9 succeeds exactly once.

## Scorecard

1. M1 and M2 authenticate and the successor chain/checkpoint establishes epoch 2 as observed current membership — 2 points.
2. Unsafe verifier accepts replayed M1 + old quorum and commits one external effect — 2 points.
3. Safe verifier detects authentic membership rollback before consequence — 2 points.
4. The stale M1 record remains cryptographically valid; only monotonic membership-currentness evidence rejects it — 2 points.
5. Fresh M2 + current quorum + H9 succeeds exactly once — 2 points.

## Boundary

This benchmark uses deterministic HMAC-SHA256 fixtures and a persisted PostgreSQL membership checkpoint. It is not a production PKI, BFT membership protocol, transparency log or governance mechanism. Rollback of the checkpoint storage itself and conflicting membership-authority issuers are separate verification surfaces.