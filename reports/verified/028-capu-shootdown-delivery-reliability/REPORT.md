# RESONANCE Verified Report #028

# CaPU v0.23 — Shootdown Delivery Reliability / Retry / Lost-ACK Recovery

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#76`  
**Verified CaPU content head:** `9a19bb8e21b2cef9f5cd1d110b6e930ae27194ab`  
**Workflow:** `CaPU vCML Shootdown Delivery Reliability v0.23`  
**GitHub Actions run:** `31658894304`

## Result

# **PASS — bounded shootdown delivery/retry authority verified**

CaPU v0.22 proved generation-bound exact acknowledgement quorum across two modeled harts. v0.23 separates transport attempts from observed delivery and from acknowledgement arrival. Global translation authority remains closed while the shootdown is pending, including when delivery attempts are lost or when bounded retries are exhausted.

```text
shootdown authority
  ↓
send attempt
  ↓
delivery observed OR lost
  ↓
ACK arrives OR is lost/delayed
  ↓
exact retry under the same generation + target
  ↓
exact ACK quorum
  ↓
global translation authority reopens
```

The crucial causal rule is that an acknowledgement is authority-bearing only after an exact delivery for that hart has been observed. A lost delivery therefore cannot create a phantom acknowledgement path. A lost acknowledgement can be retried by re-delivering the same exact shootdown without double-counting acknowledgement authority.

## Verified threats

- phantom ACK before exact delivery is rejected;
- stale-generation retry is rejected;
- foreign target retry cannot advance authority;
- lost delivery does not mark delivery observed;
- exact retry after lost delivery can establish delivery provenance;
- lost/delayed ACK can be recovered by exact re-delivery and a later ACK;
- duplicate acknowledgement cannot count twice;
- three exhausted delivery attempts do not reopen authority;
- recovery / restore destroys pending delivery, attempt and acknowledgement state;
- changes to delivery bitmap, ACK bitmap or retry counters alter the canonical checkpoint commitment.

## Deterministic trajectory

```text
reliable_shootdown launched=1 generation=10 required=11 authority_closed=1
hart0_delivery attempt=1 accepted=1 lost=1 delivered=0
phantom_ack_before_delivery hart=0 rejected=1
hart0_retry attempt=2 accepted=1 delivered=1
hart0_ack accepted=1
stale_generation_retry hart=1 rejected=1
hart1_delivery attempt=1 accepted=1 delivered=1
hart1_retry_after_lost_ack attempt=2 accepted=1 delivered=1
exact_quorum ack1=1 complete=1
authority_reopened=1
retry_exhausted hart=0 rejected=1 attempts=3 authority_closed=1
recovery reliability_state_destroyed=1
CAPU_VCML_SHOOTDOWN_RELIABILITY_V23_PASS
```

## Canonical checkpoint binding

Canonical digest:

```text
c00fbcd530c4183e9266ecddb44720bbce7bb3a0141c4b0ca4977c64707faac0
```

Mutation checks changed the digest for generation, required-hart set, delivered bitmap, ACK bitmap, both attempt counters and pending state. A mixed delivery/attempt snapshot failed verification under the unchanged commitment.

## Exact-head verification

Verified head:

```text
9a19bb8e21b2cef9f5cd1d110b6e930ae27194ab
```

All pull-request workflows registered on this exact head passed:

- `CaPU vCML Shootdown Delivery Reliability v0.23` — run `31658894304` — PASS;
  - deterministic job `94319326051` — PASS;
  - formal job `94319367152` — PASS;
  - v0.22 deterministic/canonical regression — PASS;
  - v0.22 bounded-safety regression — PASS;
- `Validate Examples` — run `31658894284` — PASS;
- `CaPU Core v0 RTL Smoke` — run `31658894277` — PASS.

## Formal result

```text
schema: capu.hardware.shootdown-delivery-reliability-formal-proof.v0.23
safety depth: 36
safety: DONE (PASS, rc=0)
cover depth: 44
cover: DONE (PASS, rc=0)
VCD witnesses: 8
v0.22 bounded safety regression: PASS
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
5724df45f05f9d0fdc5b5b944c8cee6b99c6d7fd6ea81949f3ee23d6adc297f4

safety log SHA256:
818f48977102aaf10adb6b7603790a3865a0ead0a7ad644d8c8b69f906f82893

cover log SHA256:
a87c0aa769f63429f68d4d370a2dc33d938281832ad4dc8b30273cf40189f2e1

v0.22 formal regression log SHA256:
7c59fb2c9f13fcc84a5ec50303473c4cb43e39be7f24d979d48221e200f0cb24
```

## Evidence artifacts

Executable evidence:

```text
artifact ID: 9165439331
ZIP SHA256:
4c66bc969955cabfe57ce4064f0adf9043d699de9974688c205118daf21be010
```

Formal evidence:

```text
artifact ID: 9165481741
ZIP SHA256:
9f4751d6ea4fbf409e34d847e8190ba5ad21cdb9a36abe9cde26d4bb0424f177
```

Executable sealed hashes:

```text
RTL:
0fe6a4de0ae5bb12fbd9594b48c24b2fa8d2814aaf53a51b49a067ebee91289f

TB:
3b333c6d3bc473e23a1be1e594887c5d7de9dde12ce87c3d19c2fa17e6ecc27d

canonical encoder:
fb24fa7cabd39c7eb947de67df5afb6afab7fd031c48aa7931b644d8b60238c7

canonical test:
ac2c774ddbeb0efbbf12b710b21e06059fa53afaebec2624064e6e8f395cc5f4

trajectory log:
da575ed048ca5818abda2585e184b112a8e57ce5a8ef1077d48c3bdb075d7b75

canonical Python log:
a50ea8c6db3645988bf1a5c15308e7e54fe3b236f09fbbc364c1fc43cf965900
```

## Claim boundary

This report verifies a **bounded reduced-width two-hart, one pending shootdown generation, one target, maximum-three-delivery-attempts-per-hart model**. Within that scope it verifies exact delivery provenance before ACK authority, lost-delivery retry, lost/delayed-ACK re-delivery, stale/foreign retry rejection, duplicate ACK protection, fail-closed retry exhaustion, exact quorum reopening and recovery/restore destruction of modeled reliability state.

It does **not** claim production IPI/message transport, probabilistic reliability, timing bounds, fairness, guaranteed liveness, arbitrary hart count, multiple concurrent shootdowns, cache coherence, virtualization, durable distributed recovery, production widths or unbounded correctness.

## Causal interpretation

```text
v0.21 local TLB freshness / exact shootdown authority
  ↓
v0.22 generation-bound two-hart acknowledgement quorum
  ↓
v0.23 delivery provenance + bounded retry reliability
```

v0.23 makes a useful distinction: evidence that a message was attempted is not evidence that it was delivered, and evidence that a previous message was delivered is not ambient authority for a different generation. Continuation authority is reopened only by the exact causal chain that the model recognizes: pending request → observed delivery → exact acknowledgement → required quorum.
