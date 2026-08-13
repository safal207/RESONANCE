# RESONANCE Verified Report #038

# CaPU v0.33 — Queue-Epoch Wrap / Authority Incarnation

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#87`  
**Verified CaPU content head:** `f9d3832d84dc2415617a782cb226af83943b5ecd`  
**Base verified head (v0.32):** `a3f1336825f245166e042fb14ed0f7184789a8e8`  
**Primary workflow:** `CaPU vCML Queue-Epoch Wrap Incarnation v0.33`  
**Primary run:** `31705641935`  
**Sealed evidence run:** `31705641770`

## Result

# **PASS — bounded queue-epoch wrap / authority-incarnation protection verified**

v0.33 extends verified v0.32 beyond fail-closed numeric queue-epoch exhaustion. The bounded model now permits a queue epoch to wrap from `MAX` to `0`, but only by advancing an explicit authority incarnation.

The adversarial case deliberately repeats the numeric queue epoch and transaction IDs:

```text
historical: (incarnation=1, queue_epoch=0)
...
retired:    (incarnation=1, queue_epoch=MAX)
current:    (incarnation=2, queue_epoch=0)
```

An ancient completion message from `(1,0)` therefore looks numerically adjacent to the current `(2,0)` transaction except for the incarnation discriminator. It is rejected and quarantined; it cannot mutate current effect authority.

## Authority identity

```text
incarnation
+ queue_epoch
+ slot
+ command_id
+ execution_epoch
+ effect_id
= exact transaction authority identity
```

The bounded successor rule is:

```text
retired_epoch < MAX
=> same incarnation, epoch + 1

retired_epoch == MAX && retired_incarnation < MAX
=> incarnation + 1, epoch = 0

retired_epoch == MAX && retired_incarnation == MAX
=> fail closed; no new slot authority
```

Incarnation itself does not wrap in v0.33.

## Deterministic evidence

The final exact-head trajectory produced:

```text
inc1_epoch0_checkpoint pending=1 incarnation=1 epoch=0 state=UNISSUED
wrap_reuse current_incarnation=2 epoch=0 same_numeric_epoch_as_history=1 incarnation_discriminator=1
ancient_same_epoch_evidence quarantined=1 old_incarnation=1 current_incarnation=2 epoch=0 no_authority_mutation=1
stale_pre_wrap_checkpoint current_incarnation=2 epoch=0 unknown_preserved=1 durable_identity_wins=1
incarnation_namespace_exhausted last_incarnation=3 last_epoch=3 wrap_to_incarnation0_epoch0_blocked=1 fail_closed=1
CAPU_VCML_QUEUE_EPOCH_WRAP_INCARNATION_V33_PASS
```

The trajectory also re-ran the complete v0.32 executable and canonical path successfully.

## Canonical checkpoint binding

Canonical digest:

```text
b2a12198076c7b58ef193648bababa2d64a24b80db6581c0849481ab611634ca
```

Mutation and consistency checks passed for live, durable, retired and checkpoint incarnation fields, queue epoch, stale-evidence quarantine state, exact wrap successor acceptance, same-incarnation numeric-wrap rejection, skipped-incarnation rejection and bounded incarnation exhaustion.

Representative results:

```text
live_incarnation_change_digest_changed=1
durable_incarnation_change_digest_changed=1
retired_incarnation_change_digest_changed=1
checkpoint_incarnation_change_digest_changed=1
wrap_without_incarnation_increment_rejected=1
wrap_with_skipped_incarnation_rejected=1
exact_wrap_successor_accepted=1
same_incarnation_numeric_wrap_rejected=1
skipped_incarnation_wrap_rejected=1
incarnation_exhaustion_fail_closed=1
stale_same_epoch_foreign_incarnation_checkpoint_preserved=1
VCML_QUEUE_EPOCH_WRAP_CHECKPOINT_V33_PASS
```

## Exact-head CI

Verified content head:

```text
f9d3832d84dc2415617a782cb226af83943b5ecd
```

GitHub Actions checked PR merge ref:

```text
43220a1f5587d7b276537d2914f3bde095f6361e
```

All exact-head pull-request workflows were green:

- `CaPU vCML Queue-Epoch Wrap Incarnation v0.33` — run `31705641935` — PASS
  - deterministic job `94465382435` — PASS
  - formal job `94465382553` — PASS
- `CaPU vCML Queue-Epoch Wrap Evidence v0.33` — run `31705641770` — PASS
  - evidence job `94465382308` — PASS
