# RESONANCE Verified Report #021

# CaPU v0.16 — Causally Bound Architectural Execution Resumption

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU content head:** `4bc80b38cce8b9b7a9428e9182d8ff016f164e63`  
**Workflow:** `CaPU vCML Architectural Causal Resume v0.16`  
**GitHub Actions run:** `31612609824`

## Result

# **PASS — bounded architectural + causal execution resumption verified**

CaPU v0.15 proved that an already accepted causal/replay recovery snapshot can become the live policy state used by subsequent local STORE execution.

v0.16 addresses the next missing boundary:

> Can a minimal architectural execution context resume together with the recovered causal/replay context without allowing state from different recovery epochs to compose, and without allowing recovery-boundary speculation to become visible?

The v0.16 model adds a deliberately small architectural context:

```text
architectural state
  PC
  four GPRs
  status byte

causal / replay state
  causal head
  GEN
  SEAL
  finite spent-authorization set

+ one accepted recovery epoch
```

The architectural wrapper composes with the already-verified v0.15 runtime. It does not replace the earlier exact-parent / next-GEN / SEAL / replay admission rules.

Central invariant:

# **ARCHITECTURAL STATE AND CAUSAL STATE MUST RESUME AS ONE ACCEPTED RECOVERY EPOCH BEFORE EXECUTION MAY BECOME VISIBLE**

## Split-State Recovery

The new v0.16 threat model is a recovery assembled from independently plausible but unrelated state components:

```text
PC / GPR / status from epoch A
+
causal head / GEN / SEAL / replay set from epoch B
=
REJECT
```

The executable and bounded formal model enforce:

```text
SPLIT_STATE_EPOCH_MISMATCH
=> RESTORE_REJECT
&& RECOVERY_BARRIER
&& NO_VISIBLE_EFFECT
```

This closes the case where a valid causal chain could otherwise authorize an unrelated architectural computation, or a valid architectural context could inherit unrelated causal provenance.

## Recovery / restore as a visible-effect barrier

Formal exploration exposed a recovery-boundary race that the deterministic trajectory did not initially reveal: a pre-boundary STORE could already have a retirement pulse pending while recovery or restore activity began.

v0.16 therefore places a hard visible-effect boundary around recovery and restore:

```text
RECOVERY_OR_RESTORE_ACTIVITY
=> NO_VISIBLE_EFFECT
```

The wrapper masks `memory_write_enable` and `vcml_event_valid` whenever recovery or restore is active, while the underlying v0.15 runtime clears or replaces speculative state.

Formal also exposed a separate false-accept race when `recovery_begin` and `restore_valid` were simultaneously asserted. Recovery now has strict priority: a snapshot presented during `recovery_begin` cannot be reported as accepted when sequential recovery is clearing live state.

## Atomic live-state restoration

An accepted restore establishes the minimal architectural snapshot and the causal/replay snapshot under the same accepted recovery epoch:

```text
RESTORE_ACCEPT
=> NEXT_LIVE_ARCH_STATE == ACCEPTED_ARCH_SNAPSHOT
&& NEXT_LIVE_CAUSAL_STATE == ACCEPTED_CAUSAL_SNAPSHOT
&& LIVE_EPOCH == ACCEPTED_EPOCH
```

Execution remains fail-closed for a wrong architectural program counter:

```text
EXECUTION_PC != LIVE_PC
=> REJECT
```

A visible resumed STORE is sourced from restored architectural registers:

```text
VISIBLE_STORE
=> ADDRESS == LIVE_GPR[addr_reg]
&& DATA == LIVE_GPR[data_reg]
```

The downstream causal continuation policy remains unchanged from v0.15: exact parent, next GEN, unsealed chain, no GEN wrap, and restored root-authorization replay rejection.

## Deterministic trajectory

The executable v0.16 trajectory covers:

```text
architectural epoch 0x11
causal epoch        0x12
        ↓
split-state restore                      → reject

one accepted epoch 0x21
PC       = 0x40
GPR1     = 0x80   // STORE address
GPR2     = 0x55   // STORE data
status   = 0xA5
head     = 0x2201
GEN      = 6
SEAL     = 0
        ↓
issue at PC=0x41                       → reject
issue at PC=0x40 / parent=0x2201 / GEN=7
        ↓
visible STORE [0x80] = 0x55
head becomes 0x2202 / GEN=7
PC advances exactly once

buffer another STORE
        ↓
recovery + different restored epoch
        ↓
old speculative STORE                  → cannot retire
```

Final marker:

```text
CAPU_VCML_ARCH_RESUME_V16_PASS epoch=22 pc=60 head=3301 gen=2
```

## Formal verification

Final exact-head workflow:

- run `31612609824`;
- RTL trajectory job `94167473386` — **success**;
- bounded formal job `94167585994` — **success**.

Safety:

