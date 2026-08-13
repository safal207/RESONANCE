# RESONANCE Verified Report #035

# CaPU v0.30 — Out-of-Order / Overlapping DMA Fragment Recovery Authority

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#84`  
**Verified CaPU content head:** `f2a70b31393e52f0fbb4f43dd14739c96a8a8bd0`  
**Base verified head (v0.29):** `64b7f26ec58e1f1f6a1f8553b458098610ec5c96`  
**Workflow:** `CaPU vCML Overlapping DMA Fragment Recovery v0.30`  
**GitHub Actions run:** `31682249200`

## Result

# **PASS — bounded out-of-order overlapping DMA fragment recovery authority verified**

CaPU v0.30 removes the ordered committed-prefix assumption of v0.29. It models one bounded four-fragment DMA transaction in which fragments may complete out of order and overlap the same four modeled byte lanes.

The fixed overlap map is:

```text
fragment0 -> lanes 0,1
fragment1 -> lanes 1,2
fragment2 -> lanes 2,3
fragment3 -> lanes 3,0
```

The key new state is durable per-byte **visible-owner provenance**. A committed fragment may be permanently non-replayable even when a later overlapping fragment becomes the current visible owner of some of the same lanes.

## Verified recovery path

The deterministic trajectory reached the intended non-prefix and overlap states:

```text
fragment_command_submit accepted=1 command=12 epoch=7 effect=14 fragments=4
out_of_order_commit committed_set=0101 owner_map=A0 prefix_assumption=0
overlap_checkpoint states=COMMITTED,UNKNOWN,COMMITTED,UNKNOWN owners=A0
recovery volatile_fragment_state_cleared=1 durable_receipts_preserved=1 durable_owner_preserved=1
partial_set_restore committed_nonprefix=0101 unknown=1010 replay_committed_blocked=1
foreign_fragment_evidence rejected=1 exact_transaction_identity_required=1
negative_fragment_evidence fragment=1 replay_authority=1 unrelated_fragment3_unknown=1
overlap_commit fragment=3 owners=E3 overwrote_lanes=3,0 committed_history_preserved=1
final_overlap_commit fragment=1 owners=D7 completion_bitmap=1111 all_fragments_committed=1
late_stale_restore completion_receipts_win=1 durable_owner_map_wins=1 states=ALL_COMMITTED owners=D7 replay=0000
fragment_command_retire accepted=1 exact_fragment_set_completion=1
CAPU_VCML_OVERLAPPING_DMA_FRAGMENT_RECOVERY_V30_PASS
```

The first deterministic candidate contained one testbench-only packed-state expectation error (`8'h88` instead of the correct `8'h22` for committed fragments 0 and 2). The final fix changed only that assertion. RTL, formal properties and canonical checkpoint semantics were unchanged.

## Canonical checkpoint authority

Canonical digest:

```text
116e51eed5468aebd1bc51aa6d9cfcf946a09384e0ead0db8fdd1fe69ccc4da9
```

The canonical state binds fragment state, issue/negative/completion receipts, exact transaction identity, checkpoint owner state and durable visible-owner provenance.

Mutation checks passed:

```text
committed_without_completion_receipt_rejected=1
foreign_receipt_identity_mixed_state_rejected=1
owner_without_fragment_commit_rejected=1
overlap_owner_wrong_lane_rejected=1
```

## Formal result

The v0.30 proof is explicitly **bounded model checking**, not an unbounded or inductive correctness claim.

```text
fragments: 4
byte lanes: 4
formal transaction identity width: 2 bits
safety depth: 14 — PASS
cover depth: 26 — PASS
VCD witnesses: 10
v0.29 bounded safety regression: PASS
```

Verified bounded invariants include:

```text
FRAGMENT_COMMITTED(F)
=> !REPLAY_AUTHORITY(F)

FRAGMENT_UNKNOWN(F)
=> EVIDENCE_REQUIRED(F)
&& !REPLAY_AUTHORITY(F)

DURABLE_OWNER(L)=F
=> COMPLETION_RECEIPT(F)
&& L IN MASK(F)

RESTORE
=> durable exact fragment evidence
   + durable owner provenance
   dominate stale checkpoint state

RETIRE
=> ALL_4_FRAGMENTS == COMMITTED
&& COMPLETION_RECEIPT_BITMAP == 1111
```

## Exact-head CI

All registered pull-request workflows on the exact content head passed:

```text
v0.30 main run: 31682249200                     PASS
  deterministic job: 94390124242                PASS
  formal job:        94390124320                PASS
  v0.29 deterministic/canonical regression      PASS
  v0.29 bounded safety regression                PASS

Core RTL Smoke: 31682249314                      PASS
Validate Examples: 31682249263                   PASS
```

## Evidence

Executable artifact:

```text
ID: 9173931194
SHA256:
75f19dcc94d3564e0d98d22cfd9216d71a962856f91c7b4f44a3acad765a3553
```

Formal artifact:

```text
ID: 9174077812
SHA256:
179270f31180cfec524166c3f118ef1ca48b7567b3c9605307f6021de0489156
```

Formal hashes:

```text
formal input:
0fd1c9f178b41676792fc0552f7147b0877562e4c797a097a80eba3b4d0fb1da

safety log:
94223361fdb329097a0c49bbac1b7296fedebee884f7629c47dd8633c51ac84f

cover log:
ad82448766692d0f7ac886f576c7536b7617787161e0d22c66ec269aba13af63

v0.29 regression log:
45f919f39ac0a3171aeb1715f14a34f774949d16f43659877643b1a08b3c45f7
```

Pinned formal toolchain:

```text
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33
Z3 4.8.12
```

## Claim boundary

This verifies a **bounded reduced-width one-command, four-fragment, four-byte-lane model with fixed overlapping masks and durable visible-owner provenance**.

It does not claim production PCIe/CXL/NoC semantics, arbitrary addresses or masks, payload-value correctness, byte tearing, cache/coherence/IOMMU behavior, multiple concurrent transactions, arbitrary overlap graphs, atomic persistence implementation, evidence authenticity, liveness/fairness, production widths or unbounded correctness.

## Research significance

v0.29 established recovery authority for a partially completed ordered transaction. v0.30 moves beyond a single committed frontier: the set of committed effects and the set of currently visible byte owners can now differ. Recovery therefore requires preserving both **irrevocable effect history** and **current overlap provenance**.

The next natural boundary is multiple concurrent DMA transactions / queue ordering, where overlap authority must also distinguish which transaction owns each effect and how inter-transaction ordering survives recovery.