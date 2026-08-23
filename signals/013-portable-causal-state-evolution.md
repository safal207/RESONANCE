# Engineering Signal 013 — Portable Causal-State Evolution / Multi-Epoch Convergence

**Status:** VERIFIED — 2026-08-23

## Signal

Liminal extended history-free downstream causal identity beyond a single convergence anchor.

Two independently rooted and differently shaped historical paths now advance through two later causal epochs and produce the **same portable checkpoint and witness chain** at each tested epoch.

```text
History A: generation 1 → 3 → 4
                           │    │
                           │    └────────────┐
                           └──────────┐       │
                                      ▼       ▼
Portable causal chain: epoch 0 → epoch 1 → epoch 2
                                      ▲       ▲
                           ┌──────────┘       │
                           │                  │
History B: generation 1 → 2 ───────────────→ 5
```

The histories deliberately do not advance with the same generation schedule. Path A inserts a semantic no-op generation before causal epoch 1; Path B inserts its extra historical generations between causal epochs 1 and 2.

Despite those distinct historical trajectories, both independently verified paths establish the same semantic state at causal epochs 1 and 2 and therefore produce byte-identical portable checkpoint/witness objects.

## Fractal Causal Refactoring diagnosis

The previous gate established a history-free convergence anchor at causal epoch 0, but a deeper traversal exposed a new First Meaningful Divergence.

The intended idea was:

```text
portable causal chain validation
= validate every predecessor relationship in the chain
```

The initial implementation effectively performed:

```text
validate current object
+ inspect one predecessor
```

For epoch 2, `validate_causal_checkpoint(previous_checkpoint)` no longer had the predecessor context required to validate epoch 1. The same structural problem existed in the witness chain.

The problem was therefore not a digest mismatch. It was an API/model error:

> **object validity and chain validity had been collapsed into one operation without carrying the chain context required at later epochs.**

Refactor point:

```text
single-object validation
        ↓
explicit full-prefix validation
```

A second causal primitive was also required:

```text
CausalTransitionRef
```

A transition now identifies the portable logical transition between two semantic state references without promoting path-specific registry, manifest, provider, or historical generation identities into portable causal identity.

## Three distinct identities

The model now separates:

```text
1. semantic state identity
   CausalStateRef

2. portable transition identity
   CausalTransitionRef

3. historical transition provenance
   provider / registry / manifest / generation evidence
```

This distinction is what allows:

```text
Path A generation 1 → 3
Path B generation 1 → 2
```

to represent the same causal transition from epoch 0 to epoch 1, while preserving different provenance for how each history established it.

## Immutable proof chain

- implementation gate: `262436b9b35f72f9ca425ee590f68a6341f16eb6`
- immutable Path A producer: `97b2c2f9b5b0e5ba250d97a8ceba070b07713792`
- reusable multi-epoch verifier: `5f5cee5749eaa15814323f563c1544347524d000`
- discoverable pinned caller: `c5d92872db1a9870d824d9f60575d4b2c6dd4245`
- one-shot: **`32637713399` — FULL SUCCESS**
- epoch-0 downstream verifier: `65140882f172c53b6556ce9aa7a190f40bacc3bf`
- historical verifier: `64116d0eea55a874ac7f63b733416df39108d7a7`
- Root A rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

Exact-head gates on reusable verifier `5f5cee5749eaa15814323f563c1544347524d000` before pinning:

- Python CI `32635346698` — SUCCESS
- Python Integration `32635346719` — SUCCESS
- Artillery `32635346683` — SUCCESS

The one-shot rebuilt the entire upstream trust chain from a fresh Root A rotation, re-proved historical A/B convergence, rebuilt and attested the portable epoch-0 anchor, produced and attested Path A evolution, verified the detached Path B Ed25519 evolution, constructed the two-epoch portable chain, attested the result, and then ran a separate audit job that reverified all GitHub signers and independently recomputed the complete evolution from artifact bytes.

## Independent evolution paths

### Path A — GitHub OIDC attested

Historical schedule:

```text
generation 1 → generation 3 → generation 4
```

- transition 1: `1 → 3`
- transition 2: `3 → 4`
- contains a validated semantic no-op generation before causal epoch 1;
- producer source pinned at `97b2c2f9b5b0e5ba250d97a8ceba070b07713792`;
- result is GitHub attested and reverified by the final verifier and external audit.

Path A result digest:

`53534958b73c4691e1d44fb74c290c5029f87531e8df135ea8fd9a9e995deff7`

### Path B — detached Ed25519 signed

Historical schedule:

```text
generation 1 → generation 2 → generation 5
```

- transition 1: `1 → 2`
- transition 2: `2 → 5`
- extra historical generations occur on a different schedule from Path A;
- full registry/manifest chain is revalidated from committed material;
- signed by a separate detached Ed25519 evolution authority.

Path B evolution signer:

`ed25519-sha256:51c016fefc63fce955d954bcd2b30e08eb40effd18f36a9646bdb5baa0fabfd8`

Signed Path B evolution envelope:

`8e34c19378da73ef15e2a3fa7380d9b68f89042f8b6772257492b06f297a752c`

## Portable causal states

Epoch 0:

`ceca17a68e8f469fdfb847ca7a72b80b6214507910c4e99670ec0f33efa1ef91`

Epoch 1:

`5e098592e9a7cc96b3dc85da43de271209154504f8d1fd043690094f646927f8`

