# Engineering Signals — Trust Portability Track

This index records the verified portability milestones produced by the Liminal trusted-recovery evidence program.

```text
physical location independence
        ↓
topology independence
        ↓
verifier-output independence
        ↓
verifier-implementation independence
        ↓
trust-root / signing-authority independence
        ↓
execution-provider / transport independence
        ↓
checkpoint source-producer / control-plane independence
        ↓
upstream rotation-producer / control-plane independence
        ↓
?
genesis / historical trust-base independence
```

## Verified milestones

- [`002 — Manifest-backed Witness Recovery`](002-manifest-backed-witness-recovery.md)
- [`003 — Evidence Topology Portability`](003-evidence-topology-portability.md)
- [`004 — Normalized Verification Receipt`](004-normalized-verification-receipt.md)
- [`005 — Independent Verifier Portability`](005-independent-verifier-portability.md)
- [`006 — Trust-Provider Portability`](006-trust-provider-portability.md)
- [`007 — Execution + Evidence-Transport Portability`](007-execution-transport-portability.md) — **VERIFIED 2026-08-13**
- [`009 — Source-Producer + Control-Plane Portability`](009-source-producer-control-plane-portability.md) — **VERIFIED 2026-08-13**
- [`010 — Upstream Rotation-Authority Portability`](010-upstream-rotation-authority-portability.md) — **VERIFIED 2026-08-13**

### Latest verified gate

The upstream rotation producer and rotation control plane were changed while preserving the same portable rotation authority and downstream trusted state transition:

- primary: immutable GitHub rotation workflow + GitHub repository rotation policy;
- secondary: standalone OpenAI-isolated rotation producer + separately signed offline Ed25519 control plane.

Portable identities converged at:

- generation-1 registry: `5441072b0e550995a9ad0b27b4f3af7c7b5bf531f59e27c870ab1a8cf61789a1`
- generation-1 manifest: `b9cb0b37da2d74ece6c1cf780b06b17fbbb96f02e073ac64fb26be49cae24277`
- Portable Rotation-Authority Receipt: `9576a9f96acd278d873c65f4dcaf974a661bf5547319ba1fd60b874f89aef368`
- checkpoint-v0.3 generation 1: `cfe0ede206da217fa774cd980c20032857692c461c421ffceeeacfe863276e1a`
- next witness-v0.4: `ed385f07200b424937498374035ce11d0e4327a4c42ff701c7842bc74cee8dc6`

Immutable one-shot `31690895530` completed successfully, and its independent audit recomputed the exact proof result bytes after separately reverifying the GitHub signer and all four external Ed25519 signatures.

Core architecture lesson:

> **A causal trust transition can remain stable across producer, control-plane, execution, transport, verifier, and signing-provider changes only when authority is expressed as explicit portable contracts and every migration is bound rather than inferred.**

A first pinned run, `31689958160`, failed closed on `standalone_source_digest_mismatch`; restoring the exact signed source bytes produced the successful final proof without changing executable semantics or authority claims.

## External research signals

These entries record externally observable engineering feedback and architecture convergence. They are evidence of public technical interaction, **not** verification milestones, endorsements, partnerships, or implementation certification.

- [`007 — External Research Impact via Semantic Mutation`](007-external-research-impact-semantic-mutation.md)
- [`008 — Independent Outcome-Provenance Convergence`](008-independent-outcome-provenance-convergence.md) — **OBSERVED 2026-08-13**

### Current external-research finding

**`source_class` answers how an outcome was established; it does not by itself answer who observed it or from what vantage.**

A comparison against an independently developed, shipped `verdict_outcome` mechanism converged on the separation of decision provenance from outcome provenance and exposed `outcome_observer_id` + `outcome_vantage` as a concrete missing axis.

## Current open gate

**Genesis / Historical Trust-Base Portability v0.1**

Falsifiable question:

> Can materially independent trust-base providers establish equivalent genesis/history under a portable genesis contract and still reproduce the same downstream rotation, checkpoint, and witness semantics without inheriting the same historical Liminal predecessor registry/manifest bytes as ambient authority?

This index is descriptive only. A milestone is marked VERIFIED only after immutable execution, external recomputation, and fail-closed agreement evidence exist.
