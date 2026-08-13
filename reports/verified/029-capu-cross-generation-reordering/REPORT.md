# RESONANCE Verified Report #029

# CaPU v0.24 — Cross-Generation Message Reordering / In-Flight Stale Message Quarantine

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#77`  
**Verified CaPU content head:** `140b3394b3d5ca4ef2d0fa3dcc43e6ac0f5ad5ac`  
**Workflow:** `CaPU vCML Cross-Generation Reordering v0.24`  
**GitHub Actions run:** `31659575820`

## Result

# **PASS — bounded cross-generation stale-message quarantine verified**

CaPU v0.23 proved delivery provenance and bounded retry reliability inside one shootdown generation. v0.24 adds a temporal authority boundary between two successive generations. After generation N retires and N+1 begins, a delayed delivery or acknowledgement carrying N cannot mutate the delivery or quorum state of N+1. The stale event is instead recorded in a separate quarantine ledger.

```text
generation N completes
  ↓
N retires
  ↓
exact successor N+1 launches
  ↓
late N delivery / ACK arrives
  ↓
quarantine stale evidence
  ↓
N+1 authority state unchanged
  ↓
N+1 completes only from N+1 evidence
```

## Verified threats

- delayed generation-N delivery cannot create generation-N+1 delivery authority;
- delayed generation-N ACK cannot advance generation-N+1 quorum;
- stale or foreign delivery/ACK is quarantined rather than accepted;
- current-generation ACK reordered before delivery is rejected;
- a retired generation cannot immediately be reused as the next generation;
- successor generation progression is exact and generation wrap is blocked in this bounded model;
- recovery / restore destroys current in-flight and quarantine state;
- changes to last-retired generation, current generation or quarantine ledger alter the canonical checkpoint commitment.

## Deterministic trajectory

```text
generation_n retired=5 authority_reopened=1
late_generation_n_delivery quarantined=1 current_generation=6 no_authority_mutation=1
late_generation_n_ack quarantined=1 current_generation=6 no_authority_mutation=1
reordered_current_ack_before_delivery rejected=1
generation_n_plus_1 completed_only_from_generation_6_evidence=1 authority_reopened=1
generation_reuse rejected=1 last_retired=6
recovery in_flight_quarantine_state_destroyed=1
CAPU_VCML_CROSS_GENERATION_V24_PASS
```

## Canonical checkpoint binding

Canonical digest:

```text
4c7656a9e36e9d921c8f72e2d43c5e3e00f919fef381f681ba45b4cb1d276ea2
```

Mutation checks changed the digest for last-retired generation, current pending generation, delivered/ACK bitmaps, quarantined delivery/ACK bitmaps, quarantine event count and pending state. A mixed cross-generation snapshot failed verification under the unchanged commitment.

## Exact-head verification

Verified head:

```text
140b3394b3d5ca4ef2d0fa3dcc43e6ac0f5ad5ac
```

All pull-request workflows registered on this exact head passed:

- `CaPU vCML Cross-Generation Reordering v0.24` — run `31659575820` — PASS;
  - deterministic job `94321368026` — PASS;
  - formal job `94321414146` — PASS;
  - v0.23 deterministic/canonical regression — PASS;
  - v0.23 bounded-safety regression — PASS;
- `Validate Examples` — run `31659575766` — PASS;
- `CaPU Core v0 RTL Smoke` — run `31659575731` — PASS.

## Formal result

```text
schema: capu.hardware.cross-generation-reordering-formal-proof.v0.24
safety depth: 38
safety: DONE (PASS, rc=0)
proof method: successful k-induction
cover depth: 48
cover: DONE (PASS, rc=0)
VCD witnesses: 8
v0.23 bounded safety regression: PASS
```

Pinned toolchain:

```text
SBY b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input SHA256:
05bbccbe26ef44a45ef4b9f4407fc4f80c1c9b92a023a39ab6b6235b9aa2697d

safety log SHA256:
f32ef9f98a0e5e91757dd0c483ae8b84f3e23ee4620f036c7ac4fb5746129e14

cover log SHA256:
f6629238e768e0af408a3f1135c49d1b8618f5a02d752e2245dcd3f98bb47db1

v0.23 formal regression log SHA256:
be8c31f0b2071f93ab1c413fdbe0790a3e17e1052ab9756eccdb2979afcaaf1a
```

## Evidence artifacts

Executable evidence:

```text
artifact ID: 9165678090
ZIP SHA256:
30240252c282876cfe67eb8094a374417872aa8eae7a8cd9b0c212ee162437b5
```

Formal evidence:

```text
artifact ID: 9165768881
ZIP SHA256:
db8603cd320f1487c85c2840ad1fbfd24d502be8cf61fe018e3c4a6fe7f0605e
```

Executable sealed hashes:

```text
RTL:
a740156658ae6350b58e285e0b244bd0af5030e29c24767b07b35f1ddf67611c

TB:
0e0fa2d6db80764ac43f14cdb412251b9c17983d2ec91ee9b5280f30e7262fe8

canonical encoder:
6b2b8223963a452674112b3bf3b066f18c07906ad0f1ac8d95c110ba61d94acd

canonical test:
ecc6081c5b44364a1bc864a99742bd80e10876d7b10c43277751eb4180ae7377

trajectory log:
3b3604d5f0f9fecc00cb05cf391dcf1ea4837969da6e9e98782459203ca0d85d

canonical Python log:
a0a1a6c9682c69a79815e71e8d40fc668867c4d5069b806573b78eecc3e9d711
```

## Claim boundary

This report verifies a **bounded reduced-width two-hart, two-successive-generation temporal-reordering authority model**. Within that scope it verifies exact successor generation progression without wrap, quarantine of delayed stale/foreign delivery and ACK evidence, non-mutation of current-generation authority by quarantined evidence, delivery-before-ACK causality, exact current-generation quorum completion, canonical binding of last-retired/current/quarantine state, and recovery/restore destruction of modeled in-flight state.

It does **not** claim generation wrap/reuse safety, arbitrary in-flight queues, production IPI/message transport, timing/fairness/liveness, arbitrary hart count, multiple concurrent shootdowns, cache coherence, virtualization, durable distributed recovery, production widths or unbounded correctness.

## Causal interpretation

```text
v0.22 generation-bound multi-hart quorum
  ↓
v0.23 delivery provenance + bounded retry reliability
  ↓
v0.24 cross-generation temporal quarantine
```

v0.24 makes old evidence explicitly non-ambient. A delivery or acknowledgement that was valid for generation N does not remain generally useful evidence after N retires. Once N+1 becomes authoritative, delayed N messages are evidence of reordering, not evidence that may advance N+1. The quarantine ledger preserves that distinction while keeping continuation authority fail-closed.
