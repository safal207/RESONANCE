# RESONANCE Verified Report #027

# CaPU v0.22 — Multi-Hart Shootdown Delivery / Acknowledgement Quorum

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#75`  
**Verified CaPU content head:** `c898007f4cac2127374bd6c468d523c6818e6e25`  
**Workflow:** `CaPU vCML Multi-Hart Shootdown Quorum v0.22`  
**GitHub Actions run:** `31658440108`

## Result

# **PASS — bounded two-hart shootdown quorum authority verified**

CaPU v0.21 proved freshness-gated authority for one cached translation and one exact local shootdown acknowledgement. v0.22 moves the authority boundary across two modeled harts: a memory-view transition remains globally incomplete until every required hart has supplied an exact acknowledgement for the same shootdown generation and target.

```text
memory-view transition
  ↓
shootdown generation + ASID + epoch + VPN + required hart set
  ↓
exact per-hart acknowledgements
  ↓
acknowledgement bitmap
  ↓
exact required-hart quorum
  ↓
retire distributed shootdown authority
  ↓
reopen global translation authority
```

The generation field is part of acknowledgement identity. This prevents an acknowledgement from an older shootdown from being replayed against a later request that happens to reuse the same ASID, translation epoch and VPN.

## Verified threats

- stale-generation acknowledgement replay is rejected;
- foreign ASID / translation epoch / VPN acknowledgements are rejected;
- acknowledgement from a non-required or already-counted hart cannot advance quorum;
- duplicate acknowledgement cannot count twice;
- partial quorum keeps global translation authority closed;
- zero-hart shootdown request is rejected;
- recovery / restore destroys pending partial-quorum authority;
- changes to generation, required-hart set, acknowledgement bitmap or target alter the canonical checkpoint commitment.

## Deterministic trajectory

```text
multihart_shootdown launched=1 generation=9 required=11 authority_closed=1
stale_generation_ack hart=0 rejected=1
hart0_ack accepted=1 bitmap=01 quorum=0 authority_closed=1
duplicate_ack hart=0 rejected=1
foreign_target_ack hart=1 rejected=1
hart1_ack accepted=1 effective_bitmap=11 quorum=1
exact_quorum complete=1 authority_reopened=1
recovery partial_quorum_destroyed=1
zero_hart_request rejected=1
CAPU_VCML_MULTIHART_SHOOTDOWN_V22_PASS
```

## Canonical checkpoint binding

Canonical digest:

```text
72a3861a9a34f357e797d2f9781abe62a5cb30087c01dce9acd8af1b4060d15f
```

Mutation checks changed the digest for shootdown generation, ASID, translation epoch, VPN, required-hart set, acknowledgement bitmap and pending state. A mixed quorum snapshot failed verification under the unchanged commitment.

## Exact-head verification

Verified head:

```text
c898007f4cac2127374bd6c468d523c6818e6e25
```

All pull-request workflows registered on this exact head passed:

- `CaPU vCML Multi-Hart Shootdown Quorum v0.22` — run `31658440108` — PASS;
  - deterministic job `94317944555` — PASS;
  - formal job `94317988584` — PASS;
  - v0.21 deterministic/canonical regression — PASS;
  - v0.21 bounded-safety regression — PASS;
- `Validate Examples` — run `31658440125` — PASS;
- `CaPU Core v0 RTL Smoke` — run `31658440144` — PASS.

## Formal result

```text
schema: capu.hardware.multihart-shootdown-quorum-formal-proof.v0.22
safety depth: 34
safety: DONE (PASS, rc=0)
cover depth: 40
cover: DONE (PASS, rc=0)
VCD witnesses: 6
v0.21 bounded safety regression: PASS
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
2632fb1155e733633bdb03f61958aca70ae5155be3559cbe1e9d638a71227770

safety log SHA256:
de8df088e80688a29391e238de85edb3fbc73332909282e58cfea26704a29e37

cover log SHA256:
c0f206f70d95b97928c51fd89cb9be5b1123ea902c3fefe0a84472a3ad4e613a

v0.21 formal regression log SHA256:
90f8ef3da1fcd4d7e1658c6e11da7d5650f42e306594f6791fc0a4fd09d2343c
```

## Evidence artifacts

Executable evidence:

```text
artifact ID: 9165269712
ZIP SHA256:
4b91f8c69e6beca1b1eecba6e6332aa95e784d4b4d29d7ca9b981c06241d9d6f
```

Formal evidence:

```text
artifact ID: 9165292458
ZIP SHA256:
7fcf035f29d2b2f360b602c76c4e88ce942b52131a70a0af91bb560027c77b35
```

Executable sealed hashes:

```text
RTL:
cf5e4d7abbe39b1a86caba40d326cd9fa54ea0a3e049db1c89959b85bf6fca9a

TB:
dd8b796949f9f41f1652aa44db99612716fc0604b3976cb3ffae0f76c21a3205

canonical encoder:
d2edbd1f23f5145ad77946cce652947654454169bf82f9b89255d881e447dbdf

canonical test:
c8566eb236dcddba3ec2a2fb5864853e1578efd735f7ef1be331107fbb7367f7

trajectory log:
f77b18fc3755d0b26e22b6f8390c5894b5fca2f93c0742139b4fdde67201cede

canonical Python log:
7a6939d7d0f9a7ba4082b6bec2398205ffc2000f93e8af2ccaf7a71a3c6ebb04
```

## Verification notes

Two early CI failures were verification plumbing defects, not authority counterexamples. The first canonical test omitted the repository root from its Python import path. The initial SBY scripts also referenced repository-relative paths after SBY had copied inputs into its working source directory. Both were corrected before the final exact-head run. The v0.22 RTL authority behavior did not change after its first deterministic trajectory passed.

## Claim boundary

This report verifies a **bounded reduced-width two-hart, one pending target, one shootdown-generation authority model**. Within that scope it verifies generation-bound exact acknowledgements, stale/foreign/duplicate acknowledgement rejection, fail-closed partial quorum, exact required-hart completion, recovery/restore invalidation of partial quorum state, canonical binding of modeled distributed shootdown state, and bounded reachability of modeled paths.

It does **not** claim production IPI/message delivery, message-loss or retry liveness guarantees, arbitrary hart count, multiple concurrent shootdowns, cache/coherence interaction, page-table walker/refill semantics, hardware A/D-bit updates, PMP/PMA, virtualization/nested translation, production speculation/reorder-buffer semantics, durable distributed recovery, production widths, or unbounded correctness.

## Causal interpretation

The result strengthens the CaPU recovery chain from local cached-translation freshness to bounded distributed invalidation authority:

```text
v0.20 exact memory view
  ↓
v0.21 local TLB freshness / exact shootdown authority
  ↓
v0.22 generation-bound two-hart shootdown quorum
```

The important distinction is that an acknowledgement is not ambient evidence that “some invalidation happened.” It is authority-bearing evidence only for one exact shootdown generation, target and required participant, and global continuation remains closed until the required acknowledgement set is complete.
