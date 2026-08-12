# RESONANCE Multi-Witness Quorum Split-Brain v1.0

## Question

Can two verifiers each obtain a locally valid `2-of-3` witness quorum for incompatible authority heads?

## Law under test

> **LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM.**

A threshold count is a local property. It does not by itself prove that another verifier has not obtained a conflicting threshold certificate over the same witness-set epoch and logical round.

## Fixture

Witness set `set-A`, epoch `1`, threshold `2-of-3`:

```text
W1
W2
W3
```

Authority heads:

```text
H7 → generation 7 / R1 ACTIVE
H9 → generation 9 / R2 ACTIVE
```

At witness round `50`:

```text
QC-A → H9
  W1 signs H9
  W2 signs H9

QC-B → H7
  W2 signs H7
  W3 signs H7
```

Every individual statement authenticates. Each certificate independently contains two distinct valid members from the same 3-member witness set.

The two quorum certificates intersect at `W2`, which has signed incompatible statements for the same witness-set epoch and logical round.

## Unsafe path

An isolated verifier shown only `QC-B` sees a valid `2-of-3` certificate for H7 and a matching generation-7 regional authority replica. It accepts and commits one external effect.

## Safe path

Before consequence, quorum certificates are gossiped/cross-checked.

If two locally valid certificates have:

- the same witness-set identity,
- the same witness-set epoch,
- the same logical round,
- different authority-head digests,
- and an overlapping signer issued incompatible authentic statements,

then the result is:

```text
conflicting_quorum_certificates
→ HOLD
→ quarantine equivocating witness identity
→ 0 rows
→ 0 external effects
```

The verifier does not choose the more permissive majority.

## Recovery control

After `W2` is quarantined, neither conflicting round-50 certificate still meets threshold using non-quarantined signers.

At round `51`, non-conflicting `W1 + W3` both authenticate H9. Their fresh `2-of-3` certificate succeeds exactly once, demonstrating that conflict handling does not permanently freeze the witness set.

## Scope

This is a deterministic benchmark model using HMAC-SHA256 test identities, PostgreSQL state, and a Dockerized HTTP effect boundary. It is not a production Byzantine consensus protocol, PKI design, quorum-system proof, or external safety certification.

The test isolates one property: **two local threshold certificates can both be valid while being globally incompatible, and quorum intersection becomes useful only if conflicting cross-view evidence is actually compared.**
