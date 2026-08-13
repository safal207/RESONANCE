# RESONANCE Verified Report #037

# CaPU v0.32 — Queue-Epoch Slot Reuse / Cross-Epoch ABA Protection

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#86`  
**Verified CaPU content head:** `a3f1336825f245166e042fb14ed0f7184789a8e8`  
**Base verified head (v0.31):** `bd3786a8a63912d34686d0ec87363caf85d60efc`  
**Workflow:** `CaPU vCML Queue-Epoch Slot Reuse v0.32`  
**GitHub Actions run:** `31691123695`

## Result

# **PASS — bounded queue-epoch slot reuse / cross-epoch ABA protection verified**

v0.32 extends verified v0.31 from non-reusable transaction slots inside one modeled queue epoch to a bounded one-slot lifecycle in which the same numeric slot is reclaimed and reused across exact successor queue epochs.

The attack is deliberately adversarial: the reused transaction may carry the same numeric command, execution and effect IDs as the retired transaction. Only `queue_epoch` distinguishes the authority domain.

```text
epoch E   : slot 0 -> transaction A -> retire
epoch E+1 : slot 0 -> transaction B

late evidence from E
+ same numeric slot
+ same command / execution / effect IDs
=> MUST NOT mutate transaction B
```

The verified authority identity is therefore:

```text
queue_epoch
+ slot
+ command_id
+ execution_epoch
+ effect_id
= exact transaction authority identity
```

## Verified causal path

```text
epoch 2 submit
→ stale checkpoint captured
→ issue / commit / retire epoch 2
→ same-epoch slot reuse rejected
→ exact successor epoch 3 reuse accepted
→ epoch 3 issue -> UNKNOWN
→ late epoch-2 completion evidence arrives
→ rejected + quarantined
→ no epoch-3 authority mutation
→ recovery
→ stale epoch-2 checkpoint restore
→ durable epoch-3 slot + issue witness dominate stale checkpoint
→ exact epoch-3 NOT_COMMITTED evidence
→ safe replay
→ exact epoch-3 COMMITTED evidence
→ retire epoch 3
→ exact-successor reuse continues through bounded namespace
→ attempted epoch wrap rejected fail-closed
```

Deterministic marker:

```text
CAPU_VCML_QUEUE_EPOCH_SLOT_REUSE_V32_PASS
```

## Exact-head CI

All required pull-request workflows passed on the same content head `a3f1336825f245166e042fb14ed0f7184789a8e8`.

```text
CaPU vCML Queue-Epoch Slot Reuse v0.32
run 31691123695                     PASS
├ deterministic job 94418442925    PASS
└ formal job        94418442982    PASS

CaPU Core v0 RTL Smoke
run 31691123726                     PASS
├ smoke job          94418443277   PASS
└ bounded STORE      94418541790   PASS

Validate Examples
run 31691123656                     PASS
└ validation job     94418442653   PASS
```

GitHub Actions PR merge ref:

```text
b7ad892acdd41e2bf7b11c1cf9baf47f23cad65a
```

## Canonical checkpoint commitment

Canonical digest:

```text
177223eea1fc5915e80667531b40f4f134a4493b05667e39defbd3c52a3873c1
```

Verified mutation / consistency checks include:

```text
queue_epoch_change_digest_changed=1
retired_epoch_change_digest_changed=1
checkpoint_epoch_change_digest_changed=1
durable_identity_change_digest_changed=1
issue_receipt_change_digest_changed=1
stale_evidence_quarantine_digest_changed=1
same_epoch_slot_reuse_rejected=1
skipped_epoch_slot_reuse_rejected=1
unknown_without_issue_receipt_rejected=1
committed_without_completion_receipt_rejected=1
future_checkpoint_epoch_rejected=1
stale_checkpoint_predates_reused_slot_preserved=1
```

## Executable evidence

```text
artifact: capu-vcml-v32-queue-epoch-slot-evidence
artifact ID: 9177420960
ZIP SHA256:
a0de73e3a83dec8450f3f5eb7a16ab341f1bd85bbc7bc6599d80f7899dd61946
```

Sealed hashes:

```text
RTL:
6edbba22ecde859836ac024c5c59d3249afcf16232854685ca69a447b43f246d

TB:
ffe58ba0eccd95fada1a5f3bbd4867383b3a78419344632ab7039e0b72c60171

canonical encoder:
d3e26cfe8d0d2128955eb710bc69796e9e97d8589d65b8af9916fc03cc4f4199

canonical test:
5113fb3d0738b6d52a90c4ff12146c69af7beded65c3ee06ff297b1da827fe03

trajectory log:
3634200a0d166088843f88038f6d1be5d1617de9b1c56576a42efef63f68748e

canonical Python log:
0339e7409ec9b08bf2226ea508a4946c4c6b0dcf983c057a3eec42a050d306dc

v0.31 deterministic regression log:
0607d7e316e7f794edf5ea6d9b5cc34a474ec28df6e34ca54038d011fd8aa5da

v0.31 canonical regression log:
5440e55cf4227405c5c7f76073d4b4a5d9ebb3769f11d9bc9da8e823e78eaa3f
```

