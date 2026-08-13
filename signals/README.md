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
?
source-producer / control-plane independence
```

## Verified milestones

- [`002 — Manifest-backed Witness Recovery`](002-manifest-backed-witness-recovery.md)
- [`003 — Evidence Topology Portability`](003-evidence-topology-portability.md)
- [`004 — Normalized Verification Receipt`](004-normalized-verification-receipt.md)
- [`005 — Independent Verifier Portability`](005-independent-verifier-portability.md)
- [`006 — Trust-Provider Portability`](006-trust-provider-portability.md)
- [`007 — Execution + Evidence-Transport Portability`](007-execution-transport-portability.md) — **VERIFIED 2026-08-13**

The latest verified gate demonstrated the same trusted state transition across:

- GitHub Actions hosted + GitHub Actions artifact transport; and
- OpenAI/ChatGPT isolated Linux workspace + Google Drive transport.

The portable transition remained stable at:

- checkpoint SHA-256: `74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`
- Portable Trust Receipt: `2235b07a4188628091cbe94af6a16dc30516d0acea743f9b4517b58a5cbd1a80`
- next witness: `cc389524836b013bb5a416f0a9f6647d9ff252d2de79598e4df119c6e5760d2f`

## External research signals

These entries record externally observable engineering feedback and architecture convergence. They are evidence of public technical interaction, **not** verification milestones, endorsements, partnerships, or implementation certification.

- [`007 — External Research Impact via Semantic Mutation`](007-external-research-impact-semantic-mutation.md)
- [`008 — Independent Outcome-Provenance Convergence`](008-independent-outcome-provenance-convergence.md) — **OBSERVED 2026-08-13**

### Current main finding

**`source_class` answers how an outcome was established; it does not by itself answer who observed it or from what vantage.**

A comparison against an independently developed, shipped `verdict_outcome` mechanism converged on the separation of decision provenance from outcome provenance and exposed `outcome_observer_id` + `outcome_vantage` as a concrete missing axis.

## Current open gate

**Source-Producer + Control-Plane Portability v0.1**

Falsifiable question:

> Can evidence produced outside the current GitHub workflow/repository authority be bound to a provider-neutral logical producer identity and authorization contract and still reproduce the same trusted transition?

This index is descriptive only. A milestone is marked VERIFIED only after immutable execution, external recomputation, and fail-closed agreement evidence exist.
