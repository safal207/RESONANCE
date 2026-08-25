# Engineering Signal 014 — Causal Fork / Reconciliation Portability

**Status:** VERIFIED — 2026-08-25

## Signal

Liminal now supports an explicitly verified portable causal fork followed by a two-parent reconciliation.

A previously verified portable chain advances to causal epoch 2, then splits into two independently evidenced branches with genuinely different semantic states at causal epoch 3. Both branch authorities subsequently authorize one new reconciled semantic state at causal epoch 4.

The reconciliation preserves both parent lineages rather than selecting a winner and erasing the other branch.

```text
portable causal epoch 2
          │
          ├── Branch A → semantic state A ──┐
          │                                 │
          └── Branch B → semantic state B ──┤
                                            ▼
                                CausalReconciliationRef
                                            │
                                            ▼
                               portable causal epoch 4
```

Branch A is GitHub OIDC attested. Branch B is signed by a separate detached Ed25519 authority. Their raw providers, signer identities, and evidence provenance remain outside portable fork/reconciliation identity.

## Fractal Causal Refactoring diagnosis

The previous gate proved multi-epoch convergence only when independent histories followed the same semantic trajectory.

A tempting next change would have been to relax the equality check and let a later linear checkpoint pick one divergent predecessor. That would have repaired the visible rejection while silently deleting one branch from the causal model.

The intended idea was:

```text
reconciliation = one state authorized by both divergent causal lineages
```

The inherited linear representation offered:

```text
next checkpoint = one state + one previous checkpoint digest
```

The **First Meaningful Divergence** was therefore not the semantic comparison. It was the transition topology.

> **A reconciliation is a DAG join, not a relaxed linear transition.**

The repair point was the checkpoint/witness ancestry model:

```text
single predecessor
        ↓
canonical two-parent lineage set
```

## New portable primitives

### ForkBranchRef

Each branch carries a provider-free reference binding:

- exact common `CausalStateRef`;
- logical branch ID;
- next branch `CausalStateRef`;
- branch contract;
- branch authorization contract.

The provider, signer authority, and evidence-provenance digest authorize the branch observation, but do not become portable branch identity.

### CausalReconciliationRef

The reconciliation reference binds:

- exact common ancestor state reference;
- exact common ancestor checkpoint and witness;
- both branch state references;
- both branch references;
- both branch checkpoint tips;
- both branch witness tips;
- canonical parent-set digest;
- reconciled result state reference;
- reconciliation contract;
- reconciliation authorization contract.

Parent order is canonicalized by branch checkpoint digest. Reversing branch input order produces the same portable reconciliation bytes.

### Two-parent checkpoint and witness

The reconciled checkpoint contains a sorted two-parent checkpoint digest set instead of one `previous_checkpoint_sha256`.

The reconciled witness contains a sorted two-parent witness digest set. Neither branch may be omitted, duplicated, or replaced.

## Immutable proof chain

- implementation and falsification gate: `9ec014179132cb1bf5a6f21275583cd50425c96e`
- immutable Branch A producer: `9ec014179132cb1bf5a6f21275583cd50425c96e`
- reusable fork/reconciliation verifier: `51894987f038e6c24fadf5b3c2768feda4117d6f`
- pinned caller: `c6412f5656fda2edaf9cad907d7af1fb8d312402`
- one-shot: **`32861017622` — FULL SUCCESS**
- upstream portable multi-epoch verifier: `5f5cee5749eaa15814323f563c1544347524d000`
- upstream downstream-state verifier: `65140882f172c53b6556ce9aa7a190f40bacc3bf`
- upstream historical verifier: `64116d0eea55a874ac7f63b733416df39108d7a7`
- Root A rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

Exact-head gates on reusable verifier `51894987f038e6c24fadf5b3c2768feda4117d6f` before pinning:

- Python CI `32860451352` — SUCCESS
- Python Integration `32860450463` — SUCCESS
- Artillery `32860451253` — SUCCESS

Caller-head gates on `c6412f5656fda2edaf9cad907d7af1fb8d312402`:

- Python CI `32861015809` — SUCCESS
- Python Integration `32861015953` — SUCCESS
- Artillery `32861015928` — SUCCESS
- Portable Causal-State Evolution `32861017272` — SUCCESS
- Causal Fork Reconciliation one-shot `32861017622` — SUCCESS

The one-shot rebuilt the upstream trust chain from a fresh Root A rotation, re-proved historical convergence, rebuilt the portable epoch-0 anchor, re-proved portable multi-epoch evolution through epoch 2, produced and attested Branch A, verified the detached Branch B Ed25519 evidence, built the two-parent fork/reconciliation objects, attested the final result, then ran a separate audit job that reverified all GitHub signers and independently recomputed the complete fork and reconciliation from bundled bytes.

