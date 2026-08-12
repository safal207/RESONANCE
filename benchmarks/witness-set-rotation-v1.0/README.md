# RESONANCE Benchmark — Witness-Set Rotation / Membership Epoch Confusion v1.0

## Question

Can a perfectly valid quorum certificate from an old witness-set epoch still authorize a consequential action after membership authority has rotated?

## Law under test

> **VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY.**

## Topology

Old membership:

```text
set_id = set-A
set_epoch = 1
members = W1, W2, W3
threshold = 2-of-3
```

Current membership after rotation:

```text
set_id = set-B
set_epoch = 2
members = W4, W5, W6
threshold = 2-of-3
```

A membership authority signs both membership records. `M1` remains cryptographically authentic after rotation, but `M2` is the current membership authority.

## Unsafe path

An old quorum certificate is still valid under its embedded historical membership:

```text
QC-old
set-A / epoch 1
W1 + W2
head = H7
threshold satisfied
signatures valid
```

A verifier that validates only against the historical membership bundled with the certificate can still authorize a write after membership rotation.

## Safe path

Before consequence, the verifier resolves the current authenticated membership authority:

```text
QC-old membership epoch = 1
current membership epoch = 2

1 != 2
→ witness_set_authority_conflict
→ 0 adoption rows
→ 0 external effects
```

A fresh `set-B / epoch 2` quorum signed by `W4 + W5` for current H9 succeeds exactly once.

## Scorecard

1. Historical set-A QC remains cryptographically valid after rotation — 2 points.
2. Unsafe verifier accepts old-membership QC and commits one effect — 2 points.
3. Current membership authority exposes epoch/digest mismatch — 2 points.
4. Safe verifier rejects old-membership QC with zero effects — 2 points.
5. Fresh set-B QC succeeds once under current membership authority — 2 points.

Maximum: 10/10.

## Interpretation boundary

This benchmark uses deterministic HMAC-SHA256 identities as test fixtures. It models membership currentness, not production PKI, governance, BFT reconfiguration, distributed membership propagation, key lifecycle, or compromise recovery.

A later benchmark should separately test stale or replayed membership-authority views during rotation.