```text
depth: 28
solver: Z3 4.8.12
Yosys: 0.33 (git sha1 2584903a060)
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
DONE (PASS, rc=0)
```

Reachability:

```text
cover depth: 32
VCD witness files: 5
DONE (PASS, rc=0)
```

The reduced formal instance uses 4-bit address and transition-ID widths, 8-bit architectural data, four GPRs, a 3-bit recovery epoch and two spent-authorization slots.

Formal hashes:

```text
formal input SHA-256:
b3d5e40a94cf95e1e5351bee6e798159a1a558581b68b70e3bf9b0c1824eb4c0

safety log SHA-256:
9f80085c2b2348cc98371b4fa0756b7cea1a4b81e1312d51a5a9447ec663762a

cover log SHA-256:
9c85696eb37d65c8e62f6edce362b6aa45fb581a52068efa5c8ebca82916c1be
```

Executable hashes:

```text
v0.15 RTL:
784519183f324c47bd999b341c445ce86078fa5ad1d5771b3594aeb8ddf58141

v0.16 RTL:
c9a9162dd399930331866b25775080ed0f6b256f4aa9a9c560d08dbbb287ea8b

v0.16 deterministic TB:
90cd66648a4452d9c5c9ce7f386af3879e1aeb69e811711a1cd0284f96444905

trajectory log:
bbca1f52ffca31854bb374be84b7c6bb36683647783365e1236d59456bd499ab
```

Evidence artifacts:

```text
capu-vcml-v16-arch-resume-evidence
artifact ID: 9147838677
ZIP SHA-256: 669033e2235ba772bc2efdc5f31cf2ee9d960512459ef37535e6ceea28d90432

capu-vcml-v16-arch-resume-formal-evidence
artifact ID: 9147938150
ZIP SHA-256: 4b82984a5a7b15d5f4a1f02cd0072d7e476aaa013a0452bbd1a561a89af0bb2c
```

## Formal-driven development note

The final PASS was not obtained by weakening a failing architectural property.

Bounded formal first exposed two real recovery-boundary races, both fixed in RTL: recovery/restore false-accept priority and a visible retirement pulse crossing the recovery barrier.

A later counterexample at formal step 7 was traced through its VCD to the proof harness. The single-entry STORE buffer may retire the old entry while the next STORE is admitted in the same sampled cycle after the buffer becomes free. The shadow model incorrectly cleared the newly admitted entry with the old retirement bookkeeping. The harness was corrected to preserve the new admission; the same architectural safety properties then completed through depth 28.

## Exact-head regression status

On verified CaPU head `4bc80b38cce8b9b7a9428e9182d8ff016f164e63`, all of the following completed successfully:

```text
Validate Examples
CaPU Core v0 RTL Smoke
CaPU vCML Bridge v0 / v0.9
CaPU vCML Recovery v0.10
CaPU vCML Checkpoint v0.11
CaPU vCML Checkpoint Commit v0.12
CaPU vCML Checkpoint Content v0.13
CaPU vCML Full Causal Checkpoint v0.14
CaPU vCML Live Causal Resume v0.15
CaPU vCML Architectural Causal Resume v0.16
```

The v0.9 Bridge run also completed both bounded safety and reachability successfully on this exact head.

## Claim boundary

This result is deliberately narrow.

v0.16 proves a **bounded reduced-width minimal architectural recovery context coupled to the v0.15 causal/replay runtime by one accepted recovery epoch**.

It does **not** yet establish that `PC`, GPR or status bytes are cryptographically included in the upstream v0.14 checkpoint digest / anchor commitment. Matching accepted recovery epochs are enforced at the modeled runtime recovery boundary; stronger upstream content binding for the new architectural fields remains outside this result.

The result also does not establish:

- a full ISA or production-width register file;
- full CSR recovery;
- precise exception or interrupt recovery;
- privilege-state recovery;
- load or general memory-order recovery;
- cache state;
- TLB/MMU state;
- branch predictor state;
- coherence or multicore recovery;
- cryptographic verification inside RTL;
- durable-media correctness;
- distributed recovery correctness;
- unbounded or parametric correctness.

The verified result is: **given an already accepted v0.15 causal/replay recovery snapshot and a minimal architectural snapshot carrying the same accepted recovery epoch, CaPU fails closed across recovery/restore, rejects split-state epoch mixing and wrong-PC resumption, restores PC/GPR/status into the live architectural context, resumes a local STORE using restored register operands, and preserves the same causal continuation rules that governed execution before failure.**

## Why this matters

v0.14 answered: **which committed causal position does the checkpoint represent?**  
v0.15 answered: **can that recovered causal position safely become the live continuation state after reset?**  
v0.16 now answers: **can a minimal architectural computation resume with that causal state without mixing recovery epochs or leaking pre-recovery effects?**

A natural next boundary is the precise architectural control state around exceptions, interrupts and privilege transitions — while preserving the same fail-closed architectural+causal recovery principle.
