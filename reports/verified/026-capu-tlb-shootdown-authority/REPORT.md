# RESONANCE Verified Report #026

# CaPU v0.21 — TLB Freshness / Shootdown Authority

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#74`  
**Verified CaPU content head:** `c32381b92e8654c7fbdb05cf6cd4601e082be458`  
**Workflow:** `CaPU vCML TLB Shootdown Authority v0.21`  
**GitHub Actions run:** `31657874752`

## Result

# **PASS — bounded TLB freshness / shootdown authority verified**

CaPU v0.20 bound a reduced authoritative memory view to checkpoint state. v0.21 addresses the next boundary: a cached address translation must not remain authoritative after the memory-view epoch changes, and shootdown completion must correspond to the exact pending target rather than an ambient acknowledgement.

The bounded model adds:

```text
v0.20 exact memory view
+ one TLB entry
  - valid
  - ASID
  - translation epoch
  - VPN -> PPN
  - R/W/X/U permissions
+ one pending shootdown target
  - ASID
  - translation epoch
  - VPN
        ↓
freshness-gated cached authority
        ↓
exact invalidation / exact acknowledgement
```

## Verified threats

- stale translation epoch does not authorize a hit;
- foreign ASID or VPN does not authorize a hit;
- permission mismatch fails closed;
- targeted shootdown invalidates the matching cached translation;
- foreign shootdown acknowledgement is rejected;
- only the exact pending ASID / epoch / VPN acknowledgement retires shootdown authority;
- recovery destroys pre-recovery TLB and pending-shootdown authority;
- mutation of TLB or shootdown state changes the canonical checkpoint commitment.

## Deterministic evidence

```text
fresh_tlb_hit exact=1 paddr=38
stale_epoch rejected=1 speculation_killed=1
permission_mismatch rejected=1
shootdown targeted=1 stale_entry_invalidated=1
foreign_shootdown_ack rejected=1
exact_shootdown_ack accepted=1
post_shootdown_refill fresh=1
recovery old_tlb_authority_destroyed=1
CAPU_VCML_TLB_SHOOTDOWN_V21_PASS
```

Canonical checkpoint digest:

```text
a712a5c668e856614bbab51ba9a772cb88c8740e4cb5e7bf18bf6b27a669812f
```

## Formal evidence

```text
schema: capu.hardware.tlb-shootdown-authority-formal-proof.v0.21
safety depth: 32 — PASS
cover depth: 38 — PASS
VCD witnesses: 4
v0.20 bounded safety regression: PASS
```

Pinned toolchain:

```text
SBY b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input:
45a06e9ca9fad2e5412c38aa602ed6fe5a3781c04eb6e35eb9d30b5716dff073

safety log:
e770a63fc1075a6d92fa8094c29f80b119026482b3a00af8d4ab2c839b513dc3

cover log:
ce4b06d5ea6730edbfffd427f8b9fe3c22fb93d266ce45d21cd703ea1b6be46d

v0.20 regression log:
c834ec87d19736362ff9608092e487468ad8fe359dca2ebcc499b65fbf7fc592
```

## Evidence artifacts

Executable:

```text
artifact ID: 9165054300
ZIP SHA256:
74cba3f991a06bde1417ed1aa3255a89821a8829069ca4b9afa7da427d00aa35
```

Formal:

```text
artifact ID: 9165080925
ZIP SHA256:
754b013f850e083f87533e452f7a21791d2cfbb7e817f0ab0a80331f9e932e4c
```

Sealed executable inputs/logs:

```text
RTL: 20c01b1512b7a31cd0cd883125786d1dd2b3b9c799ab816ef8260b3e388ce66c
TB: bce4417debf39f6ec7ea353cb63c49ff28428bfe45028b83804aad91ed8214a1
canonical encoder: 115c36e4793a89f457077386c41c750a1037ed90324a222d1af1a060e8388174
canonical test: 6eb3962b1defada6d998dc0affed712a2ccae9da232fec83442ad899e635c88a
trajectory log: a52d4a479106c809d717f4a3b1526b1ab321b1ebc55426fcae2c73aac42c2019
canonical Python log: 0258ea5b3a110b4ff6c8f11770b0c5fb394a8fac9445bfb161c2f2bd754099ab
```

## Verification notes

Early CI iterations exposed observation/harness defects rather than a TLB-authority counterexample: the deterministic test initially sampled the combinational acknowledgement after retirement; the initial formal harness generated its own clock and referenced internal DUT state; after that state was exposed as formal-observable outputs, the wildcard testbench needed matching declarations. The final evidence above is from one exact implementation head after those observation defects were removed.

## Claim boundary

This is a **bounded reduced-width one-entry TLB plus one shootdown transaction model**. It proves freshness-gated cached translation authority, permission-gated hits, matching-entry invalidation, exact pending-target acknowledgement, recovery invalidation, canonical binding of modeled TLB/shootdown state and bounded reachability.

It does **not** claim a production multi-entry/set-associative TLB, replacement policy, full page-table walker/refill semantics, A/D-bit behavior, PMP/PMA, multi-hart/IPI shootdown delivery, distributed acknowledgement quorum, cache/coherence interaction, virtualization/nested translation, production speculation/reorder-buffer semantics, RTL SHA-256/off-path verifier correctness, durable-media correctness, production widths or unbounded correctness.
