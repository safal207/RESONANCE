# Engineering Signal 002 — Manifest-Backed Witness Recovery

**Status:** verified immutable recovery proof · evidence strengthened 12 Aug 2026  
**Verified:** 12 Aug 2026  
**Scope:** open-source engineering signal  
**System:** `safal207/Liminal` trusted-recovery witness chain  
**Not:** a claim that physical artifact paths are trustworthy by themselves

## Signal

A real GitHub Actions trusted-recovery chain moved from hard-coded artifact-path recovery to a manifest-backed evidence identity model and completed an immutable one-shot proof end to end.

The engineering transition was triggered by an ordinary but important failure: logical evidence existed and was correctly attested, while the downloaded physical artifact appeared at a nested path that the consumer did not expect.

The resulting design now separates:

```text
logical evidence identity
→ attested manifest
→ logical_id + generation
→ expected SHA-256
→ bounded physical candidate field
→ digest match
→ re-anchor
→ checkpoint attestation verification
→ verified evidence bundle
→ witness recovery
→ external verification
```

## Claim classification

### Initial verified manifest-backed transition

One-shot GitHub Actions run `31610364021` completed successfully with:

- caller commit: `d2d2fc897062b5fb211631dc2f1cd97ae76f474f`
- immutable manifest-producing checkpoint workflow: `f31b56a5e21a668bcb98791b05542652760dcc27`
- immutable manifest-backed witness workflow: `3f0af42a680f42923cb18591ba127206b2292599`
- immutable trust-root rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

That run verified the manifest-backed location/digest recovery path and the GitHub attestation checks performed by the workflow. It established that the checkpoint could be recovered by logical identity + manifest digest rather than by a hard-coded downloaded path.

### Evidence update — cross-layer signer binding

A later Evidence Bundle integration exposed a narrower trust-consistency gap that the first proof did not enforce.

The old witness policy still pinned checkpoint producer:

`d0688725bd76fdf7221e84ca7c5bfb51e363ff72`

while the manifest-backed workflow was cryptographically verifying the newer immutable checkpoint producer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

The workflow's real GitHub attestation verification was succeeding, but the normalized witness evidence inside the recovery drill was derived from the older policy signer. The first proof therefore demonstrated manifest-backed resolution and attestation verification, but it did not prove full equality of signer identity across the manifest contract, normalized recovery evidence and witness policy.

This is now explicitly corrected rather than silently reinterpreted.

Witness schema v0.2 records the signer-root migration:

```text
previous checkpoint signer: d0688725bd76fdf7221e84ca7c5bfb51e363ff72
        ↓
reason: manifest_backed_checkpoint_producer_rotation
        ↓
current checkpoint signer: f31b56a5e21a668bcb98791b05542652760dcc27
        ↓
previous proven witness anchor: 3f0af42a680f42923cb18591ba127206b2292599
```

The v0.2 root rejects the old producer for new checkpoint advancement and accepts the new producer only when signer identity agrees across the Evidence Manifest, Evidence Bundle and witness policy.

### Stronger immutable proof

The strengthened exact-head witness candidate:

`4fe0b61d28b776304d4a8e733b14dbc73c5810c7`

passed Python CI, Python Integration and Artillery WebSocket Smoke before promotion as the new immutable witness anchor.

A new one-shot proof then completed successfully:

- run: `31615095274`
- caller commit: `662992d2025c11c3f8f70939d0de48e3fe1adffb`
- immutable rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`
- immutable manifest/checkpoint producer: `f31b56a5e21a668bcb98791b05542652760dcc27`
- immutable Evidence-Bundle witness: `4fe0b61d28b776304d4a8e733b14dbc73c5810c7`

The real witness job completed:

1. bounded manifest locator resolution;
2. manifest signer verification;
3. manifest-backed checkpoint digest resolution;
4. checkpoint signer verification;
5. verified Evidence Bundle construction;
6. v0.2 witness recovery;
7. stale-checkpoint rejection;
8. explicit bundle-SHA binding in the recovery result;
9. bundle attestation;
10. witness attestation;
11. recovery-result attestation.

The independent external job then recomputed the manifest/evidence/bundle/recovery/witness chain and separately verified:

- immutable producer signer on the manifest;
- immutable producer signer on the checkpoint;
- immutable witness signer on the Evidence Bundle;
- immutable witness signer on generation-1 witness;
- immutable witness signer on the recovery result.

### Canonical chain receipt

The external recomputation produced the following exact content digests:

```text
manifest SHA-256
5f80518cb671ea0622336adbd9a0a9bd16b72ea803ad09d0ac2abd4415f58be2
        ↓
checkpoint SHA-256
74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a
        ↓
Evidence Bundle SHA-256
5eeaed5eada3b92e99b593f7fded458f2d7f8c85a3c7666619fb51203024791d
        ↓
generation-0 witness SHA-256
af12743396296c788223d3087f427b1f93d3086a5aeb9b7c8c0f38d49347e9f9
        ↓
generation-1 witness SHA-256
cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f
        ↓
