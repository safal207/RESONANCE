# RESONANCE Verified Report #030

# CaPU v0.25 — Generation Wrap / ABA Protection

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#78`  
**Verified CaPU content head:** `1343afbf5dedca6cc478e8a7f3a38f763a589d54`  
**Workflow:** `CaPU vCML Generation Wrap ABA v0.25`  
**GitHub Actions run:** `31660219582`

## Result

# **PASS — bounded generation-wrap ABA authority verified**

CaPU v0.24 proved that delayed prior-generation delivery and acknowledgement evidence cannot mutate a successor generation, but deliberately excluded numeric generation-counter wrap. v0.25 introduces a separate incarnation identity so that reuse of the same small generation number after wrap does not recreate old authority.

```text
incarnation A / generation MAX retires
  ↓
incarnation A+1 / generation 0 launches
  ↓
historical incarnation A / generation 0 message arrives
  ↓
same numeric generation, foreign incarnation
  ↓
QUARANTINE / NO AUTHORITY
```

The authority identity is modeled as:

```text
incarnation + generation + ASID + translation epoch + VPN + hart
```

A non-wrap successor increments generation under the same incarnation. A wrap successor resets generation to zero and increments incarnation. Historical same-generation delivery or ACK evidence with a stale incarnation is quarantined and cannot mutate current delivery or acknowledgement state.

## Deterministic trajectory

```text
pre_wrap retired_generation=3 incarnation=1 authority_reopened=1
wrap_launch accepted=1 generation=0 incarnation=2
historical_same_generation_delivery quarantined=1 old_incarnation=1 current_incarnation=2 no_authority_mutation=1
historical_same_generation_ack quarantined=1 old_incarnation=1 current_incarnation=2 no_authority_mutation=1
wrapped_generation_completed_only_from_incarnation_2_evidence=1 authority_reopened=1
old_incarnation_reuse rejected=1 retired_incarnation=2
recovery in_flight_aba_quarantine_destroyed=1
CAPU_VCML_GENERATION_WRAP_ABA_V25_PASS
```

## Canonical checkpoint binding

Canonical digest:

```text
7d9f5a93ece085b6ed104a1f54f800410ae9ea08856a4c0092689aefc067319f
```

Mutation checks changed the commitment for retired incarnation/generation, pending incarnation/generation, delivery/ACK bitmaps, quarantine bitmaps and pending state. A mixed ABA snapshot failed verification under the unchanged commitment.

## Exact-head verification

Verified head:

```text
1343afbf5dedca6cc478e8a7f3a38f763a589d54
```

All pull-request workflows registered on this exact head passed:

- `CaPU vCML Generation Wrap ABA v0.25` — run `31660219582` — PASS;
  - deterministic job `94323298911` — PASS;
  - formal job `94323298879` — PASS;
  - v0.24 deterministic/canonical regression — PASS;
  - v0.24 bounded-safety regression — PASS;
- `Validate Examples` — run `31660219574` — PASS;
- `CaPU Core v0 RTL Smoke` — run `31660219535` — PASS.

## Formal result

```text
schema: capu.hardware.generation-wrap-aba-formal-proof.v0.25
safety depth: 40
safety: DONE (PASS, rc=0)
proof method: successful k-induction
cover depth: 52
cover: DONE (PASS, rc=0)
VCD witnesses: 6
v0.24 bounded safety regression: PASS
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
b06811ff661a83fc8190184d511004218f1ac0ef2b69c3ad45d7b74192df7b70

safety log SHA256:
100bc4316dc61b27c18c265189c9a7c9f4b87a7fabca204962d134f4af45a46a

cover log SHA256:
80e2e1e77e31398494adc1274881bd97bc96fce0e10ede9fda90f4329628ebfa

v0.24 formal regression log SHA256:
737b826093580a2b8a44c89784f058c2d869c7e6c3dd804c948a32c7f53ba006
```

## Evidence artifacts

Executable evidence:

```text
artifact ID: 9165904843
ZIP SHA256:
152049c5d77321d17ec623d3f845227e3bdca799f94e59c79a21a729cea44f65
```

Formal evidence:

```text
artifact ID: 9165994049
ZIP SHA256:
6233fc07b0a6b4422375083b4fa18cc789e869f66b3fd68d96d06c58b899232e
```

Executable sealed hashes:

```text
RTL:
8410edd2875f381ed41c4113ff31d4b21c50bb9a76f4b09f84f700b3b9bcd718

TB:
a77dd9d338818878d17fdddf2f617dc786b9b7b09df4aab1810234b176422e0f

canonical encoder:
ce141e603b1cbf80ed339afffcb8e17c9100d19d8168b28389f6b8374db55d0e

canonical test:
2f686cb5afc3f5950d688a326fe5780aedd85001a71271c39483696cd625669f

trajectory log:
f214655a3656a87ff87565391741d5d39bd67520cde63c5163b4b707cb266d5b

canonical Python log:
e519aa523130f47505490bac58acae6f86dbcb21f5f503d82d6886f82bfcb6c0
```

## Claim boundary

This report verifies a **bounded reduced-width model with a 2-bit generation and 3-bit incarnation identity**, exercising one numeric generation wrap. Within that scope it verifies non-wrap successor progression, wrap-driven incarnation change, stale same-generation/foreign-incarnation delivery and ACK quarantine, delivery-before-ACK authority, exact quorum completion, canonical binding of incarnation/generation/quarantine state, and recovery/restore destruction of modeled in-flight ABA state.

It does **not** claim incarnation-wrap safety, arbitrary in-flight queues, cryptographic uniqueness, production IPI/message transport, timing/fairness/liveness, arbitrary hart count, multiple concurrent shootdowns, cache coherence, virtualization, durable distributed recovery, production widths or unbounded correctness.

## Causal interpretation

```text
v0.23 delivery provenance + retry
  ↓
v0.24 cross-generation temporal quarantine
  ↓
v0.25 generation-wrap identity / ABA protection
```

The key distinction is that a reused numeric identifier is not a reused authority identity. Authority survives only when the incarnation and the rest of the exact target identity match the current causal generation.
