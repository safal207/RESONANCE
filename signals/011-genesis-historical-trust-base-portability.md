# Engineering Signal 011 — Genesis / Historical Trust-Base Portability

**Status:** VERIFIED — 2026-08-14

## Signal

The Liminal trusted-recovery chain removed the tested dependency on a shared genesis manifest and shared historical registry bytes.

Two independently rooted histories now converge only at a normalized terminal trust-state layer:

```text
Root A
GitHub OIDC trust-root rotation history
        ↓
independently valid history A
        ↓
semantic trust state
        ↑
independently valid history B
        ↑
separately signed Ed25519 genesis Root B
```

The histories are intentionally not byte-identical. Their genesis manifests, history tips, and registries are different. Portability is established because both histories independently validate, carry no shared manifest identity or hidden cross-root dependency, and normalize to the same terminal authorization state.

## Immutable proof chain

- final reusable verifier: `64116d0eea55a874ac7f63b733416df39108d7a7`
- pinned caller: `b530e5818bf28e170552e5d194d01c7f2463f483`
- one-shot: **`31763346787` — FULL SUCCESS**
- primary Root A rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

Exact-head gates on the reusable verifier before pinning:

- Python CI `31763123291` — SUCCESS
- Python Integration `31763123300` — SUCCESS
- Artillery `31763123298` — SUCCESS

The one-shot performed a fresh Root A rotation drill, verified its GitHub attestation, verified the independently signed Root B history, produced the portability result, attested that result, then ran a separate audit job that reverified the result signer and Root A signer and recomputed the receipt from artifact bytes.

## Independent genesis identities

Root A genesis authority:

`github-oidc:safal207/Liminal:trusted-recovery-trust-root-rotation-drill@e2cb6a014236bc561d03c405f4986146026041fa`

Root B genesis authority:

`ed25519-sha256:bba40ffa1bb8bf5db3ecb6f0b1c7e28d67462b15694dd357fe7a7e7825e842c2`

Root B was bootstrapped with its own builder/verifier workflow identities and its own policy/lock material. The detached Ed25519 private key was not committed; the repository contains only the public key and signed history envelope.

## Independent histories

Root A:

- genesis manifest: `bd8aaa6162d0f7e9627e10ee6d495810820fd6fd8cd07d9d48e5d585786537b5`
- terminal manifest: `b9cb0b37da2d74ece6c1cf780b06b17fbbb96f02e073ac64fb26be49cae24277`
- terminal registry: `5441072b0e550995a9ad0b27b4f3af7c7b5bf531f59e27c870ab1a8cf61789a1`

Root B:

- genesis manifest: `b4e5a317c841fe20eb6b20e38bb6e43f636b7fdcfc097bf4a3939253f0ea7e82`
- terminal manifest: `6fc61082148daac72d405d6a305ece0cf9bdde0e015f882553746761f7556c7b`
- terminal registry: `acc16847c0cc89da4c5f32ba4ba46f462f6ed4dde526e2442bb3a197a3de51d2`

The comparator requires:

- distinct genesis authorities;
- distinct genesis manifests;
- no shared manifest digest anywhere in either history;
- distinct registry digests;
- no Path A manifest/registry identity smuggled into Path B metadata;
- independent registry validation before semantic comparison.

## Portable terminal state

Both histories normalize to the same semantic trust-state digest:

`ceca17a68e8f469fdfb847ca7a72b80b6214507910c4e99670ec0f33efa1ef91`

The normalized state retains current authorization semantics:

- trust domain;
- authority IDs and threshold;
- rotation and authorization contract digests;
- active builder/verifier workflow identities and Git blob identities;
- active policy-material digests;
- authorization scope.

It excludes historical provenance that describes how the state was reached rather than what is currently authorized, including generation number, predecessor-manifest pointer, registry paths, and policy source commits.

## Evidence

Portable receipt:

`af140d709a13c12b875c6bbf300b8efd9730edf701dbfc22410adbb69ccc225b`

Canonical proof result:

`1806f984b7d55bf40fc00f0e891ed066b251464857d5d3e4bba4c74efcf8806d`

Independent audit:

`5fc92c9429cf4e30dc5161a98891d4c32954a5321e11b9a646694c334f804cc8`

Root B signed envelope:

`d3a06e98d74bfe4639f217c1e664c6039b29a978f8c2a4485e8ed1459e3f24d4`

Artifacts:

- proof `9205405698` — `sha256:92fd006f683e7283ca9963b8fda0ebb2f8849499fc24ac8ef1e6bff1116767cb`
- independent audit `9205412961` — `sha256:8691e4e6e2f1e747947ecc7753c7cc3caef5f8ab0dde052ca2d7890a25b52129`
- fresh Root A rotation `9205400046` — `sha256:6562e9cae9b581add8f577c434307b4286dad6e79b7b11f55acd1a4768431741`

The external audit reproduced the exact portable receipt digest from bundled Root A and Root B history material after independently revalidating both registries and the Root B Ed25519 signature.

## What changed architecturally

Before this signal, upstream rotation production/control could move between independent providers, but both paths still inherited the same historical Liminal predecessor bytes.

Now the trust model is:

```text
history provenance A ≠ history provenance B
              ↓
independent validation
              ↓
portable authorization semantics
              ↓
same terminal trust-state digest
```

Principle:

> **Trust portability does not require identical history bytes; it requires independently valid histories that converge on the same explicitly normalized authorization semantics.**

## Claim boundary

This signal establishes, for the tested two-generation construction:

- cryptographic genesis independence;
- historical manifest/registry independence;
- fail-closed cross-root dependency detection;
- terminal semantic trust-state convergence.

It does **not** establish:

- organizational-governance independence;
- hardware-provenance independence;
- storage-provider independence;
- network-path independence;
- universal provider independence;
- indefinite multi-provider durability.

It also does not claim that raw downstream checkpoint/witness bytes are history-independent. Existing checkpoint representations still carry concrete predecessor registry/manifests. This signal proves portability at the normalized terminal trust-state layer, not byte identity of every downstream representation.

## Next falsifiable question

**Downstream Causal-State Portability Across Independent Histories v0.1**

Can independently rooted histories authorize the same next logical checkpoint/witness transition through portable semantic references, without forcing downstream state objects to inherit one concrete registry/history digest as ambient identity?
