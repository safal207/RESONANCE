# RESONANCE Verified Report #024

# CaPU v0.19 — Delegated + Nested Trap Authority

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#72`  
**Verified CaPU content head:** `16ac81286cf6542189021f6a9aa3a3773c003e31`  
**Workflow:** `CaPU vCML Delegated Nested Trap Authority v0.19`  
**GitHub Actions run:** `31656176115`

## Result

# **PASS — bounded delegated two-level trap authority verified**

CaPU v0.18 bound one trap/privilege context to the exact architectural/causal/replay checkpoint authority. v0.19 addresses the next boundary: nested trap entry and return must preserve parent context while the authority deciding the target privilege is itself part of the checkpointed state.

The bounded v0.19 record adds:

```text
v0.18 exact checkpoint
+ current privilege
+ delegation mask
+ trap depth 0..2
+ outer trap frame
+ inner trap frame
        ↓
one canonical payload / commitment
```

Each trap frame records trap kind, cause, return PC, return privilege and target privilege.

Central invariant:

# **A NESTED TRAP MAY ENTER ONLY UNDER CHECKPOINT-BOUND DELEGATION AUTHORITY, AND RETURN MUST RESTORE THE EXACT TOP PARENT CONTEXT**

## Threat model

v0.19 fails closed for several valid-components / invalid-composition cases:

```text
valid v0.18 state
+ foreign delegation policy
= reject by checkpoint binding

valid nested trap
+ foreign outer parent context
= reject by checkpoint binding

unauthorized target privilege
= no trap entry

depth 2 + another trap
= overflow reject

depth 0 + return
= underflow reject
```

The delegation policy is not ambient configuration. It is part of the checkpoint-authoritative payload. This prevents a recovered trap stack from silently inheriting a different post-recovery delegation policy.

## Deterministic trajectory

The exact-head executable trajectory covers:

```text
unauthorized target privilege               → reject
outer trap                                  → capture base PC/privilege, depth 1
nested trap                                 → capture outer PC/privilege, depth 2
pre-nested speculative effect               → killed, not visible
third trap                                  → overflow reject
nested return                               → exact outer parent, depth 1
outer return                                → exact base context, depth 0
return at depth 0                           → underflow reject
wrong-privilege normal continuation         → reject
mutated delegation checkpoint candidate     → reject
exact checkpoint authority path             → accept
recovery                                    → runtime closed
```

Final marker:

```text
CAPU_VCML_DELEGATED_NESTED_TRAP_V19_PASS
```

Canonical v0.19 checkpoint digest:

```text
90543218d6e93fed2dd58169a815a01453dcc88196f42b5851ce8f555d180f38
```

Mutation tests prove the commitment changes when the delegation mask, outer parent context or nested context changes. Mixing a valid base with a foreign parent context fails commitment verification.

## Formal verification

Final exact-head workflow:

- run `31656176115`;
- deterministic/canonical job `94311014663` — **success**;
- bounded formal job `94311060795` — **success**.

Safety:

```text
depth: 28
solver: Z3 4.8.12
Yosys: 0.33 (git sha1 2584903a060)
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
DONE (PASS, rc=0)
```

The safety run produced no counterexample trace.

Reachability:

```text
cover depth: 34
VCD witness files: 9
DONE (PASS, rc=0)
```

The witnesses demonstrate that the modeled restore, rejection, nested-entry, return, overflow/underflow, checkpoint and speculative-containment paths are reachable rather than vacuous assertions.

The v0.18 bounded safety proof also completed successfully inside the v0.19 workflow.

Formal proof schema:

```text
capu.hardware.delegated-nested-trap-authority-formal-proof.v0.19
```

Formal hashes:

```text
formal input SHA-256:
09a014afe4d886c53c48e01e56405935f1996c483b34e710addc2c2f09d5ff0a

safety log SHA-256:
50617924cea12b7a638e12339e3e1011054cb3b690b880212669e891914f6dcf

cover log SHA-256:
8c1a6ff8b9c86a430d847a360213f5ffcfb64f5aabb61498d6f5436aa7eee9f1

v0.18 regression log SHA-256:
63ac89bd78d513f678e1cd62723fc9ab90bc76c6e4a2266fe382f93e8d20bc2c
```

## Executable evidence

Hashes sealed by the exact-head workflow:

```text
v0.19 RTL:
7d1d03f7c0629f3f34731ca504d1cc8e312b378918488de8a9e45d8f4084f116

v0.19 deterministic TB:
7d5ef37d2ce21e470b09ffc7fa8406af21cc6085a0bde3d5f04a698340179907

v0.19 canonical encoder:
a5582fc0972a6ef6a41545c246366e2f89e26202a0e18baad0444c7c1a6bf393

v0.19 canonical test:
ae09890cf0185c327a02f4eb5ee7be79c68f966fa0e7c83778ee00ee58c7863b

trajectory log:
ceb61b3722b98560fb5aa0bdfe9b2ababd8f88ad67d2670c2aab4419c737209d

canonical Python log:
d40f657b18a8285760b8d4f4da6534925c04c10f54fef6a0d4870ca7c01f5c29
```

Evidence artifacts:

```text
capu-vcml-v19-delegated-nested-trap-evidence
artifact ID: 9164456375
ZIP SHA-256: 4d1425c3a2c32f2f1348f84ce04d548eb04ce472ca84c0ce91f531a44412364a

capu-vcml-v19-delegated-nested-trap-formal-evidence
artifact ID: 9164504572
ZIP SHA-256: 4eca67ce324a6a89bc884a1f07061a4978406459f8efaa4ee9b446a5e9d3b0c0
```

## Exact-head regression status

On verified CaPU head `16ac81286cf6542189021f6a9aa3a3773c003e31`:

```text
CaPU vCML Delegated Nested Trap Authority v0.19 — PASS
Validate Examples — PASS
CaPU Core v0 RTL Smoke — PASS
v0.18 deterministic + canonical regression — PASS
v0.18 bounded safety regression — PASS
```

## Claim boundary

This result is deliberately narrow. v0.19 proves a **bounded reduced-width two-level delegated trap authority model**.

It establishes that the modeled delegation policy, trap depth and two trap frames are bound to the same checkpoint authority as the embedded v0.18 state; unauthorized delegation fails closed; nested entry captures the exact parent PC/privilege; top-frame return restores that exact parent context; bounded overflow and underflow reject; and modeled visible effects cannot cross accepted trap/recovery boundaries.

It does **not** establish:

- full RISC-V, x86, ARM or other ISA CSR/delegation semantics;
- arbitrary or unbounded nesting;
- production trap-stack storage correctness;
- MMU/TLB or page-fault recovery;
- NMI/debug semantics;
- interrupt-controller behavior or asynchronous interrupt synchronization correctness;
- production speculation or reorder-buffer semantics;
- cache/coherence/multicore recovery;
- SHA-256 verification inside RTL or off-path verifier correctness;
- durable-media correctness;
- production-width or unbounded correctness.

## Why this matters

v0.18 answered: **can a checkpoint-bound privilege/trap context resume and take or return one precise trap safely?**

v0.19 now answers: **when traps nest, is the authority to enter the next privilege itself recoverable evidence, and can each return be causally tied to the exact parent context it interrupted?**

The natural next boundary is page-fault / address-translation recovery: execution authority should not resume under architectural and causal state A while using stale or unrelated translation authority B.
