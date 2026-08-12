# Engineering Signal 003 — Evidence Topology Portability

**Status:** verified immutable portability proof  
**Verified:** 12 Aug 2026  
**Scope:** open-source engineering signal  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Not:** proof of CI-provider independence

## Signal

The same producer-attested evidence bytes were deliberately repackaged into two different physical artifact topologies — including changed directory depth and changed filenames/extensions — and produced the same evidence identity, Evidence Bundle, recovery authorization and witness transition.

The important transition is:

```text
same logical_id + generation
+ same bytes / SHA-256
+ same verified signer contract

physical topology A != physical topology B
        ↓
same verified evidence identity
        ↓
same Evidence Bundle
        ↓
same recovery decision
        ↓
same witness transition
```

## Verified fact

The immutable GitHub Actions one-shot run completed successfully:

- run: `31617370441`
- caller: `cf258a247c9ea4393d16d3508b6dc03618b2b768`
- immutable portability workflow: `2a71b4c77f7a9271dd47ffc5002d3fc254dc635a`
- immutable checkpoint/manifest producer: `f31b56a5e21a668bcb98791b05542652760dcc27`
- immutable trust-root rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

The portability workflow SHA passed Python CI, Python Integration and Artillery smoke checks before it was pinned as the experiment signer.

## Two physical topologies

The exact same attested manifest and checkpoint bytes were materialized as:

```text
Topology A
  topology-a/evidence-manifest-v0.1.json
  topology-a/checkpoint-generation-1.json

Topology B
  topology-b/meta/opaque-evidence-index.bin
  topology-b/transport/layers/opaque-blob.dat
```

This changes both path depth and filename/extension while preserving the subject bytes.

## Content identities

The successful proof recorded:

- manifest SHA-256: `5f80518cb671ea0622336adbd9a0a9bd16b72ea803ad09d0ac2abd4415f58be2`
- checkpoint SHA-256: `74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`
- portable Evidence Bundle SHA-256: `e3a11b8e98e1f5c7d5c56326d91a641848536f3bedb4be3f51fc1237d0a30d13`
- topology-portability result SHA-256: `b83584388985c82b88204835ffb4fa59d99e44598a6fa86a515f65b88ee57493`

Both physical topologies produced:

- `verified_recovery`;
- `checkpoint_witness_advanced`;
- the same next-witness SHA-256;
- the same canonical Evidence Bundle SHA-256.

## External verification

The external job did not trust the portability workflow's verdict alone. It independently recomputed:

- manifest digest equality;
- checkpoint digest equality;
- Evidence Bundle digest equality;
- recovery authorization equality;
- witness decision equality;
- next-witness digest equality.

It then successfully ran producer attestation verification on all four physical subjects, including the renamed nested copies:

```text
opaque-evidence-index.bin  → producer attestation verified
opaque-blob.dat            → producer attestation verified
```

The externally verified result therefore demonstrates that, for this GitHub Actions / GitHub Attestations chain, moving or renaming an unchanged subject did not invalidate its content-bound producer attestation.

The external job also verified the immutable portability workflow signer on the portable Evidence Bundle and the portability-result receipt.

## Evidence artifacts

The run retained:

- portability evidence artifact `9149843672` — `sha256:e8b4861ed9c4ff65b7a50861a18f1b2760b2cbea1b419ccce657b91d22a403af`
- external verification artifact `9149864501` — `sha256:7a4c001786457ac7b4d9e039c9744eb3a7660b0a2dcdf08053dbfdeca54d8543`
- producer checkpoint/manifest artifact `9149812316` — `sha256:1233a206a51ed00eef4c52aa64e4aff095b4228e4b5245b355fe8e41ed476daf`
- rotation evidence artifact `9149799718` — `sha256:ad4b7e9d4bdc98715d37a70a8fb4f599408fbff55f3242f025fdc73b17773738`

The run's 30-day artifacts are scheduled to expire on 11 Sep 2026.

## Causal trajectory

```text
hard-coded nested-path failure
→ ResolutionFailure identified
→ logical evidence identity separated from physical location
→ bounded Evidence Locator
→ deterministic ReAnchor
→ attested Evidence Manifest
→ digest-backed resolution
→ Evidence Bundle
→ signer-binding drift discovered and corrected
→ bundle-backed immutable recovery proof
→ two deliberately different physical topologies
→ same bundle + same recovery/witness decision
→ external verification on renamed subjects
→ topology portability verified
```

This is why the original path bug mattered: a packaging failure became a falsifiable architecture question about what evidence identity actually consists of.

## Why it matters

A trustworthy consumer should not accidentally treat archive layout, extraction directory or filename as authority when the stable identity is already bound by logical identity, content digest and signer verification.

The current separation is:

```text
physical path / filename  → retrieval concern
logical_id + generation   → semantic identity
SHA-256                   → content identity
signer / attestation      → verification authority
Evidence Bundle           → proof receipt
recovery policy           → authorization
```

The experiment shows these layers can survive a substantial packaging-topology change without changing the final trust decision.

## Safety boundary

This signal does **not** show that:

- modified bytes remain trusted;
- arbitrary candidates may be selected when several digest matches exist;
- filename/path checks can be removed from bounded retrieval policy;
- SHA-256 alone establishes authority;
- signer, source, policy or attestation checks can be skipped;
- the proof is portable across independent CI providers or verifier implementations.

Ambiguity, digest drift, out-of-bounds candidates and verification failure remain fail-closed conditions.

## Newly exposed boundary: verification receipt portability

Topology portability is now verified, but a deeper portability boundary remains.

The current Evidence Bundle includes SHA-256 digests of raw verification JSON. Raw verifier output can differ across runs or verifier implementations even when the security-relevant verification semantics are equivalent.

Therefore:

```text
artifact topology portability     → VERIFIED
verification receipt portability  → NOT YET VERIFIED
provider portability              → NOT YET VERIFIED
```

This means the next cross-provider test should not simply require identical current Evidence Bundle bytes.

## Next verification gate

Define **Normalized Verification Receipt v0.1**.

The receipt should canonically bind security-relevant facts such as:

```text
subject digest
signer workflow identity
signer workflow commit
source repository / ref
verification result
runner-policy constraints
attestation/provenance identity
raw evidence reference
```

while keeping provider-specific/raw verifier JSON as referenced evidence rather than semantic identity.

The next falsifiable experiment then becomes:

```text
same logical evidence
→ verifier / transport A
→ verifier / transport B
→ normalized verification semantics agree
→ same authorization decision
→ portable verification receipt
```

## Primary / inspectable references

1. Liminal PR #124: https://github.com/safal207/Liminal/pull/124
2. Successful portability one-shot: https://github.com/safal207/Liminal/actions/runs/31617370441
3. Immutable portability workflow: https://github.com/safal207/Liminal/commit/2a71b4c77f7a9271dd47ffc5002d3fc254dc635a
4. Pinned one-shot caller: https://github.com/safal207/Liminal/commit/cf258a247c9ea4393d16d3508b6dc03618b2b768
5. Immutable producer: https://github.com/safal207/Liminal/commit/f31b56a5e21a668bcb98791b05542652760dcc27

---

**RESONANCE classification:** Verified Engineering Signal — identical trusted evidence bytes preserved the same bundle and recovery/witness decision across two distinct packaging topologies, with external attestation verification succeeding on renamed nested subjects.
