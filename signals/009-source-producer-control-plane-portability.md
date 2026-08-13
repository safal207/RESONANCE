# Engineering Signal 009 — Source-Producer + Control-Plane Portability

**Status:** verified stronger immutable proof  
**Verified:** 13 Aug 2026  
**System:** `safal207/Liminal` trusted-recovery evidence chain  
**Scope:** checkpoint source producer + checkpoint authorization control plane  
**Not:** upstream rotation-authority portability, universal provider independence, or organizational governance

## Signal

Checkpoint trust survived a material change of both the producer that constructed the checkpoint and the control plane that authorized that producer role.

```text
GitHub Actions checkpoint producer
+ GitHub repository policy control plane
        ↓
        same logical producer contract
        same authorization contract
        same checkpoint subject
        same trusted transition
        ↑
standalone OpenAI-isolated-workspace producer
+ independently signed offline Ed25519 control plane
```

The secondary producer was not relabeled as the GitHub workflow signer. Instead, the witness authority model was migrated from a concrete signer identity to a logical contract whose implementation can be independently proven.

## Architecture result

The stronger Checkpoint Witness Authority v0.3 binds authority as:

```text
logical_producer_id
+ producer_contract_sha256
+ authorization_contract_sha256
+ evidence_type
```

Concrete signer/provider identity is **evidence about authority, not authority itself**.

This distinction is the key result of this milestone.

## Portable contract identities

Logical producer:

`liminal.trusted-recovery.checkpoint-producer`

Producer Contract SHA-256:

`72bba8eddc81e88c2e9ad24e266713e9534f6c332fec7ad5ecaa264f922b7ca3`

Authorization Contract SHA-256:

`576da1fa0c5cd70313ad1d89de88f4a7048e13fa5d0ce05c833f7bef4233a553`

Evidence type:

`trusted-recovery-consumer-checkpoint`

## Explicit legacy-authority migration

The previous witness authority was the immutable GitHub producer workflow itself. The stronger v0.3 migration preserves that causal origin rather than silently replacing it.

Legacy v0.2 witness SHA-256:

`af12743396296c788223d3087f427b1f93d3086a5aeb9b7c8c0f38d49347e9f9`

Legacy producer signer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

Canonical provider-neutral migration claim SHA-256:

`aec92a1c1100e6ea5944e042cd5e7c56f3ebc01b5a957782482231732d504f10`

Stronger v0.3 generation-0 witness SHA-256:

`8d2e44dab167f1f4613ef66257ca3c3be19f2168a87b620483628389b771ca8c`

Raw verifier output is excluded from migration identity. Verification remains mandatory, but verifier-specific bytes do not define the authority migration.

## Independent producer and control plane

Secondary control-plane root:

`ed25519-sha256:ecd3d6167557ed9d8dfbd3cccb75c72ea38da3ed09b89fa4f277cbcac3c51bb6`

Secondary producer root:

`ed25519-sha256:452f19f3bcee0a79e3907224474803a45cca5edaa2b1dff5e43b1fb7ea764408`

Standalone producer implementation SHA-256:

`e45233b9432f00f21d82c5a29875e445045f705f2d2cd1560d1312d7a5f6eccb`

The external producer used a standalone implementation without importing `liminal.*`. It independently consumed bounded rotation inputs plus signed portable contracts, built generation-1 checkpoint bytes, and only afterward compared its result with the GitHub producer output.

Both paths produced the same checkpoint subject:

`74096c48cd730c55dd2f486f1af4b211b4f7f1ce38613134be645055ff1f946a`

## Stronger immutable proof

Reusable verifier:

`d4d498288afac1d26e37f62ff8a8c17746d25d8d`

Exact-head gates before pinning:

- Python CI `31673332543` — **SUCCESS**
- Python Integration `31673332545` — **SUCCESS**
- Artillery `31673332564` — **SUCCESS**

Pinned caller:

