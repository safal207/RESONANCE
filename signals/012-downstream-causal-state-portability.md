# Engineering Signal 012 — Downstream Causal-State Portability Across Independent Histories

**Status:** VERIFIED — 2026-08-14

## Signal

Liminal removed the tested dependency of downstream checkpoint/witness identity on one concrete historical registry and manifest chain.

Two independently rooted histories now pass through independent historical verification, converge on the same semantic trust state, and produce the **same portable downstream checkpoint and witness bytes** without embedding either history's raw provider, genesis, registry, or manifest identity.

```text
History A provenance ─┐
                      ├→ independently verified semantic trust state
History B provenance ─┘
                                  ↓
                           CausalStateRef
                                  ↓
                      portable checkpoint
                                  ↓
                        portable witness
```

The portable objects preserve causal authorization semantics while historical provenance remains evidence rather than identity.

## Fractal Causal Refactoring diagnosis

The failure was not located first in the witness layer.

The intended idea was:

```text
downstream causal state = what is currently authorized
```

But checkpoint v0.3 still encoded:

```text
accepted_registry_sha256
accepted_manifest_sha256
previous_checkpoint_sha256
```

After Signal 011 proved that distinct registries/manifests can independently establish the same semantic trust state, those raw history identities became too strong to serve as portable downstream identity.

The **First Meaningful Divergence** was therefore checkpoint v0.3. Witness v0.4 merely inherited that choice.

Refactor point:

```text
concrete historical checkpoint identity
        ↓
CausalStateRef
```

`CausalStateRef` carries only:

- trust domain;
- logical state ID;
- causal epoch;
- semantic trust-state digest.

It deliberately excludes provider ID, genesis authority, registry digest, manifest digest, and historical generation.

## Immutable proof chain

- reusable downstream verifier: `65140882f172c53b6556ce9aa7a190f40bacc3bf`
- pinned caller: `d70701d95328bb9d4a58ec2d3855362844302b6d`
- one-shot: **`31767862942` — FULL SUCCESS**
- upstream historical verifier: `64116d0eea55a874ac7f63b733416df39108d7a7`
- upstream rotation workflow: `e2cb6a014236bc561d03c405f4986146026041fa`

Exact-head gates on the reusable downstream verifier before pinning:

- Python CI `31767484404` — SUCCESS
- Python Integration `31767484408` — SUCCESS
- Artillery `31767484397` — SUCCESS

The one-shot rebuilt fresh Root A evidence, reran Genesis / Historical Trust-Base Portability, verified the historical result signer, independently re-audited historical convergence, built the portable downstream state, attested it, and then executed a separate audit job that reverified both downstream and historical signers and recomputed the result from artifact bytes.

## Independent historical provenance

Path A terminal provenance:

- registry: `5441072b0e550995a9ad0b27b4f3af7c7b5bf531f59e27c870ab1a8cf61789a1`
- manifest: `b9cb0b37da2d74ece6c1cf780b06b17fbbb96f02e073ac64fb26be49cae24277`

Path B terminal provenance:

- registry: `acc16847c0cc89da4c5f32ba4ba46f462f6ed4dde526e2442bb3a197a3de51d2`
- manifest: `6fc61082148daac72d405d6a305ece0cf9bdde0e015f882553746761f7556c7b`

The raw identities remain distinct.

Shared semantic trust-state digest:

`ceca17a68e8f469fdfb847ca7a72b80b6214507910c4e99670ec0f33efa1ef91`

## Portable downstream identities

Portable semantic state reference:

`09e45b0629a3507d476ddeacc246e11ab751921877868c465930a2dc7ac37e85`

Portable checkpoint:

`c1f78afc86ed00597bed0855b440b4cebd595549860f5f9b095ea69284b861d9`

Portable witness:

`265eedc7753fd32f5d6596c78de45126c6ada056673c2ea7cda9db32fd9eff25`

Portable downstream receipt:

`9e1ec5ca29cdcacadb034826633d9900ec31b223736862fc540dc11b2fbb77b5`

The checkpoint and witness contain none of the Path A / Path B provider, genesis-authority, registry, or manifest identities.

## Evidence

Canonical proof result:

`fe2fff552040b5b0a9cc1d1769b5b62e9e8ef7e3531e6c5c28a2974beaf0d041`

Independent audit:

`2ea54bc1f33235afdddc66fd855b51814e9a00a6722d7dc6c3ef1d3223c3ddbe`

Artifacts:

- downstream proof `9207001915` — `sha256:6099254b051030ba2c765f26273a269e925a66837d167ff8d1607e9e439a56e9`
- independent audit `9207085176` — `sha256:c52a10a663e32d07a9d7a17f535ccff83e91ee9c63ad0d062feb7df18224b967`
- fresh historical proof `9206990695` — `sha256:30719ea95690698037e6e3ab36e7a63936e34ac29bacce83ced8bd116ced31f6`
- fresh Root A rotation `9206978810` — `sha256:40efcdefe7a4a53f78aec718949d4760fe5795c881ee3310a642e0f31c2b55c8`

The external audit reproduced the exact downstream checkpoint, witness, and receipt from bundled proof material after re-verifying both the downstream result signer and the upstream historical result signer.

## Causal epoch is not historical generation

A second divergence surfaced during the refactor: replacing a manifest digest with `history_generation` would merely move the historical dependency into a counter.

Therefore the portable model separates:

```text
historical_generation  = provenance of how one history arrived
causal_epoch           = position in the portable downstream state machine
```

The immutable proof establishes the convergence anchor at causal epoch `0`. Implementation falsification tests also verify that differing historical generation counts do not change the portable state reference when the independently verified semantic state is the same.

## What changed architecturally

Before:

```text
registry/history bytes
        ↓
checkpoint identity
        ↓
witness identity
```

Now:

```text
history A ─→ independent verification ─┐
                                      ├→ semantic state → CausalStateRef
history B ─→ independent verification ─┘                  ↓
                                                   checkpoint → witness
```

Principle:

> **Provenance must prove a causal state; provenance must not become the causal state's identity when multiple valid histories can establish the same semantics.**

## Claim boundary

This signal establishes, for the tested convergence anchor:

- independent raw historical provenance remains distinct;
- terminal semantic state is equal;
- raw history identities are excluded from the portable downstream objects;
- both independent histories produce byte-identical portable checkpoint and witness objects;
- the downstream result is attested and independently recomputed from artifact bytes.

It does **not** establish:

- arbitrary multi-epoch causal-state evolution;
- convergence after independent histories continue changing beyond the anchor;
- organizational-governance independence;
- hardware/storage/network-path independence;
- universal provider independence;
- indefinite durability.

Existing historical checkpoint/witness schemas remain valid historical representations; they were not rewritten. The new causal-state layer is a separate portable identity model.

## Next falsifiable question

**Portable Causal-State Evolution / Multi-Epoch Convergence v0.1**

Can independently rooted histories advance from the same portable causal anchor through later causal epochs, possibly via different historical transitions, and still converge on the same authorized next checkpoint/witness state without reintroducing concrete history identity into the downstream chain?
