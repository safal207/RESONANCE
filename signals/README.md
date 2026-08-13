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
?
upstream rotation-authority independence
```

## Verified milestones

- [`002 — Manifest-backed Witness Recovery`](002-manifest-backed-witness-recovery.md)
- [`003 — Evidence Topology Portability`](003-evidence-topology-portability.md)
- [`004 — Normalized Verification Receipt`](004-normalized-verification-receipt.md)
- [`005 — Independent Verifier Portability`](005-independent-verifier-portability.md)
- [`006 — Trust-Provider Portability`](006-trust-provider-portability.md)
- [`007 — Execution + Evidence-Transport Portability`](007-execution-transport-portability.md) — **VERIFIED 2026-08-13**
- [`009 — Source-Producer + Control-Plane Portability`](009-source-producer-control-plane-portability.md) — **VERIFIED 2026-08-13**

### Latest verified gate

The checkpoint source producer and checkpoint authorization control plane were changed without impersonating the legacy GitHub signer:

- primary: GitHub Actions checkpoint producer + GitHub repository policy control plane;
- secondary: standalone OpenAI-isolated-workspace producer + independently signed offline Ed25519 control plane.

Portable identities remained stable at:

- checkpoint SHA-256: `74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`
- stronger v0.3 witness root: `8d2e44dab167f1f4613ef66257ca3c3be19f2168a87b620483628389b771ca8c`
- next v0.3 witness: `efc242be9ebeb3bf898c3cee301391525d1609d499f44c7ae4eac9ce4e5cb4ed`
- Portable Source-Control Receipt: `9d6a90e5f079b8c8bde01ab858fa9b9050603f3245d5008b0a90d61301a5c73a`

Core architecture lesson:

> **Authority is a logical contract. A concrete signer/provider is evidence about that authority, not the authority itself.**

The latest stronger immutable one-shot is `31673608370`. An earlier successful source/control proof (`31669188983`) remains historical evidence but is superseded for current authority semantics by stronger exact-legacy-signer and canonical migration-claim binding.

## External research signals

These entries record externally observable engineering feedback and architecture convergence. They are evidence of public technical interaction, **not** verification milestones, endorsements, partnerships, or implementation certification.

- [`007 — External Research Impact via Semantic Mutation`](007-external-research-impact-semantic-mutation.md)
- [`008 — Independent Outcome-Provenance Convergence`](008-independent-outcome-provenance-convergence.md) — **OBSERVED 2026-08-13**

### Current external-research finding

**`source_class` answers how an outcome was established; it does not by itself answer who observed it or from what vantage.**

A comparison against an independently developed, shipped `verdict_outcome` mechanism converged on the separation of decision provenance from outcome provenance and exposed `outcome_observer_id` + `outcome_vantage` as a concrete missing axis.

## Current open gate

**Upstream Rotation-Authority Portability v0.1**

Falsifiable question:

> Can the causal rotation-authority input that permits checkpoint generation advance itself be independently produced and authorized under provider-neutral contracts while preserving the same downstream checkpoint subject and trusted transition?

This index is descriptive only. A milestone is marked VERIFIED only after immutable execution, external recomputation, and fail-closed agreement evidence exist.
