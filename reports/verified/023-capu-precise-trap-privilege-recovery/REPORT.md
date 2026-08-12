# RESONANCE Verified Report #023

# CaPU v0.18 — Precise Trap / Privilege Recovery

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#71`  
**Verified CaPU content head:** `dc47ba9801d8c17862d600d55c8795f7dfd9d61e`  
**Workflow:** `CaPU vCML Precise Trap Privilege Recovery v0.18`  
**GitHub Actions run:** `31619671057`

## Result

# **PASS — bounded exact trap / privilege checkpoint recovery verified**

v0.17 established one exact checkpoint authority over the minimal architectural state plus causal and replay state.

v0.18 extends that authority to the smallest trap/privilege context needed to make local resumption precise across an exception or interrupt boundary:

```text
v0.17 checkpoint record
+ current privilege mode
+ trap pending
+ trap kind
+ trap cause
+ trap return PC
+ trap return privilege
+ interrupt mask
        ↓
one domain-separated canonical v0.18 payload
        ↓
one SHA-256 commitment
        ↓
PREPARE → PERSIST → ANCHOR → EXACT RESTORE
```

The runtime model then checks that resumed execution follows the restored privilege/trap context.

Central result:

# **THE AUTHORITY THAT SAYS WHERE EXECUTION MAY RESUME ALSO BINDS THE BOUNDED CONTROL STATE THAT SAYS HOW THAT EXECUTION IS LEGAL**

## Threat model

### Foreign trap / privilege context

```text
valid v0.17 architectural + causal + replay state A
+
trap / privilege context B
=
REJECT
```

Matching checkpoint or recovery epochs cannot make foreign trap bytes authoritative. The explicit restore fields must re-pack to the exact anchored v0.18 payload.

### Wrong-privilege continuation

```text
normal step privilege != live restored privilege
=> REJECT
```

A correct PC alone is insufficient if execution is presented under the wrong privilege mode.

### Interrupt masking and priority

A masked interrupt cannot enter the modeled trap path. When an exception and an unmasked interrupt are presented together, the exception has strict priority.

### Pre-trap speculation

The model includes one abstract speculative visible-effect slot only to state the trap precision property. If a trap is taken while a pre-trap effect is pending, that effect cannot become visible in the trap-entry cycle and the pending speculation is discarded.

Speculative-effect state is deliberately **not checkpoint authority state**.

## Bounded trap semantics

The v0.18 execution surface is deliberately small:

- 2-bit privilege mode;
- one pending trap context;
- exception or interrupt kind;
- bounded cause code;
- return PC;
- return privilege;
- one interrupt-mask bit;
- no nested trap stack.

Accepted trap entry atomically records the pre-trap return PC and privilege, selects the exception/interrupt cause and vector, changes live privilege to the supplied target mode, and blocks a visible effect in that boundary cycle.

Trap return is accepted only when one live trap context is pending. It restores the recorded return PC and return privilege and clears the pending trap marker.

## Deterministic trajectory

The exact-head executable path produced:

```text
prepare_privilege_mutation rejected=1 exact=1
restore_privilege_mutation rejected=1
exact_restore ready=1 pc=40 privilege=1 mask=1
privilege_mismatch rejected=1
masked_interrupt rejected=1
exception_priority precise=1 return_pc=40 return_privilege=1
trap_return exact=1 pc=40 privilege=1
recovery_priority runtime_closed=1
CAPU_VCML_TRAP_PRIVILEGE_V18_PASS pc=41
```

The trajectory therefore covers:

1. mutation of privilege bytes before checkpoint authority;
2. exact prepare → persist → anchor authority;
3. restore rejection when the anchor is valid but explicit privilege state differs;
4. exact restore of PC, privilege, trap-idle context, mask and embedded v0.17 base payload;
5. wrong-privilege normal-step rejection;
6. masked-interrupt rejection;
7. one admitted speculative effect;
8. simultaneous exception + interrupt + effect commit, with exception priority and no visible effect;
9. destruction of the pre-trap speculative effect;
10. exact trap return to the recorded PC and privilege;
11. correct-privilege continuation;
12. recovery closing runtime readiness.

## Canonical checkpoint verification

The v0.18 off-path canonical encoder embeds the complete v0.17 canonical checkpoint record beneath a new v0.18 domain separator, then appends the trap/privilege fields.

Canonical test digest:

```text
da7f80efe0eac2695edf367ee42193ab6100bd184b091da8f1f00d0797f0c16e
```

Mutation tests verify digest changes for:

- privilege mode;
- trap context;
- interrupt mask;
- embedded architectural state;
- embedded causal/replay state.

A valid v0.17 base combined with foreign trap/privilege bytes fails verification under the original commitment.

## Formal verification

Exact-head v0.18 workflow:

- run `31619671057`;
- deterministic/canonical job `94191037153` — **success**;
- bounded formal job `94191128567` — **success**.

Safety:

```text
depth: 26
solver: Z3 4.8.12
Yosys: 0.33 (git sha1 2584903a060)
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
DONE (PASS, rc=0)
safety traces: none
```

Reachability:

```text
cover depth: 30
VCD witness files: 7
DONE (PASS, rc=0)
```

The seven VCD witnesses collectively reach the bounded paths for exact restore/mismatch, privilege rejection, masked interrupt, exception entry, interrupt entry, trap return, speculation kill and checkpoint authority commit; several cover statements may share one witness.