- `CaPU Core v0 RTL Smoke` — run `31705641812` — PASS
  - deterministic smoke job `94465391993` — PASS
  - bounded STORE proof job `94465534308` — PASS
- `Validate Examples` — run `31705641746` — PASS
  - validation job `94465381660` — PASS
- v0.32 executable/canonical regression — PASS
- v0.32 bounded-safety regression — PASS

## Formal evidence

Schema:

```text
capu.hardware.queue-epoch-wrap-incarnation-formal-proof.v0.33
```

Result:

```text
proof method: bounded model checking
formal identity width: 2 bits
slot count: 1
safety depth: 24 — PASS
cover depth: 44 — PASS
VCD witnesses: 4
queue-epoch wrap requires incarnation increment: true
incarnation wrap policy: fail-closed
v0.32 bounded-safety regression: PASS
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
1056503e0fe76ebb432e859d41157e393c51652f53a6da09e168123b8ab7edbf

safety log SHA256:
499aa048dfedad377311e189883999bc77fad697401d7cae86f488a935baae03

cover log SHA256:
8046f95526d80e4d906eed0121fdce4b14b070f662b17e640244d129a4f63d79

v0.32 regression log SHA256:
4e9f79ab33ce5f22390f56f036f388e7457e440bf64a3dec26dbb379df7f1645
```

## Sealed artifacts

Executable evidence:

```text
artifact: capu-vcml-v33-queue-epoch-wrap-evidence
artifact ID: 9183052862
ZIP SHA256:
ef9a09e4412d6dd20088338f5345e3c1df53e6407f745aec75ba6a25ce9b026d
```

Formal evidence:

```text
artifact: capu-vcml-v33-queue-epoch-wrap-formal-evidence
artifact ID: 9183088442
ZIP SHA256:
c14527a9392abae54457f1ee8cb97c968f24be53bf0de42e32c0b3e7d2a35490
```

## Verified bounded invariants

```text
NON_WRAP_SUCCESSOR
=> SAME_INCARNATION && EPOCH_PLUS_ONE

EPOCH_WRAP_SUCCESSOR
=> INCARNATION_PLUS_ONE && EPOCH_ZERO

SAME_NUMERIC_EPOCH && FOREIGN_INCARNATION
=> NO_RESOLUTION_AUTHORITY

STALE_PRE_WRAP_CHECKPOINT
&& DURABLE_POST_WRAP_SLOT
=> DURABLE_POST_WRAP_IDENTITY_WINS

RECOVERY
=> DURABLE_INCARNATION_AND_EPOCH_PRESERVED

INCARNATION_EXHAUSTED
=> NO_NEW_SLOT_AUTHORITY
```

## Verification history

The first implementation passed its deterministic v0.33 trajectory, canonical tests and v0.32 executable regressions. The first real Z3 run then exposed an over-broad quarantine-ledger assertion across the recovery boundary: a combinational stale-evidence condition could be observable while recovery had priority, even though no live-runtime ledger event was committed.

The final formal surface therefore proves the actual v0.33 delta: live-runtime wrap/incarnation authority, stale prior-incarnation rejection, durable incarnation/epoch preservation across recovery and fail-closed incarnation exhaustion. The complete effect/recovery state machine remains guarded by the mandatory verified v0.32 bounded regression. Superseded first-pass formal files were removed before the final exact-head run.

This distinction matters: v0.33 does **not** claim that recovery-time external inputs are accepted quarantine-ledger events. It claims that those inputs have no resolution authority, while live-runtime stale evidence is rejected/quarantined under the bounded identity model.

## Claim boundary

This is a **bounded reduced-width one-slot lifecycle model**. Within scope it verifies numeric queue-epoch wrap through an explicit bounded authority-incarnation discriminator, rejects live-runtime prior-incarnation evidence even when the numeric epoch and transaction IDs repeat, preserves current durable post-wrap identity across stale-checkpoint recovery, and fails closed when the bounded incarnation namespace is exhausted.

It does **not** prove:

- incarnation wrap safety;
- globally unique identifiers forever;
- persistent monotonic incarnation storage across real power loss;
- cryptographic anti-replay;
- arbitrary queue depth or multiple reusable slots;
- asynchronous free lists;
- production PCIe/CXL/NoC transport;
- IOMMU/cache/coherence semantics;
- evidence authenticity;
- liveness or fairness;
- production widths;
- unbounded correctness.

CaPU PR #87 remains draft and unmerged at publication time.