`b6cf8dbe1f3e846e2abc430f905e69a07a5fb78f`

Successful one-shot:

`31673608370` — **FULL SUCCESS**

Immutable upstream checkpoint producer:

`f31b56a5e21a668bcb98791b05542652760dcc27`

## Portable outcome

Both paths independently advanced the same stronger v0.3 witness with:

```text
authorized: true
reason: checkpoint_witness_advanced
```

Next v0.3 witness SHA-256:

`efc242be9ebeb3bf898c3cee301391525d1609d499f44c7ae4eac9ce4e5cb4ed`

Portable Source-Control Receipt SHA-256:

`9d6a90e5f079b8c8bde01ab858fa9b9050603f3245d5008b0a90d61301a5c73a`

Canonical proof-result SHA-256:

`e57156c8645c1c68ad73bff06513ccf14bb15e44f7c41d0ad96f8c814cf9aada`

Independent audit record SHA-256:

`6821468c5c6f1543ff63554c313cd306e6d812a9b9850f9a040b3dcae1683069`

## Evidence

Stronger proof:

- artifact `9170683259`
- `sha256:638de3db91e4d45e9208ac7d2b093dfb023357f3f98f36cf8c6f5ae19e64a4ab`

Independent audit:

- artifact `9170705052`
- `sha256:2023aa344dc5c95036dfe6dfdca8c6876b160d68d76756a674c1d0eb97bcb2ac`

The audit did not trust the proof's success flag. It independently reverified the immutable result signer, fresh GitHub producer signer, both external Ed25519 signatures and public-key fingerprints; then recomputed contracts, migration claim, v0.3 witness transition and Source-Control agreement, and required exact equality of the recomputed result bytes.

## Historical first proof and correction trail

An earlier immutable implementation also succeeded:

- verifier `32152ef2b8f7f134b7830743a70c6bc903b64c1c`
- one-shot `31669188983` — **SUCCESS**
- proof artifact `9169187861` — `sha256:062c509d840557e798cd20f161982df16393ddaaf33589683c063f0a692d4c1b`
- audit artifact `9169232567` — `sha256:020c8e8aed36889e1fa19401e3c4180ef2ce806a84b3547ed7d1b05927833cb7`

That proof is not deleted or retroactively called a failure. It demonstrated the earlier model. Later review exposed a stronger requirement: migration from concrete signer authority to logical authority should bind the **exact legacy signer mapping plus a canonical provider-neutral migration claim**.

The current stronger proof adds that binding. The first proof is therefore **historical and superseded for current authority semantics, not revoked**.

This is itself an engineering lesson: a successful immutable proof can remain valid evidence for its stated model while a later model narrows or strengthens the claim.

## Independence matrix

| Boundary | Result |
| --- | --- |
| Checkpoint source producer | ✅ independent in tested paths |
| Checkpoint authorization control plane | ✅ independent in tested paths |
| Concrete producer signer identity | ✅ not portable authority identity |
| Producer implementation | ✅ distinct in tested paths |
| Logical producer contract | ✅ identical |
| Authorization contract | ✅ identical |
| Checkpoint subject | ✅ identical |
| Trusted state transition | ✅ identical |
| Upstream rotation authority | ❌ still shared causal dependency |
| Organizational governance | not claimed |
| Hardware / network provenance | not claimed |

## Claim boundary

This result does **not** establish total infrastructure independence.

The secondary checkpoint producer still consumed rotation evidence whose causal authorization originated in the existing GitHub rotation chain. Therefore the remaining dependency sits one causal step upstream of checkpoint production.

## Progression

```text
physical-location independence
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
checkpoint producer / control-plane independence
        ↓
?
upstream rotation-authority independence
```

## Next falsifiable question

Can the rotation-authority input that permits a generation advance itself be produced and authorized through a materially independent producer/control plane while preserving the same downstream checkpoint subject and trusted state transition?