## Formal evidence

Proof method: **bounded model checking**.

```text
schema:
capu.hardware.queue-epoch-slot-reuse-formal-proof.v0.32

slot count: 1
formal identity width: 2 bits
exact successor epoch reuse: true
epoch wrap policy: fail-closed

safety depth: 14
DONE (PASS, rc=0)

cover depth: 28
DONE (PASS, rc=0)
VCD witnesses: 8

v0.31 bounded-safety regression: PASS
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
acb04bca813dbea2d52e1dafc31c80b29aaa84b45911a80c22b8dcebdb4e53c7

safety log:
36b7a222e173ed4d70efb922661d6b9709c1170a26450f58398b775127116454

cover log:
03882adcb519fd757da7cf6e1513e7fec630a36089bc490e609dd4a2da2374ce

v0.31 regression log:
d0be005b4dcf3cd489c94ae975b45e31af16fae91921fcdec9c6c049abbf2bbb
```

Formal artifact:

```text
artifact: capu-vcml-v32-queue-epoch-slot-formal-evidence
artifact ID: 9177465671
ZIP SHA256:
bc32595403c668ca34f276e052306d85ef9f7e7d8787971753637ee373700b01
```

## Verified bounded invariants

```text
SLOT_REUSE_ACCEPT
&& LAST_RETIRED_VALID
=> NEW_QUEUE_EPOCH == LAST_RETIRED_QUEUE_EPOCH + 1
&& NO_EPOCH_WRAP

CURRENT_SLOT_VALID
=> LIVE_IDENTITY == DURABLE_CURRENT_IDENTITY

OLD_EPOCH_EVIDENCE
&& CURRENT_SLOT_VALID
=> REJECT
&& NO_CURRENT_EFFECT_AUTHORITY_MUTATION

STALE_CHECKPOINT_PREDATING_CURRENT_EPOCH
&& DURABLE_CURRENT_SLOT_VALID
=> DURABLE_CURRENT_SLOT_WINS

RETIRED_SLOT
=> STALE_CHECKPOINT_CANNOT_RESURRECT_PENDING_SLOT

QUEUE_EPOCH_EXHAUSTED
=> NO_NEW_SLOT_AUTHORITY
```

## Verification history

The verification loop exposed three useful non-semantic issues before closure:

1. The first executable run reached the canonical test but Python could not import the repository `tools` package when launched from `tests/`; only the test harness import path was corrected.
2. The first SBY attempt used repository-relative source paths after SBY had already copied those files into its local `src` directory; only SBY source paths were corrected.
3. The first real Z3 solve found a step-5 counterexample to an over-strong formal assertion `UNISSUED => no durable receipts`. Recovery intentionally clears volatile `effect_state` while preserving durable receipts, so the assertion was correctly scoped to a live runtime. **RTL did not change for this formal correction.**

The final exact head then passed deterministic/canonical checks, v0.31 deterministic/canonical regressions, v0.32 bounded safety and reachability, v0.31 bounded-safety regression, Core RTL Smoke and Validate Examples.

## Claim boundary

This is a **bounded reduced-width one-slot lifecycle model**. Within scope it verifies exact-successor queue-epoch reuse, stale prior-epoch evidence rejection/quarantine despite reused numeric transaction identifiers, stale-checkpoint dominance by the current durable slot, retirement-history preservation and fail-closed queue-epoch exhaustion.

It does **not** prove queue-epoch wrap safety, arbitrary queue depth, multiple reusable slots, asynchronous free lists, persistent monotonic epochs across real power loss, cancellation, arbitrary transaction reordering, arbitrary overlap graphs, production PCIe/CXL/NoC transport, payload-value semantics, byte tearing, IOMMU/cache/coherence, evidence authenticity, production widths, liveness/fairness or unbounded correctness.

## Why this matters

v0.31 established that fragment evidence and transaction-slot identity are distinct authority objects. v0.32 adds the lifecycle consequence: **slot reuse itself must be causally namespaced**. A numeric slot becoming free does not authorize evidence from its former occupant to act on its successor.

The research chain now advances from durable transaction-slot identity to cross-epoch slot lifecycle authority without hiding the next boundary: the bounded queue epoch itself does not wrap. That unresolved wrap boundary remains explicit rather than being silently treated as globally unique.