## Common portable ancestor

The fork begins at the verified causal epoch-2 tip from Signal 013:

- semantic state: `bd7a9d1eb813f9a817857f175f69d9f551c07d65a43705d9a85096a6c93d08f5`
- state ref: `146b6342b40ad9206f128e86d0ada9b6ea93788b5272fa7e7c1d4f3ce3e49835`
- checkpoint: `300538e7aa1c10cc82651f9b60097ab467bbbb84b2e42873d7ff6cf5cd74a0f2`
- witness: `c03f26774a5e3f45b15d118bb50263c529bf1a8883c8021b6d41476ea9fd1804`

The complete checkpoint and witness prefix through this ancestor is independently revalidated before either branch is accepted.

## Independent divergent branches

### Branch A — GitHub OIDC attested

- provider: `github-oidc-fork-a`
- authority: `github-oidc:safal207/Liminal:causal-fork-branch-a-producer@9ec014179132cb1bf5a6f21275583cd50425c96e`
- logical branch: `authorization-policy-fork-a`
- semantic state: `0100f6388a6200f7eeec730259ffb4f597080adb61ba484ccffc53beaa47adc4`
- state ref: `c53803375a01d33366bdaab3db38bc063a8c0441464012bff40b4845f9cc5e02`
- branch ref: `ce5a854b1002a400889b1c0a394fd27617cf0412c52cb7c00aaa9d105ded0ba5`
- checkpoint: `6cd94ab45be78236f638607a3616e5f3d9f462e9bfaa29103bcc278b3d9c36de`
- witness: `c825f5db66092f6db5637c8f46e2707d328b355d87ab7f8ce91918cd1f1ed589`
- result digest: `1719a618d5579561ddbfd48c5b1e168f95357b15866fc5d977b4f2aa448882a1`

### Branch B — detached Ed25519 signed

- provider: `offline-ed25519-fork-b`
- authority: `ed25519-sha256:7a068f1ffd936617cc613b68e6c8b92b17cace27f932d5e566da56c8e693415a`
- logical branch: `authorization-policy-fork-b`
- semantic state: `13f0d56c02c4af63fb6eb72a3ce5b85d99724343fd37b2926e167183b46c09c0`
- state ref: `ec53ec1ab489875066e02f62d5ac74c3d3d11a86ad9845b2d00947e7856034cf`
- branch ref: `f42e9d497e303f2da4b5e4b178867331da263b039ca88079c34ff47cf646843b`
- checkpoint: `ee976252e9e9dcf6b47fb548d381cd71c5874abad53bc91818c575453a1f2994`
- witness: `fc82bcb40ff6287c9309407bb1a5b12136b74bae5407d37e441ae6026dd651d7`
- signed envelope: `7726cc7e20f4857d568aa6b9cec7e1781ef0c7572989e076a07cfb44c3aa0be7`

The two branch semantic states are intentionally different. This is a genuine fork, not two providers reproducing one state.

The detached private key was not committed. The repository contains only the public key and the signed envelope.

## Portable reconciliation

Both independently verified votes bind their exact branch ref, branch state ref, checkpoint, witness, reconciliation contract, authorization contract, and the same new semantic target.

Reconciled semantic state:

`4b54fe9df355b3602433624614c3dc3668cd1152a0558265a38c21ded4685077`

Portable reconciliation identities:

- reconciled state ref: `595c907a29ad9ff607a1651830a777382c11e6ae7a93d82c43bcb605b6942c86`
- canonical parent set: `232a2681d3406b262e3e663d237bd78f699eeba7b11508ea03794eb505cb7f75`
- reconciliation ref: `a9329a61a0403e54443154a5cff8a2583965121df1c6862937058c54e0d97eb9`
- reconciliation checkpoint: `6998bf2749eaf0392b1693b0867890272d2f494a3ee42d9517cbfeae693c8e11`
- reconciliation witness: `1b3c83909ae1ef6978973bc23874e9c158a381064e91384f1b2e258142f80776`
- portability receipt: `a23d89511bbeaa73f119bf80df39665c5a6bf4819c60135ddb8d5f391341eb9c`

The receipt reports:

```text
fork_causal_epoch          = 3
reconciled_causal_epoch    = 4
lineage_parent_count       = 2
both_lineages_preserved    = true
fork_semantics_divergent   = true
branch_order_canonical     = true
raw_evidence_embedded      = false
```

