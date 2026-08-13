# RESONANCE Verified Report #025

# CaPU v0.20 — MMU Translation + Precise Page-Fault Recovery

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#73`  
**Verified CaPU content head:** `9fdb2ea1eaabeebce18c9d15b12cb6cfd109e1a9`  
**Workflow:** `CaPU vCML MMU Translation Recovery v0.20`  
**GitHub Actions run:** `31657042934`

## Result

# **PASS — bounded exact memory-view recovery verified**

CaPU v0.19 bound delegation policy and a two-level trap stack to one exact checkpoint authority. v0.20 addresses the next recovery boundary: the same architectural, causal, privilege and trap state must not resume under a different or stale address-translation authority.

The reduced v0.20 record adds:

```text
v0.19 exact checkpoint state
+ translation root
+ ASID
+ translation epoch
+ one canonical VPN -> PPN mapping
+ R/W/X/U permissions
+ precise page-fault pending/address/cause
        ↓
one canonical checkpoint payload
        ↓
exact restore / fail-closed memory view
```

## Verified threats

The exact-head deterministic and bounded paths reject or contain:

- a foreign translation root under an otherwise valid checkpoint;
- a foreign ASID;
- a stale translation epoch;
- changed mapping or permission bytes under the unchanged commitment;
- a foreign page-fault context;
- a stale candidate checkpoint prepared against a different committed memory view;
- a speculative visible effect attempting to cross a precise page-fault boundary.

A successful modeled translation is constrained to the exact checkpoint-bound PPN plus the original page offset.

## Runtime invariants

```text
RESTORE_ACCEPT => EXACT_BOUND_MEMORY_VIEW
FOREIGN_OR_STALE_MEMORY_VIEW => RESTORE_REJECT
TRANSLATION_HIT => EXACT_PPN_PLUS_OFFSET
PAGE_FAULT => NO_VISIBLE_EFFECT
PAGE_FAULT => SPECULATION_KILL
RECOVERY_OR_RESTORE => NO_VISIBLE_EFFECT
PREPARE_ACCEPT => EXACT_COMMITTED_MEMORY_VIEW
```

## Deterministic evidence

Observed exact-head markers:

```text
exact_restore memory_view=1 root=3 asid=5 epoch=7
translation_hit exact=1 paddr=26
permission_fault precise=1 speculation_killed=1 cause=2
foreign_translation_root rejected=1
foreign_asid rejected=1
stale_translation_epoch rejected=1
foreign_fault_context rejected=1
stale_candidate rejected=1
checkpoint_authority exact_memory_view=1
recovery_priority runtime_closed=1
CAPU_VCML_MMU_TRANSLATION_V20_PASS
```

Canonical SHA-256 test digest:

```text
4d9df3fc8b25c1025e08e1a41211c9f42e09d15c1843837240f46857466c4f99
```

Canonical mutation tests changed the digest for translation root, ASID, translation epoch, VPN/PPN mapping, permissions and page-fault context; a mixed memory view failed verification under the original commitment.

## Formal evidence

```text
schema: capu.hardware.mmu-translation-recovery-formal-proof.v0.20
safety depth: 30 — PASS
cover depth: 36 — PASS
VCD witnesses: 8
v0.19 bounded safety regression: PASS
```

Pinned formal toolchain:

```text
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input SHA256:
685ec5828d58d7523158d55f0b05ef212c8fd28e61bfe5462023764f264ad5d0

safety log SHA256:
8fabbdec657bd0cfb928ca5ff2d670a6b71596356a060708c112c5c98b672a06

cover log SHA256:
dc79e43f8c077e91b617ae6dcc81ee667aeddcc30dd51fdbc9fdf89d5f134ea7

v0.19 regression log SHA256:
057b7d7755caa52021be2656bad6d12bc61f73ed73a6d3dadd7e4a261ccd5b9a
```

## Evidence artifacts

Executable evidence:

```text
artifact ID: 9164763988
ZIP SHA256:
6a71ef942d5f03e439e64a19826dc0a5e039c51d41aa06a311bbc8d2678e0421
```

Formal evidence:

```text
artifact ID: 9164801987
ZIP SHA256:
fec5c1ffd40cd12b758f7b6256eb627bbbfa63271a1518b6e40e46c083e06ebe
```

Sealed executable hashes:

```text
RTL: 91aeb6a38d4a7fde3357ff3ef092c0c4dfdb7b8e50b6d59fac59b0f76abddaea
TB: 7fa20cc3cd934dfcead2baf8b33a3f0e0d5bdb8763e2747406ce288fe91e81a7
canonical encoder: c9abbdedebe2705c5706ac030343ae093cf2bef00be8821b75b34ae7a945491d
canonical test: f88b656ffd12b07013a2c3e91db32106a9ad8987d17f27bbd093b1796f9b42b7
trajectory log: ac253779973f407b51774da370a5612b1ebba8a076cd6c436adcb256b112193f
canonical Python log: 6bd2b8d3099427dd6245e624ca44a08bd617af7c14a75645e7374d16a72571da
```

## Exact-head regression

All pull-request workflows registered on the verified CaPU head were green:

```text
CaPU vCML MMU Translation Recovery v0.20 — run 31657042934 — PASS
Validate Examples — run 31657042925 — PASS
CaPU Core v0 RTL Smoke — run 31657042888 — PASS
```

The v0.20 workflow also reran the v0.19 deterministic, canonical and bounded-safety paths successfully.

## Verification notes

Two early CI failures were infrastructure/bootstrap defects, not RTL/invariant counterexamples:

1. the new Python test initially lacked the repository-root import bootstrap already used by previous tests;
2. the initial SBY scripts referenced repository-relative source paths after SBY had copied those files into its local `src/` directory.

Both were corrected without changing the v0.20 RTL semantics. The exact-head evidence above is the authoritative result.

## Claim boundary

This is a **bounded reduced-width one-entry translation/page-fault recovery result**. It proves exact binding of the modeled translation root, ASID, translation epoch, one VPN→PPN mapping, R/W/X/U permissions and precise page-fault state to checkpoint authority, plus bounded fail-closed translation and visible-effect containment.

It does **not** claim a production MMU: no full or multi-level page-table walk, TLB refill/shootdown, accessed/dirty-bit semantics, huge pages, PMP/PMA, complete CSR semantics, virtualization/nested translation, cache/coherence behavior, multicore address-space synchronization, production speculation/reorder-buffer behavior, RTL SHA-256/off-path verifier correctness, durable-media correctness, production widths or unbounded correctness is claimed.

**Vulnerability claim:** false.  
**External safety certification:** false.
