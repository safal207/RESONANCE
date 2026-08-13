# RESONANCE Verified Report #034

# CaPU v0.29 — Partial / Multi-Beat DMA Recovery Authority

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#83`  
**Verified CaPU content head:** `64b7f26ec58e1f1f6a1f8553b458098610ec5c96`  
**Workflow:** `CaPU vCML Multi-Beat DMA Recovery v0.29`  
**GitHub Actions run:** `31672635544`

## Result

# **PASS — bounded ordered four-beat DMA recovery authority verified**

CaPU v0.29 extends verified v0.28 from one accelerator/DMA effect to one bounded ordered four-beat DMA transaction. The recovery problem is no longer binary at transaction scope: some beats may already be durably committed, one beat may be unresolved, and later beats may not yet have issued.

The target crash window is:

```text
beat0 -> COMMITTED
beat1 -> COMMITTED
beat2 -> UNKNOWN
beat3 -> UNISSUED
        ↓
      crash
        ↓
recovery must preserve:
  beat0 / beat1 -> never replay
  beat2         -> require discriminating evidence
  beat3         -> no authority until the prefix is committed
```

The bounded model treats a committed prefix as externally irreversible. Recovery does not roll the transaction back to beat 0 and does not guess whether an unresolved beat committed.

## Exact-head verification

All pull-request workflows registered on the exact v0.29 content head are green:

```text
content head:
64b7f26ec58e1f1f6a1f8553b458098610ec5c96

CaPU vCML Multi-Beat DMA Recovery v0.29
run 31672635544 — PASS
  deterministic job 94360334079 — PASS
  formal job        94360334250 — PASS

CaPU Core v0 RTL Smoke
run 31672635546 — PASS
  deterministic smoke job 94360334443 — PASS
  bounded STORE proof     94360383648 — PASS

Validate Examples
run 31672635539 — PASS
  validation job 94360334147 — PASS
```

GitHub Actions checked PR merge ref `c66e7214cdfba4a2645917f4d375d2e5de410a00`; run and artifact metadata is associated with content head `64b7f26e...`.

## Per-beat authority model

Each modeled beat has one of four states:

```text
UNISSUED | UNKNOWN | COMMITTED | NOT_COMMITTED
```

Verified bounded authority rules:

```text
COMMITTED
=> NO_REPLAY

UNKNOWN
=> EVIDENCE_REQUIRED
&& NO_REPLAY

NOT_COMMITTED
=> REPLAY_MAY_REOPEN_FOR_THIS_EXACT_BEAT
&& ALL_EARLIER_BEATS == COMMITTED

UNISSUED
=> ISSUE_MAY_OPEN_FOR_THIS_EXACT_BEAT
&& ALL_EARLIER_BEATS == COMMITTED

RETIRE
=> ALL_4_BEATS == COMMITTED
&& COMPLETION_RECEIPT_BITMAP == 1111
```

The model therefore blocks a later beat from jumping over an unresolved gap.

## Durable per-beat evidence

v0.29 models three four-bit evidence maps bound to one exact transaction identity:

- `issue_receipt_bitmap` — beat entered the unresolved issued window;
- `negative_receipt_bitmap` — exact evidence proved that beat did not commit;
- `completion_receipt_bitmap` — exact evidence proved that beat committed.

Exact transaction identity is:

```text
command_id
+ execution_epoch
+ effect_id
```

Per-beat restore precedence is:

```text
completion receipt
  > current issue receipt
  > durable negative receipt
  > checkpoint beat state
```

This carries the v0.28 `UNKNOWN` / negative-evidence convergence model down to individual beats of one ordered transaction.

## Deterministic trajectory

The exact-head executable run produced:

```text
command_submit accepted=1 command=11 execution_epoch=6 effect=13 beats=4
beat0 committed=1 durable_completion_receipt=1 replay_blocked=1
beat1 committed=1 durable_completion_receipt=1 replay_blocked=1
beat2 issued=1 completion=UNKNOWN evidence_required=1 tail_beat3_blocked=1
partial_checkpoint beats=COMMITTED,COMMITTED,UNKNOWN,UNISSUED
partial_restore committed_prefix_replay_blocked=1 unresolved_beat_requires_evidence=1 tail_blocked=1
foreign_beat_evidence rejected=1 exact_transaction_identity_required=1
negative_evidence beat=2 durable_negative_receipt=1 replay_authority=1 tail_blocked=1
stale_partial_restore negative_receipt_wins=1 beat2=NOT_COMMITTED replay_authority=1
beat2_retry accepted=1 old_negative_receipt_consumed=1 completion=UNKNOWN
retry_crash_restore current_issue_witness_wins=1 beat2=UNKNOWN replay_authority=0
prefix_complete beat0_2_committed=1 beat3_authority=1
beat3 committed=1 all_beats_committed=1 durable_completion_bitmap=1111
command_retire accepted=1 exact_multibeat_completion=1
late_stale_partial_restore completion_receipts_win=1 all_beats=COMMITTED replay_bitmap=0000
CAPU_VCML_MULTIBEAT_DMA_RECOVERY_V29_PASS
```

This trajectory demonstrates all three important recovery outcomes inside one transaction:

1. committed beats remain non-replayable;
2. an unresolved beat remains evidence-gated;
3. an unissued tail beat obtains authority only after the committed prefix advances through the unresolved beat.

## Canonical checkpoint binding

Canonical v0.29 checkpoint digest:

```text
d5d75cc5050f6971bf1115aea89787f2c66eee212090fd5bb8de7295b8e1014d
```

The canonical payload binds:

- verified v0.28 canonical digest;
- live transaction identity;
- live four-beat state vector;
- checkpoint transaction identity;
- checkpoint four-beat state vector;
- issue / negative / completion receipt bitmaps;
- exact receipt transaction identity.

