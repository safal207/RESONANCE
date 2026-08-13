# RESONANCE Verified Report #036

# CaPU v0.31 — Concurrent DMA Queue Ordering Recovery Authority

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#85`  
**Verified CaPU content head:** `bd3786a8a63912d34686d0ec87363caf85d60efc`  
**Base verified head (v0.30):** `f2a70b31393e52f0fbb4f43dd14739c96a8a8bd0`  
**Workflow:** `CaPU vCML Concurrent DMA Queue Recovery v0.31`  
**GitHub Actions run:** `31688676864`

## Result

# **PASS — bounded concurrent DMA queue recovery authority verified**

v0.31 extends the v0.30 overlapping-fragment model from one DMA transaction to two concurrent transactions under one modeled queue epoch.

```text
TX0 (older) -> TX1 (younger)

TX0.F0 -> lanes 0,1
TX0.F1 -> lane 2
TX1.F0 -> lane 3          # non-overlap may progress early
TX1.F1 -> lanes 1,2       # overlap waits for older effects
```

The central distinction is now:

```text
visible-owner provenance
!=
queue-overtake authority
```

A younger non-overlapping fragment may make progress while the older transaction is unresolved, but a younger overlapping fragment cannot acquire issue authority until the older overlapping effects have committed. Retirement remains ordered.

Formal verification also exposed a second independent authority dimension:

```text
fragment evidence
!=
transaction-slot existence / identity
```

A stale checkpoint may predate TX1. If durable TX1 fragment/owner evidence survives, recovery must not erase the younger transaction slot and make it reusable. v0.31 therefore models a durable non-reusable transaction-slot identity within the queue epoch.

## Verified recovery path

```text
pre_tx1_checkpoint tx_pending=01 younger_slot_absent=1
queue_submit tx0=1 tx1=1 queue_epoch=3 order=TX0_before_TX1 durable_slots=11
younger_nonoverlap_commit tx1_f0=COMMITTED older_tx0_f0=UNKNOWN lane3_owner=TX1_F0 concurrent_safe=1
stale_pre_tx1_restore durable_tx1_slot_wins=1 tx_pending=11 tx1_identity_preserved=1 fragment_evidence_preserved=1
stale_slot_resubmit rejected=1 durable_slot_identity=1 completion_evidence_preserved=1
younger_overlap_blocked tx1_f1=1 older_overlap_unresolved=1 no_issue_authority=1
older_overlap_resolved tx0_completion=11 tx1_f1_queue_blocked=0
queue_restore exact_tx_slots=1 younger_nonoverlap_commit_preserved=1 overlap_unknown_preserved=1 owner_provenance_preserved=1
younger_retire_before_older rejected=1 queue_order_preserved=1
ordered_retire tx0_then_tx1=1 retired_bitmap=11
CAPU_VCML_CONCURRENT_DMA_QUEUE_RECOVERY_V31_PASS
```

## Canonical checkpoint authority

```text
canonical digest:
b9f2a008513d6676e3c279f49ae25c4fb189f452672d6fee608face6318e729c
```

Canonical mutation checks reject transaction-slot swaps, younger retirement before older, owner provenance without committed fragments, younger overlap authority before older completion, fragment evidence without a historical durable slot, durable-slot identity mismatch, and stale-checkpoint erasure of a younger slot.

## Formal result

The v0.31 proof is explicitly **bounded model checking**, not an unbounded or inductive correctness claim.

```text
transactions: 2
fragments per transaction: 2
byte lanes: 4
formal identity width: 2 bits
safety depth: 12 — PASS
cover depth: 24 — PASS
VCD witnesses: 11
v0.30 bounded safety regression: PASS
```

Key bounded invariants:

