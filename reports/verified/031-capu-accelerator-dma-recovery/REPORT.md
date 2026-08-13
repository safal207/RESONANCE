# RESONANCE Verified Report #031

# CaPU v0.26 — Accelerator Command / DMA Recovery Authority

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#79`  
**Verified CaPU content head:** `ee9e1291c190d9aba0c7f6f389d25f82035b7b80`  
**Workflow:** `CaPU vCML Accelerator DMA Recovery v0.26`  
**GitHub Actions run:** `31661107793`

## Result

# **PASS — bounded accelerator DMA recovery authority verified**

CaPU v0.26 is the first explicit AI-accelerator execution/recovery layer above the previously verified CPU/MMU trust chain. It models one accelerator command and one externally committed DMA effect, asking whether recovery of an older pre-effect checkpoint can accidentally recreate authority to execute an already-committed effect a second time.

The bounded result is fail-closed: a separate modeled durable effect receipt takes precedence over a stale checkpoint for external-effect reconciliation. If the restored checkpoint says `effect_spent=0` while a matching receipt says the effect already committed, the command enters `RECONCILE_REQUIRED`; DMA replay authority remains closed. Exact reconciliation marks the effect spent, after which the command may retire but the same effect cannot re-execute.

```text
command submit
  ↓
pre-effect checkpoint
  ↓
authorized DMA issue
  ↓
external DMA effect commit
  ↓
durable effect receipt
  ↓
recovery
  ↓
stale checkpoint restore
  ↓
receipt/checkpoint conflict
  ↓
RECONCILE_REQUIRED
  ↓
no DMA replay authority
  ↓
exact reconcile: effect_spent=1
  ↓
retire command
```

## Exact-head verification

All PR workflows registered on exact head `ee9e1291c190d9aba0c7f6f389d25f82035b7b80` passed:

- v0.26 run `31661107793` — PASS;
- deterministic job `94325939577` — PASS;
- formal job `94325939605` — PASS;
- Validate Examples run `31661107792` — PASS;
- Core RTL Smoke run `31661107746` — PASS;
- v0.25 deterministic/canonical regressions — PASS;
- v0.25 bounded-safety regression — PASS.

## Deterministic evidence

The exact-head executable trajectory produced:

```text
command_submit accepted=1 command=5 execution_epoch=3 effect=9
pre_effect_checkpoint captured=1 dma_issued=0 effect_spent=0
dma_issue authorized=1 command=5 effect=9
dma_effect committed=1 durable_receipt=1 effect_spent=1
duplicate_dma_commit rejected=1 exactly_once_effect=1
recovery volatile_state_cleared=1 checkpoint_preserved=1 receipt_preserved=1
stale_checkpoint_restore accepted=1 reconcile_required=1 checkpoint_effect_spent=0 durable_receipt=1
post_restore_dma_replay rejected=1 receipt_conflict_blocks_authority=1
pre_reconcile_retire rejected=1
foreign_reconcile rejected=1
exact_reconcile accepted=1 effect_spent=1 reconcile_required=0
post_reconcile_dma_replay rejected=1 spent_effect_cannot_reexecute=1
command_retire accepted=1 exactly_once_dma_effect=1
historical_command_reuse rejected=1 durable_receipt_blocks_identity_reuse=1
CAPU_VCML_ACCELERATOR_DMA_RECOVERY_V26_PASS
```

Canonical checkpoint digest:

```text
ddfdc07cde04d3f732e8f479f4fbd8edd094494734801cf7c172468626809b9d
```

The canonical mutation suite changes the commitment when live command identity, execution epoch, effect identity, DMA issued/spent state, reconciliation state, checkpoint state or durable-receipt state changes. Mixed checkpoint/receipt authority and a stale checkpoint stripped of its matching receipt fail verification under the unchanged commitment.

## Formal evidence

```text
schema: capu.hardware.accelerator-dma-recovery-formal-proof.v0.26
safety depth: 42
safety result: PASS
proof method: successful k-induction
cover depth: 56
cover result: PASS
VCD witnesses: 10
v0.25 bounded-safety regression: PASS
```

