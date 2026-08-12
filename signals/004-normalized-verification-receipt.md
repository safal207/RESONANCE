# Engineering Signal 004 — Normalized Verification Receipt

**Status:** verified immutable proof  
**Verified:** 12 Aug 2026  
**Scope:** verifier-output representation independence  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Not:** proof of independent verifier or CI-provider agreement

## Signal

Portable trust identity does not need to inherit the byte layout of one verifier's JSON output.

A real successful GitHub Attestations verification event was retained as raw capture A. A deliberately byte-distinct, explicitly non-authoritative audit envelope of the same event was created as capture B.

The raw bytes differed, but both representations normalized to the same security-relevant verification identity, the same receipt-backed Evidence Bundle and the same witness transition.

```text
raw verifier representation A != B
        ↓
same verified security contract
        ↓
Normalized Verification Receipt A == B
        ↓
Evidence Bundle v0.2 A == B
        ↓
witness transition A == B
```

## Immutable proof

One-shot run:

`31620226592` — **SUCCESS**

Pinned caller:

`dd069652dd38ef11410650da9385b1fd923ecfd4`

Immutable normalized-receipt workflow:

`608061196ef8504a5bed8208797a14bc2dc71c50`

Immutable producer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

Immutable trust-root rotation workflow:

`e2cb6a014236bc561d03c405f4986146026041fa`

The proof workflow and pinned caller were gated by Python CI, Python Integration and Artillery.

## Byte-distinct raw evidence

```text
manifest capture A
1014a62cadb75b00bc40b0934904afefa82d827d62f171b71e1adb36412089c6

manifest capture B
9c9657efa7fd179c077fb672bcedf98983a998675ea59d97e7db8b4b5427e45a

checkpoint capture A
a86adb43d8fef225a073cddf7c77ff2df3dfada1f8062450252a38bf08b1e206

checkpoint capture B
bc9b89634bf62035289562b595d477b7ea7e0006be83da49b2cee7fc81dd8d2d
```

These raw SHA-256 values are intentionally different.

## Normalized identities

Manifest subject:

`5f80518cb671ea0622336adbd9a0a9bd16b72ea803ad09d0ac2abd4415f58be2`

Checkpoint subject:

`74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`

Normalized manifest verification receipt:

`05367cac13290c50dbd413c37b3741a6d1977f19f2b12a29f0e1e154d79e73ca`

Normalized checkpoint verification receipt:

`fc14a91512662d58a6db21263bf0dd71ce5ad2abcc09a431c027c4bb73a4db70`

Receipt-backed Evidence Bundle v0.2:

`63110899de2feb57152232b07e63a48921e3822320d6b1eb5e7cd6b016bd9892`

Attested proof result:

`49e4e3706645fb47b70251d8ad2ea0714ba4e03595cbf91c16b980d47c1c36da`

## State-transition result

Both A and B authorized exactly the same transition:

```text
authorized: true
reason: checkpoint_witness_advanced
next_witness_sha256:
cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f
```

## Independent external check

A separate job:

- recomputed raw-capture inequality;
- recomputed normalized receipt equality;
- recomputed Evidence Bundle v0.2 equality;
- checked subject/receipt/bundle bindings;
- reverified the immutable producer on manifest and checkpoint;
- verified the proof signer on both A/B receipt copies;
- verified the proof signer on both A/B Bundle v0.2 copies;
- verified the proof-result signer.

Only the A receipt/bundle copies were directly attested in the proof producer job. The B copies independently passed attestation verification because their canonical content bytes were identical.

Evidence artifacts:

- proof artifact `9150941935` — `sha256:ffc420fe9f81ba6e823a212c8c4d32ecfc90752e9a926f483327b8158c25c74a`
- external verification `9150963798` — `sha256:db4e60a85fe698be68f017b346aeac3df5ebe27d28d767045325e0c8e8e33d58`

## What changed architecturally

The verification layer now separates three identities:

```text
raw verifier bytes
        → audit identity

normalized security semantics
        → verification identity

subject + normalized receipts
        → portable Evidence Bundle identity
```

This prevents timestamps, output ordering, CLI decoration, physical path names or provider-specific JSON formatting from silently becoming trust anchors.

## Claim boundary

Capture B is **not** a second independent verifier. It is an alternate representation of the same successful GitHub verification event and is explicitly marked non-authoritative.

Therefore this signal proves **verifier-output representation independence**, not:

- independent verifier agreement;
- CI-provider independence;
- transport independence;
- cross-attestation-ecosystem equivalence.

## Next falsifiable gate

**Independent Verifier Portability v0.1**

```text
GitHub verifier
        +
independent verifier
        ↓
independently obtained verdicts
        ↓
Normalized Verification Receipt A/B
        ↓
semantic equality or fail closed
        ↓
Evidence Bundle v0.2 equality
        ↓
same recovery / witness transition
```

The normalizer must never erase a real disagreement. A mismatch in subject, signer, source, policy or verdict must remain a hard failure.