```text
TX1_NONOVERLAP_FRAGMENT
=> MAY_PROGRESS_WHILE_TX0_UNRESOLVED

TX1_OVERLAP_FRAGMENT
&& OLDER_OVERLAPPING_EFFECTS_NOT_COMMITTED
=> NO_ISSUE_AUTHORITY

TX1_RETIRE
=> TX0_RETIRED
&& TX1_FRAGMENTS_FULLY_COMMITTED

HISTORICALLY_ACCEPTED_TX_SLOT
=> NON_REUSABLE_WITHIN_MODELED_QUEUE_EPOCH

RESTORE(STALE_CHECKPOINT_PREDATING_TX1)
=> TX1_IDENTITY_RECONSTRUCTED
&& TX1_FRAGMENT_EVIDENCE_PRESERVED
&& TX1_SLOT_NOT_RESUBMITTABLE
```

## Exact-head CI

```text
v0.31 main run: 31688676864                     PASS
  deterministic job: 94410690842                PASS
  formal job:        94410690643                PASS
  v0.30 deterministic/canonical regression      PASS
  v0.30 bounded safety regression                PASS

Core RTL Smoke: 31688676858                      PASS
  deterministic smoke: 94410690856              PASS
  bounded STORE proof: 94410776111               PASS

Validate Examples: 31688676837                   PASS
  validation job: 94410692160                    PASS
```

GitHub Actions checked PR merge ref `1dee90e38415c60f7322fca8f5e40a5dfb71e07b` for exact content head `bd3786a8...`.

## Evidence

Executable artifact:

```text
ID: 9176458080
SHA256:
67dcc03dd73dd1a9d4e32ca72ed5fcebf59df7f61a4081992253c6cea5b6665e
```

Formal artifact:

```text
ID: 9176549963
SHA256:
bda40b43be684a48a24bb0225ed73a346bdc663199a665706d04a0f6d5a76ff7
```

Formal hashes:

```text
formal input:
ca1b45d637f6815e8745d25997fcfd0f542152084457d0c57fb0d3bfd87aa6e8

safety log:
421cce2fe45bbcacd53811067d961fa3fbe049d3c89c75cb44d5dcdcf6d44b81

cover log:
92a1ea104e729c3bd4541f3fbdd458c397204d59aed46e80871162e929a2cd0f

v0.30 regression log:
ef2d732993402afe7011e422a5028a00cc78604ac4eea5356d473abe40d11eb0
```

Pinned formal toolchain:

```text
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (2584903a060)
Z3 4.8.12
```

## Verification history

Formal development produced useful evidence before the final PASS:

1. an early overlap-gate elaboration issue was corrected without a solver counterexample;
2. a genuine bounded counterexample exposed transaction-slot identity resurrection after a stale checkpoint predating TX1, leading to durable non-reusable slot authority;
3. a later exact-head formal failure was a harness observability bug: hierarchical references to DUT-local durable registers became implicit undriven wires in Yosys;
4. the final formal harness replaced those hierarchical observations with a formal-side ghost ledger derived only from externally accepted transaction submissions. No RTL, deterministic trajectory, canonical encoding, queue semantics or recovery semantics changed in that final fix.

## Claim boundary

This verifies a **bounded reduced-width two-transaction, two-fragments-per-transaction, four-byte-lane, one-queue-epoch model with fixed overlap and non-reusable durable transaction slots within that epoch**.

It does not claim arbitrary queue depth, slot reuse across epochs, cancellation, arbitrary transaction reordering, arbitrary overlap graphs, production PCIe/CXL/NoC transport, payload-value semantics, byte tearing, IOMMU/cache/coherence, production persistence, evidence authenticity, production widths, liveness/fairness or unbounded correctness.

## Research significance

v0.30 separated irrevocable fragment history from current visible-owner provenance. v0.31 adds inter-transaction ordering and proves that transaction identity itself is an authority object: durable fragment evidence is unsafe if recovery can forget which transaction slot that evidence belongs to and later reuse the slot.

The next natural boundary is **queue-epoch / slot-reuse lifecycle authority**: safely reclaiming finite transaction slots without allowing stale evidence from an earlier occupant to reacquire authority.