Pinned formal toolchain:

```text
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys: 0.33 (git sha1 2584903a060)
Z3: 4.8.12
```

Formal hashes:

```text
formal input SHA256:
a8ec3763f5b01b8134cc969472c39b0920732ccb0fcc6702ca7e96a856ddfc18

safety log SHA256:
108e52fc87c21361b281f3829fd25e724e716c5c49515400cbf81a248239a91b

cover log SHA256:
8e513620709eb30824176d385be377ff1f8c5c5a54d811295dfa087b7fda8eb2

v0.25 regression log SHA256:
5968cde690fe28c015020aff0e3d0c8c25b6863002ffcc3da897f018f05df75e
```

## Evidence artifacts

Executable evidence:

```text
artifact: capu-vcml-v26-accelerator-dma-evidence
artifact ID: 9166208426
ZIP SHA256:
53414914e7f05db01db8b7a9d45c8be8035a1e1be5107d2651132ba752435bdf
```

Formal evidence:

```text
artifact: capu-vcml-v26-accelerator-dma-formal-evidence
artifact ID: 9166281121
ZIP SHA256:
52ca3d0c4b92749f42ed4d4f392733958e2258c734c2e5ebea7911c74377048c
```

Sealed executable hashes:

```text
RTL:
3707e600597ad173a0da64c3dbd51bee6892a8a6d0b31060d74ffecec30cc8dc

TB:
f83ab8c4df5b7bef9224a86f0178ff32e07fa35363c286286762ebc3f1452c6c

canonical encoder:
3ca75e7784a9dff7e750e7d32792b5c48fc8e7c1f99efc10d2c0a197765b27d8

canonical test:
59c80d9c4fd79927f45bb8f365345b241b3aa5e8820c12ee15d3c058810e04e9

trajectory log:
8e48910d24336844ad0e32ef6366ef56a54004188e19682cbde21f674d93f137

canonical Python log:
a091d0fc080b55cbca0d590a71ee3da3012eb132e37239872f7edf9209c982a9
```

## Verified invariants

```text
DMA_ISSUE_ACCEPT
=> EXACT_COMMAND_EPOCH_EFFECT
&& DMA_REPLAY_AUTHORITY
&& !EFFECT_SPENT
&& !MATCHING_DURABLE_RECEIPT

DMA_COMMIT_ACCEPT
=> PRIOR_AUTHORIZED_ISSUE
&& EXACT_COMMAND_EPOCH_EFFECT
&& !PRIOR_RECEIPT

RECOVERY
=> VOLATILE_ACCELERATOR_STATE_CLEARED
&& CHECKPOINT_PRESERVED
&& DURABLE_RECEIPT_PRESERVED

RESTORE_ACCEPT
&& CHECKPOINT_EFFECT_SPENT == 0
&& MATCHING_DURABLE_RECEIPT
=> RECONCILE_REQUIRED
&& !DMA_REPLAY_AUTHORITY

RECONCILE_ACCEPT
=> EFFECT_SPENT
&& !DMA_REPLAY_AUTHORITY

DUPLICATE_DMA_COMMIT
=> REJECT

RETIRED_OR_SPENT_EFFECT
=> SAME_EFFECT_CANNOT_REEXECUTE
```

## Claim boundary

This is a **bounded reduced-width one-command / one-DMA-effect recovery-authority model** layered on verified v0.25. A durable effect receipt is modeled as authoritative evidence.

It does **not** prove the durability or authenticity of that receipt, asynchronous in-flight DMA ambiguity before receipt creation, arbitrary command queues, multiple concurrent effects, production DMA engines or message transport, accelerator firmware, IOMMU behavior, cache/coherence ordering, device-memory contents, completion interrupts, durable-media correctness, production widths, liveness/fairness or unbounded correctness.

The result is therefore an accelerator recovery **authority invariant**, not a complete accelerator or production DMA implementation.