## Fail-closed falsification

The implementation rejects:

- invalid or unverified branch evidence;
- same provider, same authority, or same provenance on both branches;
- duplicate logical branch identity;
- branches that are not semantically divergent;
- a branch that does not descend from the exact common tip;
- a reconciliation vote bound to the wrong branch ref, state, checkpoint, or witness;
- vote target mismatch;
- reconciliation-contract mismatch;
- reconciliation-authorization mismatch;
- a missing parent;
- a duplicated parent;
- a tampered common prefix;
- raw provider identity smuggled into portable logical identity;
- branch input ordering that would otherwise change reconciliation bytes.

## Evidence

Canonical proof result:

`cdfe800a10f782a3ec4a47fa53e1d6c063734377453baaac1c2cd913939cc532`

Independent audit result:

`e493e03b67fedd679fb222b317b913413defa5a3e5297d8b1ea272dbb97a01bd`

Artifacts from one-shot `32861017622`:

- fork/reconciliation proof `9568276299` — `sha256:bfae1c7e5cad8251fbe2738f92ec7d4e3349ba10fffee302a8cfcd4f10df2d0c`
- independent audit `9568308448` — `sha256:32c9df7b285e1aae5575121e03068c2f1639416a032e102b12e70763e498dbd8`
- Branch A evidence `9568252429` — `sha256:c65a0d9482d3afeaf3295d9820ceb45d2e93a46a4958ce908d7691b1bb40f22b`
- fresh multi-epoch prefix `9568233490` — `sha256:a3ce81176139d10560416e54a12ec9f5b0e6d10edccbe7d4b59650d2ac65e567`
- fresh Path A evolution `9568207502` — `sha256:550adf809256ff8baff5fe3d317e4d238a9a09d8a1d2d87ece2f1d07f4dd8d8c`
- fresh downstream proof `9568186007` — `sha256:aa82fba47dfccb4981535bd21ec62c2ed3f7c5cbe12883b690a718ac85dffbad`
- fresh historical proof `9568165529` — `sha256:82babf9260921267e5b98a7e5301562b0403d8172ac03df89d3a88f8aaa4413b`
- fresh Root A rotation `9568145765` — `sha256:34ecd3750082ca96683f6bac2a714de651ab58bac5606167af88002b3483d43a`

The independent audit reverified:

- the final fork/reconciliation GitHub signer;
- the bundled portable multi-epoch signer;
- the bundled Branch A signer;
- the detached Branch B Ed25519 signature;
- all source-material bindings;
- the complete common checkpoint/witness prefix;
- both fork branch objects;
- both reconciliation votes;
- the canonical two-parent set;
- the exact reconciliation ref, checkpoint, witness, and receipt bytes.

It independently reproduced the canonical proof result, target semantic state, parent-set digest, receipt, and `raw_evidence_embedded=false`.

## What changed architecturally

Before this signal:

```text
independent histories
        ↓
one shared semantic trajectory
        ↓
portable linear causal chain
```

Now:

```text
portable common prefix
        ↓
explicit divergent semantic branches
        ↓
independently evidenced branch votes
        ↓
canonical two-parent reconciliation
        ↓
portable reconciled state
```

Principle:

> **A reconciled causal state must commit every lineage that authorized it; selecting one predecessor and forgetting the other is not reconciliation.**

## Claim boundary

This signal establishes one tested two-parent reconciliation construction:

- a fully validated portable common prefix through causal epoch 2;
- two genuinely different semantic branch states at causal epoch 3;
- independent GitHub OIDC and detached Ed25519 branch evidence;
- exact branch-bound reconciliation votes;
- canonical order-independent parent identity;
- explicit preservation of both checkpoint and witness lineages;
- a new reconciled semantic state at causal epoch 4;
- no raw provider/signer/provenance evidence in portable fork/reconciliation objects;
- independent recomputation from immutable artifact bytes.

It does **not** establish:

- arbitrary N-parent reconciliation;
- repeated or nested fork/reconciliation cycles;
- bounded ancestry compaction after repeated joins;
- Byzantine quorum or governance correctness;
- automatic conflict-resolution policy safety;
- organizational-governance independence;
- hardware/storage/network-path independence;
- universal provider independence;
- indefinite durability.

## Next falsifiable question

**Repeated Fork / Reconciliation Lineage Compaction v0.1**

After a successful two-parent reconciliation, can the reconciled chain fork and reconcile repeatedly while retaining bounded, independently verifiable lineage rather than embedding an ever-growing raw ancestry payload?