Epoch 2:

`bd7a9d1eb813f9a817857f175f69d9f551c07d65a43705d9a85096a6c93d08f5`

All three semantic state identities are distinct. The proof therefore demonstrates actual state evolution, not repetition of one anchor.

## Portable transition / checkpoint / witness chain

Anchor identities from Signal 012:

- state ref: `09e45b0629a3507d476ddeacc246e11ab751921877868c465930a2dc7ac37e85`
- checkpoint: `c1f78afc86ed00597bed0855b440b4cebd595549860f5f9b095ea69284b861d9`
- witness: `265eedc7753fd32f5d6596c78de45126c6ada056673c2ea7cda9db32fd9eff25`

Causal epoch 1:

- state ref: `f6b8eb9efc07dbbd68f325c608f641af908269c5018347ee0b83701476ede0ec`
- checkpoint: `64d742c6c1eaa769faf54b4371ceab1e89f7dcb376bc20e341101ba322150479`
- witness: `4cf45367459eabf8c45beae9086690d01f182ecac041a0fade70b2a8c24fa88e`
- transition-ref digest: `a7f672ac6507ac7c3a26bd75d2e94a619f707553a4ad604fa395ca822d9f3bfb`

Causal epoch 2:

- state ref: `146b6342b40ad9206f128e86d0ada9b6ea93788b5272fa7e7c1d4f3ce3e49835`
- checkpoint: `300538e7aa1c10cc82651f9b60097ab467bbbb84b2e42873d7ff6cf5cd74a0f2`
- witness: `c03f26774a5e3f45b15d118bb50263c529bf1a8883c8021b6d41476ea9fd1804`
- transition-ref digest: `884a57987106ad6bfdaef305ec7da66b3367820f9d17fcfa5aebe9bec284c9c7`

The receipt reports:

```text
epochs_advanced             = 2
final_causal_epoch          = 2
equivalent_checkpoint_chain = true
equivalent_witness_chain    = true
raw_history_embedded        = false
```

## Evidence

Portable evolution receipt:

`defba3fd71ce6eb27b147d9a975f2621198f4a1473cf40469c4edd23ad267576`

Canonical proof result:

`1b7a05a478bf3bafa6da32649af70f25853f20fb1a094c69d6d794f936b203c2`

Artifacts from one-shot `32637713399`:

- multi-epoch proof `9492779416` — `sha256:c683ee3e0524232ba62cf08abd6fe76dd6703e001fdb30b2e8bfa7c5ae984996`
- independent audit `9492785613` — `sha256:748a827203d3ef288cce382b4675211a9b62d81587ef8e8ead86639b9fbc3f76`
- Path A evolution `9492772456` — `sha256:3afcd39ad3dd0d24af13bbbcf8273d0e98275f2fb7bbe2fd442aebd6bcad0b70`
- fresh epoch-0 downstream proof `9492768089` — `sha256:f5a72daa5e03007c3842bef6c8d2d0c803712c679a03f45c8e9512587de5e66a`
- fresh historical proof `9492762188` — `sha256:8c3abc48f05788f36b59545a20b5ad3b72d9543e9b78adc65bec480280b4a743`
- fresh Root A rotation `9492756892` — `sha256:a2fcbb78a6240b2ecc592976ba51e102465bf720c50cdca400358ffb187b3c83`

Independent external audit reproduced:

- `epochs_advanced = 2`;
- `final_causal_epoch = 2`;
- final semantic state `bd7a9d1e...`;
- final checkpoint `300538e7...`;
- final witness `c03f2677...`;
- receipt `defba3fd...`;
- Path B signer `ed25519-sha256:51c016fe...`;
- `raw_history_embedded = false`.

## What changed architecturally

Before this signal:

```text
independent histories
        ↓
one common portable anchor
```

Now:

```text
history A trajectory ─┐
                      ├→ portable epoch 0
history B trajectory ─┘         ↓
                         CausalTransitionRef
                                ↓
                         portable epoch 1
                                ↓
                         CausalTransitionRef
                                ↓
                         portable epoch 2
```

At each step, historical transition provenance remains independently inspectable while portable state and transition identity remain history-free.

Principle:

> **A portable causal chain must bind the meaning of each transition and validate its complete causal prefix, without confusing historical path length with causal progress.**

## Claim boundary

This signal establishes, for the tested two-step evolution:

- two later causal epochs beyond the history-free anchor;
- distinct semantic state at each causal epoch;
- different historical generation schedules across independent paths;
- a semantic no-op historical generation that does not advance causal epoch;
- explicit portable transition identity;
- full checkpoint-prefix validation;
- full witness-prefix validation;
- byte-identical portable checkpoint and witness chains across the two tested histories;
- GitHub OIDC attestation of Path A;
- detached Ed25519 verification of Path B;
- independent recomputation from immutable artifact bytes.

It does **not** establish:

- arbitrary or unbounded epoch evolution;
- safe collapse of genuinely different intermediate causal states;
- fork/reconciliation semantics;
- organizational-governance independence;
- hardware/storage/network-path independence;
- universal provider independence;
- indefinite durability.

## Next falsifiable question

**Causal Fork / Reconciliation Portability v0.1**

If two independently valid portable causal chains temporarily reach different intermediate semantic states, can they later reconcile to one authorized semantic state through an explicit reconciliation primitive without erasing either causal lineage or allowing a divergent predecessor to masquerade as the same history?
