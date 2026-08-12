# RESONANCE Verified Report #020

# CaPU v0.15 — Live Causal Execution Resumption

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU content head:** `7bdb355a1854db88230174db15adacf654b952d5`  
**Workflow:** `CaPU vCML Live Causal Resume v0.15`  
**GitHub Actions run:** `31603759854`

## Result

# **PASS — bounded live causal execution resumption verified**

CaPU v0.14 proved that a checkpoint can bind and recover the finite replay spent-set together with the committed causal record: causal-head validity, causal-head transition ID, committed GEN and SEAL.

v0.15 addresses the next missing boundary:

> Can an already accepted recovered causal record safely become the live continuation state after reset, without creating a new causal history or allowing pre-recovery speculation to cross the recovery boundary?

The v0.15 runtime composes:

```text
v0.14 accepted full causal snapshot
        ↓
restore replay spent-set
        +
restore causal head / GEN / SEAL
        ↓
live causal state ready
        ↓
ordinary v0.9 continuation policy
        ↓
exact parent
+ next GEN
+ unsealed chain
+ GEN != F
        ↓
visible STORE retirement
```

Central invariant:

# **RECOVERED CAUSAL RECORD ≠ LIVE EXECUTION STATE UNTIL RECOVERY ATOMICALLY RE-ESTABLISHES THE POLICY STATE AND REOPENS ADMISSION**

## Recovery as a speculation barrier

A key v0.15 failure mode is a STORE that entered the speculative buffer before recovery began. Closing only new admission is not enough: that old candidate must not retire after the system has crossed into a different recovered causal state.

v0.15 therefore treats recovery activity as an explicit speculation barrier:

```text
RECOVERY_OR_RESTORE_ACTIVITY
=> SPECULATION_FLUSHED
&& NO_VISIBLE_EFFECT
```

`recovery_begin` and every restore attempt flush the old candidate before execution can resume.

## Live state restoration

Given a structurally valid snapshot already accepted by the upstream v0.14 checkpoint authority / commitment boundary, v0.15 restores:

- the finite spent root-authorization set;
- `causal_head_valid`;
- `causal_head_transition_id`;
- committed 4-bit `GEN`;
- committed `SEAL` / `sealed_chain`.

All operation classes remain fail-closed until both replay recovery and causal runtime restoration are ready:

```text
EXECUTION_BEFORE_RUNTIME_RESTORE
=> REJECT
```

An accepted restore must establish the exact live causal state on the next runtime state:

```text
RESTORE_ACCEPT
=> NEXT_LIVE_CAUSAL_STATE == ACCEPTED_CAUSAL_SNAPSHOT
```

## Continuation after recovery

v0.15 does not introduce a separate recovery-specific continuation policy. After restore, ordinary execution reuses the existing causal admission rules:

```text
NORMAL_CONTINUATION_ADMIT
=> PARENT == LIVE_HEAD
&& GEN == LIVE_GEN + 1
&& !SEAL
&& LIVE_GEN != F
```

This preserves earlier barriers:

- wrong predecessor remains reject;
- wrong next GEN remains reject;
- recovered SEAL blocks automatic continuation;
- recovered `GEN=F` blocks automatic wrap;
- a restored spent root-authorization reference remains replay-rejected.

## Deterministic trajectory

The executable v0.15 trajectory covers:

```text
restore head=0x2201 / GEN=6 / SEAL=0 + spent A110
        ↓
A110 root replay                  → reject
wrong parent child                → reject
wrong GEN child                   → reject
parent=0x2201 / GEN=7 child       → admit + visible retire
live head becomes 0x2202 / GEN=7

recovery_begin                    → admission closes immediately
restore sealed head              → automatic child reject
fresh explicit root              → legitimate new chain
restore GEN=F                     → automatic F→0 wrap reject
```

Marker: `CAPU_VCML_LIVE_RESUME_V15_PASS`.

## Formal verification

Final documented-head workflow:

- run `31603759854`;
- RTL/composition job `94137351710` — **success**;
- bounded formal job `94137473225` — **success**.

Safety:

```text
depth: 24
solver: Z3
Yosys: 0.33
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
DONE (PASS, rc=0)
```

Reachability:

```text
cover depth: 28
VCD witnesses: 7
DONE (PASS, rc=0)
```

The bounded safety proof checks recovery admission, speculative-flush behavior, exact restored live state, ordinary continuation policy, recovered SEAL/GEN exhaustion and restored replay rejection. Independent cover witnesses demonstrate that resume and fail-closed paths are reachable in the reduced formal instance.

Formal hashes:

```text
formal input SHA-256:
ef4846e071b3e559f4236c4929491a6ae65b84d6bacd87fee2c68e5793c75963

safety log SHA-256:
fbc5bceb0b6112dee1eedf7322175a4e4c604cc6eed7ce9a2a32568e876bc757

cover log SHA-256:
46a6f09c7b878ec9d2608ba33023541334fcf1ed75f9d4006848de31aeee7d94
```

Evidence artifacts:

```text
capu-vcml-v15-live-resume-evidence
artifact ID: 9144210426
ZIP SHA-256: 25a55198e082f453322c1989d185a7e303d9a4f4d4c26f855639acd99d9d1dfb

capu-vcml-v15-live-resume-formal-evidence
artifact ID: 9144259726
ZIP SHA-256: 528ca761f932645ded7db8e87ec051a0f321d77400be63891366c7cfa0d09032
```

## Exact-head regression status

On verified CaPU head `7bdb355a1854db88230174db15adacf654b952d5`, all of the following completed successfully:

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
```

This verifies that the new optional runtime-restore path did not break the previously bounded lower-layer workflows on that exact source head.

## Claim boundary

This result is deliberately narrow.

v0.15 assumes `restore_valid` is driven only by a structurally valid snapshot already accepted by the upstream v0.14 checkpoint authority / commitment boundary. The standalone v0.15 proof therefore does **not** independently establish:

- SHA-256 or commitment verification correctness;
- checkpoint freshness or external anchor correctness;
- external CAS correctness;
- durable-media correctness or power-loss persistence;
- source-history omission resistance;
- complete CPU architectural-state recovery;
- register-file, cache, predictor, TLB, ISA or coherence recovery;
- distributed recovery correctness;
- unbounded or parametric correctness.

The formal instance is finite and reduced-width. The claim is local to the modeled causal STORE runtime.

The verified result is: **given an already accepted full causal checkpoint snapshot, CaPU fails closed during recovery, flushes old speculation, restores the finite replay set plus committed causal head / GEN / SEAL into the live execution controllers, and resumes local continuation under the same causal admission rules that governed execution before failure.**

## Why this matters

v0.10 answered: **which root authorizations were already spent?**  
v0.11 answered: **which recovery checkpoint is current?**  
v0.12 answered: **when does a checkpoint become recovery authority?**  
v0.13 answered: **which replay-state content does that authority refer to?**  
v0.14 answered: **which committed causal position does that checkpoint represent?**  
v0.15 now answers: **can that recovered causal position safely become the live continuation state after reset?**

The next boundary is no longer merely checkpoint representation. It is the broader execution-recovery surface: which additional architectural state must be included before the same causal recovery claim can extend beyond this local STORE path.