Reduced formal instance:

```text
checkpoint ref width: 3
checkpoint epoch width: 3
checkpoint commitment width: 4
embedded base payload width: 12
PC width: 4
privilege width: 2
cause width: 3
```

Formal proof schema:

```text
capu.hardware.precise-trap-privilege-recovery-formal-proof.v0.18
```

Formal hashes:

```text
formal input SHA-256:
2e68ea48f706250bb37faf860e03b8319acc3468f95b9659212e35eef1e5c1b1

safety log SHA-256:
a24f5a3f5e54ecf84cd03a1c852a78a0785980626d765b2ef65221318937ab61

cover log SHA-256:
32b5742b2e38391d59db90491cc88b950948caec355d3bcb698080fb6d6e5ff3

v0.17 safety regression log SHA-256:
ae2e07ead9f957d1ff79ddcf635e0de0d28d3c59332afaa90a6e1be10171af2d
```

## Evidence artifacts

Executable evidence:

```text
capu-vcml-v18-trap-privilege-evidence
artifact ID: 9150699573
ZIP SHA-256: 98a4c6ec7a37ce573013730c83ed4bf8116dc224ec381df9a548dcaae26084f4
```

Formal evidence:

```text
capu-vcml-v18-trap-privilege-formal-evidence
artifact ID: 9150741321
ZIP SHA-256: d75ff8bd4889bd479d20a7f6b097375b5db5ec5020497c11d6273381b61b2ca9
```

Executable file/log hashes:

```text
v0.18 RTL:
c1a170a7bbe97737d2446664af919423613c8c418ada5555f3238a45b98a88e0

v0.18 deterministic TB:
a933aa6f93bc254304218d45b26402d692d846900e10b31a8d93d9ddfc75e88f

v0.18 canonical encoder:
22c3929e9f2b994f53c12ec15f839aa08f24229e3c8f5717321f33f07ecc49e6

v0.18 canonical test:
66c6a5344fd7dfdc4f636f05c49af2a0780adbcd389c7a27bf935dc783adce26

trajectory log:
667aab26d18800bdb02e3edbc23fa2a329aacef753b8260f526c2259fd297e4d

canonical Python log:
f421a549b69c622f7c167986305d1528f3bc7e5152daf80ed4e744b3ad52f2c5
```

## Regression status

All pull-request workflows registered on exact CaPU head `dc47ba9801d8c17862d600d55c8795f7dfd9d61e` completed successfully:

```text
CaPU vCML Precise Trap Privilege Recovery v0.18
Validate Examples
CaPU Core v0 RTL Smoke
```

The v0.18 workflow itself also completed:

```text
v0.17 deterministic checkpoint regression — PASS
v0.17 canonical SHA-256 regression       — PASS
v0.17 bounded safety regression           — PASS
```

Core RTL Smoke completed both its deterministic and bounded formal jobs successfully.

## Core formal invariants

The sealed formal proof records:

```text
RESTORE_ACCEPT
  => SNAPSHOT == ANCHOR == EXACT_REPACKED_TRAP_STATE

FOREIGN_TRAP_OR_PRIVILEGE_STATE
  => RESTORE_REJECT

PRIVILEGE_MISMATCH
  => NORMAL_STEP_REJECT

MASKED_INTERRUPT
  => NO_INTERRUPT_TRAP_ENTRY

EXCEPTION_AND_INTERRUPT
  => EXCEPTION_PRIORITY

TRAP_ENTER
  => SAVE_RETURN_CONTEXT && NO_VISIBLE_EFFECT

PRE_TRAP_SPECULATION
  => DISCARDED_ON_TRAP

TRAP_RETURN
  => RECORDED_PC_AND_PRIVILEGE

RECOVERY_OR_RESTORE
  => NO_CHECKPOINT_AUTHORITY_TRANSITION
```

## Claim boundary

v0.18 is a **bounded reduced-width one-trap privilege-recovery result**.

It does **not** establish:

- a full RISC-V, x86, ARM or other ISA exception model;
- nested traps or a trap stack;
- complete CSR or delegation semantics;
- page faults, TLB/MMU state or privilege-dependent address translation;
- NMI/debug mode;
- timer/external interrupt-controller behavior;
- asynchronous interrupt synchronization or metastability correctness;
- a production reorder buffer or full speculative pipeline;
- cache/coherence/multicore recovery;
- SHA-256 verification inside RTL or off-path verifier trustworthiness;
- durable-media correctness;
- production-width or unbounded correctness.

The precise narrow claim is: **one bounded trap/privilege context is content-bound to the same exact checkpoint authority as the v0.17 architectural/causal/replay record; restored local execution fails closed on foreign trap bytes, wrong privilege and masked interrupt, while exception priority, return-context capture, trap return and pre-trap speculative-effect containment hold within the modeled transitions.**

## Why this matters

v0.17 answered: **are the exact architectural and causal bytes the bytes checkpoint authority committed to?**  
v0.18 answers: **can the processor resume across a bounded trap/privilege boundary without losing that same authority and without allowing the wrong execution mode or pre-trap effect to leak through?**

A natural next boundary is nested/delegated trap state or privilege-specific CSR authority. Adding more microarchitectural state before that control authority is modeled would make the checkpoint wider without yet making the recovery semantics more complete.
