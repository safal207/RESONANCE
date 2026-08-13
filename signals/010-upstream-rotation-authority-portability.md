# Engineering Signal 010 — Upstream Rotation-Authority Portability

**Status:** VERIFIED — 2026-08-13

## Signal

The Liminal trusted-recovery chain removed the remaining tested dependency on a single upstream rotation producer/control plane.

The same generation-0 → generation-1 rotation semantics were established by two materially distinct paths:

```text
immutable GitHub rotation workflow
+ GitHub repository rotation policy
        ↓
Portable Rotation-Authority Receipt
        ↑
standalone OpenAI-isolated rotation producer
+ separately signed offline Ed25519 control plane
```

The agreement did not stop at rotation-result equality. Both paths reproduced the same downstream checkpoint-v0.3 state and the same witness-v0.4 trusted transition.

## Immutable proof chain

- primary rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`
- final reusable verifier: `28d96de36267fde8e1c66ce0c5f36c2c30e44813`
- pinned caller: `5a22e30b3248416d638dc441a4fba0edd9c95edd`
- one-shot: **`31690895530` — FULL SUCCESS**

Exact-head gates on the final reusable revision before pinning:

- Python CI `31690292430` — SUCCESS
- Python Integration `31690292458` — SUCCESS
- Artillery `31690292372` — SUCCESS

## Independent roots

- external rotation control plane: `ed25519-sha256:972ce43feacdb0747fad6e0fe02d1fbe06270727600fca65b185cd94f55c1062`
- standalone rotation producer: `ed25519-sha256:26976b8f46f2d970cda4667f64a814c1a3316747fde791e4102fd5fb54942f8c`
- standalone implementation: `e8e3e0c177e018ea525c264ba6290444a803834afd6e4515895dfa120a2a548c`
- external envelope: `27186c859f6793305a8c405927db84a6f1df7e0152a645ec4dfb4597bbe4ffbb`

The external control plane signed the rotation producer contract, authorization contract, and exact pre-transition rotation intent. A distinct producer root signed the independently produced result. Both the main proof and external audit verified all four signatures and the public-root fingerprints.

## Portable identities

- logical rotation ID: `liminal.trusted-recovery.registry-rotation`
- rotation producer contract: `58e797025b5326f10bc73666034ed407a73f728ea9126170c185b5e59266889b`
- rotation authorization contract: `f23cfdb4f78f6980420c1511f7624e2aaa8d876509937c9577595c32ecbc7a1e`
- rotation intent: `d090275e16a7ad0fe161c9c05339858aa018879fd413be0e1ca7aae4ebb6c29d`
- previous registry: `bd43cb039d29245f3d7eb8b78a7a5fcde14d7bf638c4dfe98bb300b00f8670e1`
- previous manifest: `bd8aaa6162d0f7e9627e10ee6d495810820fd6fd8cd07d9d48e5d585786537b5`
- generation-1 registry: `5441072b0e550995a9ad0b27b4f3af7c7b5bf531f59e27c870ab1a8cf61789a1`
- generation-1 manifest: `b9cb0b37da2d74ece6c1cf780b06b17fbbb96f02e073ac64fb26be49cae24277`
- Portable Rotation-Authority Receipt: `9576a9f96acd278d873c65f4dcaf974a661bf5547319ba1fd60b874f89aef368`

## Downstream continuity

- checkpoint-v0.3 genesis: `0833f2463235554ab80f374fee9f14f887391e4939b7f5d082fabce4f57b821f`
- checkpoint-v0.3 generation 1: `cfe0ede206da217fa774cd980c20032857692c461c421ffceeeacfe863276e1a`
- witness-v0.4 genesis: `46c7758d25958216c07363176bea3106eceaad58f2f0bdb28ff983b56349f7c9`
- witness result: `checkpoint_witness_advanced`
- next witness: `ed385f07200b424937498374035ce11d0e4327a4c42ff701c7842bc74cee8dc6`

## Evidence

Canonical proof result:

`9e80d1dd529055b78269660301e59b94afb12cb102c0450053b5e1036418c34f`

Independent audit:

`909ce2af98e20b910d7460bb5fda45fa1ab8b703a0666e8391de6986445d03ea`

Artifacts:

- proof `9177340936` — `sha256:6b3aff98b6a5a2b63692dbd92180acb65adde417aa72847013e978244595f700`
- independent audit `9177355189` — `sha256:20c4a07561b40caf749934ba5fbb39ce1110fa96df5a006f572cb0a75f07feec`
- fresh primary rotation `9177328748` — `sha256:7926c741f547b0bf689c119b953a017ea42fa93750daf3b82bbad66505e3cff9`

## Failure that strengthened the proof

The first immutable caller run `31689958160` failed after primary signer verification and all four external signatures had already succeeded.

Reason:

`standalone_source_digest_mismatch`

Two comment-only lines had been omitted while publishing the standalone producer, so repository source bytes no longer matched the implementation digest bound into the signed producer result. The proof correctly refused to continue.

The fix restored the exact originally signed source bytes; contracts, roots, signatures, rotation claims, and executable semantics were unchanged. The corrected revision passed exact-head CI before a new immutable caller was pinned.

Principle:

> **Provenance binding is part of trust semantics even when the semantic code path is unchanged.**

## Claim boundary

This signal establishes source/control-plane portability for the tested upstream rotation step and demonstrates downstream causal convergence.

It does **not** establish independent genesis/history. Both paths deliberately begin from the same existing Liminal predecessor registry and manifest. It also does not claim organizational-governance, hardware-provenance, network-path, universal-provider, or indefinite durability independence.

## Next falsifiable question

**Genesis / Historical Trust-Base Portability v0.1**

Can materially independent trust-base providers establish equivalent genesis/history under a portable genesis contract and still reproduce the same downstream rotation, checkpoint, and witness semantics without inheriting the same historical Liminal predecessor bytes as ambient authority?