recovery-result SHA-256
050c9dacc76952dd1c73b8159ef5286b465a3dce40c83147779563552ebbf972
```

The external receipt also records:

- checkpoint signer: `f31b56a5e21a668bcb98791b05542652760dcc27`
- previous checkpoint signer: `d0688725bd76fdf7221e84ca7c5bfb51e363ff72`
- previous witness anchor: `3f0af42a680f42923cb18591ba127206b2292599`
- stale checkpoint replay: rejected.

### Verified evidence artifacts for the stronger proof

Run `31615095274` produced four retained workflow artifacts:

- trust-root rotation evidence — artifact `9148849640`, `sha256:66b2053eb43a74bb3f51b65bbee31f76689b591e89eb034bf9e4906e0116718c`
- attested checkpoint + manifest evidence — artifact `9148872094`, `sha256:ec021003d885e9bbfb7be1a4c806a0a1c834dd83f751dbc836fdc7751ce9ec09`
- witness + Evidence Bundle evidence — artifact `9148889015`, `sha256:ec40934279b0c6eb824fab70135bd1be54b64e0149930219617773d0d1c2c6ea`
- external chain verification — artifact `9148903874`, `sha256:caab31a3e51612969275293489f8c013eba9fd77b0a52bfe2483d7e12ac7e10e`

They are retained by that run until 11 Sep 2026.

## Causal trajectory

```text
checkpoint evidence exists
→ consumer expects wrong physical path
→ ResolutionFailure
→ bounded locator adapter
→ ReAnchor
→ manifest-backed recovery
→ Evidence Manifest
→ digest-based identity
→ Evidence Bundle
→ hidden signer-binding drift becomes observable
→ explicit signer-root migration v0.2
→ bundle SHA bound into recovery result
→ external digest-chain recomputation
→ five independent signer-verification gates
→ VerifiedRecovery
```

The important transition is not "we fixed a path." The path failure exposed a more general distinction:

> Logical evidence identity is not the same thing as physical artifact location.

The Evidence Bundle added a second distinction:

> Successful verification steps are not enough if different trust layers normalize different signer identities.

## Why it matters

Hard-coding a downloaded path makes trust consumers accidentally depend on packaging topology. A nested directory, archive-layout change or transport-specific extraction rule can then break recovery even when the trusted evidence itself is intact.

Manifest-backed recovery moves the stable identity to evidence properties that survive path drift:

```text
logical_id
+ generation
+ producer
+ evidence_type
+ SHA-256
+ verification expectations
```

The Evidence Bundle then binds the verified manifest and verified checkpoint into a deterministic path-independent receipt:

```text
verified manifest SHA-256
+ manifest verification receipt SHA-256
+ verified evidence SHA-256
+ evidence verification receipt SHA-256
+ immutable signer identities
→ Evidence Bundle SHA-256
```

The physical locator remains an observed fact used for retrieval, not a trust identity.

The model keeps resolution, evidence binding and authority separate:

- finding bytes is not proof that they are trusted;
- matching a manifest digest is not signer verification;
- the manifest itself must be verified before its digest contract is used;
- the recovered checkpoint must pass its own signer/attestation checks;
- the Evidence Bundle does not grant authority by itself;
- signer identity must agree across manifest, bundle and witness policy;
- ambiguity fails closed rather than being ranked heuristically.

## Safety boundary

This signal proves one concrete GitHub Actions recovery chain and its recorded immutable workflow/run evidence. It does **not** prove:

- that every artifact transport or CI provider implements the same topology semantics;
- that SHA-256 identity alone establishes authority;
- that a manifest or Evidence Bundle can replace signer, policy, registry or attestation verification;
- that ambiguous matching candidates should be auto-selected;
- that the current implementation is a universal standard.

## Next verification gate

The manifest → evidence → bundle → recovery → witness chain is now explicitly bound and externally recomputed.

The next useful falsifiable gate is portability:

```text
same logical evidence identity
→ second artifact packaging/topology implementation
→ different physical locations
→ same manifest/evidence identity
→ same fail-closed trust decision
→ independent proof receipt
```

Until that happens, cross-topology portability remains **pending**.

## Primary / inspectable references

1. Liminal PR #124 — recovery routing / evidence-resolution work: https://github.com/safal207/Liminal/pull/124
2. Initial manifest-backed one-shot run: https://github.com/safal207/Liminal/actions/runs/31610364021
3. Stronger Evidence-Bundle one-shot run: https://github.com/safal207/Liminal/actions/runs/31615095274
4. Immutable manifest producer: https://github.com/safal207/Liminal/commit/f31b56a5e21a668bcb98791b05542652760dcc27
5. Previous manifest-backed witness anchor: https://github.com/safal207/Liminal/commit/3f0af42a680f42923cb18591ba127206b2292599
6. Evidence-Bundle witness anchor: https://github.com/safal207/Liminal/commit/4fe0b61d28b776304d4a8e733b14dbc73c5810c7
7. Stronger one-shot caller: https://github.com/safal207/Liminal/commit/662992d2025c11c3f8f70939d0de48e3fe1adffb

---

**RESONANCE classification:** Verified Engineering Signal with an explicit evidence update: the initial manifest-backed proof remains evidence for path-independent resolution and attestation, while the stronger Evidence-Bundle proof closes the later-discovered cross-layer signer-binding gap and binds the complete recovery chain into an independently recomputed receipt.