Mutation checks PASS:

```text
committed_prefix_replay_mixed_state_rejected=1
foreign_receipt_identity_mixed_state_rejected=1
stale_negative_receipt_survives_retry_mixed_state_rejected=1
partial_checkpoint_state_substitution_rejected=1
VCML_MULTIBEAT_DMA_CHECKPOINT_V29_PASS
```

## Executable evidence

```text
artifact:
capu-vcml-v29-multibeat-dma-evidence

artifact ID:
9170272979

ZIP SHA256:
764d259499ae53f08a14d77d0131c747bc7a1c2acc5237591dfb395e9d2c8d43
```

Sealed hashes:

```text
RTL:
a93675cfcad7a46a2854e76d7e234cecd84d3ce5d5df28c880568a76e027982f

TB:
f7be9b55f5585f321a761f3925173629d494783245d24ab60df33c0ad44e3c4c

canonical encoder:
ffe594f7425c8195f397ffdf2b1b7d34bd359450275d0df96678e9a0063f05a9

canonical test:
584b6fffeb9218d5a65f182fad22aeb10ea4109c626cb6d52cd06c1d7b2d3bd2

trajectory log:
afdde95759df8207b14e0dadcdaa8887e56e18fee58f72796bc15f274b58277b

canonical Python log:
bab92f3012794e9f9472d47944cfa1dfd1239708e75d647e31f89a549db59943

v0.28 deterministic regression log:
1dab18550b919b10c90a1c6983381bc5cdf3032b75c7337e474d8d2929b22a6c

v0.28 canonical regression log:
397306fcec5e07393de58c285407f807b9c3f5897b4644f6e11024d7d5a3c964
```

## Formal evidence

v0.29 deliberately uses **bounded model checking**. This is not an inductive or unbounded correctness claim.

```text
schema:
capu.hardware.multibeat-dma-recovery-formal-proof.v0.29

beat count: 4
formal identity width: 2 bits

safety depth: 18
result: DONE (PASS, rc=0)
safety traces: none

cover depth: 36
result: DONE (PASS, rc=0)
VCD witnesses: 10

v0.28 bounded safety regression: PASS
```

Pinned toolchain:

```text
SBY:
b1a1e98cba941ec8433f8dc27f416cd7bb7f14be

Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input SHA256:
b685005e03e1dff7544ea1e3c8c488639e3084eea41308bb885b15b65e7b94f3

safety log SHA256:
e555bbe7b407584795e2e59db01adfc588d1d5e65e098bee4d2056eadb93b5c1

cover log SHA256:
47f6781e77241d4dd3d55410b75aa9392471aa7c8a83c8acf75f67ab70474590

v0.28 regression log SHA256:
143b27e3de0721fa8797f3159b70a589050579bdb46c4c682b22af919e3b6e8d
```

Formal artifact:

```text
artifact:
capu-vcml-v29-multibeat-dma-formal-evidence

artifact ID:
9170387478

ZIP SHA256:
12a4c0db84b3dd1836062fd74a8f4749874b5444f131ddbd62787c08bff91769
```

## Verification-bound refinement

The first v0.29 candidate requested safety depth 22. Expanding the state from one effect to four independent beat states plus three per-beat evidence maps made the no-incremental SMT instance materially more expensive. That candidate did not provide the final authority record.

The final exact head deliberately scopes safety to depth 18 while retaining cover depth 36 and the complete deterministic path. No RTL, testbench, canonical encoding or safety invariant was weakened to obtain the final PASS. All predecessor regressions were then re-run on the same final head.

## What this proves

Within the bounded model, v0.29 verifies that:

```text
COMMITTED_BEAT
=> cannot regain replay authority

UNKNOWN_BEAT
=> cannot replay or authorize a later beat without evidence

EXACT_NOT_COMMITTED_BEAT
=> may regain replay authority for that beat only

RETRY_OF_NEGATIVE_BEAT
=> consumes old negative evidence
&& becomes fresh UNKNOWN

COMMITTED_PREFIX_ADVANCES
=> next unissued beat may receive authority

ALL_BEATS_COMMITTED
=> transaction may retire

STALE_PARTIAL_CHECKPOINT
=> cannot override fresher exact per-beat evidence
```

## Claim boundary

This is a **bounded reduced-width one-command, one ordered four-beat DMA-transaction recovery-authority model** layered on verified v0.28.

It verifies modeled per-beat replay containment, committed-prefix ordering, per-beat `UNKNOWN` evidence gating, durable per-beat issue/negative/committed evidence, stale partial-checkpoint reconciliation and all-beat retirement gating.

It does **not** prove:

- production PCIe/CXL/NoC beat semantics;
- byte enables or cache-line tearing;
- burst splitting or device-memory ordering;
- IOMMU/cache/coherence behavior;
- atomicity across real persistence domains;
- arbitrary burst length;
- out-of-order or overlapping DMA fragments;
- multiple outstanding DMA transactions;
- queue ordering or completion interrupts;
- real evidence authenticity/durability implementation;
- production widths;
- liveness/fairness;
- unbounded correctness.

## Next boundary

The ordered-prefix assumption is now the largest remaining simplification in this DMA recovery line.

A natural v0.30 target is **Out-of-Order / Overlapping DMA Fragment Recovery Authority**:

```text
fragment0 -> COMMITTED
fragment1 -> UNKNOWN
fragment2 -> COMMITTED
fragment3 -> UNISSUED
```

At that point the externally visible committed set is no longer a simple prefix, so recovery authority must be represented as an exact fragment set rather than one advancing frontier.

---

**RESONANCE** — *Find the signal. Verify the path. Understand the future.*
