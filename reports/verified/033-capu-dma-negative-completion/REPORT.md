# RESONANCE Verified Report #033

# CaPU v0.28 — Durable Negative Completion Evidence / UNKNOWN Convergence

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#82`  
**Verified CaPU content head:** `3c07bc65df07112f43e361bb7864c33f79d3bbe8`  
**Workflow:** `CaPU vCML Durable Negative Completion Evidence v0.28`  
**GitHub Actions run:** `31669541370`

## Result

# **PASS — bounded durable negative-completion convergence verified**

CaPU v0.28 extends the v0.27 accelerator recovery model from fail-closed uncertainty into bounded convergence after exact evidence proves that an issued DMA effect did **not** commit.

v0.27 correctly preserved `UNKNOWN` across recovery, but an exact `NOT_COMMITTED` resolution could be lost by a later crash if the negative result itself was not durable. v0.28 introduces a durable negative completion receipt bound to the exact command, execution epoch and effect identity.

```text
DMA issue
  ↓
UNKNOWN
  ↓
exact NOT_COMMITTED evidence
  ↓
durable negative receipt
  ↓
recovery
  ↓
stale UNKNOWN checkpoint
  ↓
matching negative receipt wins
  ↓
NOT_COMMITTED reconstructed
  ↓
replay authority may reopen
```

The model also prevents that negative evidence from becoming reusable authority for a later attempt. On the next accepted DMA issue the matching negative receipt is consumed and a fresh issue witness is created atomically; the new attempt becomes `UNKNOWN` and the old negative evidence can no longer authorize replay.

## Verified exact-head closure

All pull-request workflows registered on exact content head `3c07bc65df07112f43e361bb7864c33f79d3bbe8` completed successfully:

- v0.28 run `31669541370` — PASS
  - deterministic job `94351142078` — PASS
  - formal job `94351141973` — PASS
  - v0.27 deterministic/canonical regression — PASS
  - v0.27 bounded-safety regression — PASS
- Core RTL Smoke run `31669541338` — PASS
  - deterministic STORE smoke `94351141787` — PASS
  - bounded STORE proof `94351315029` — PASS
- Validate Examples run `31669541359` / job `94351141924` — PASS

## Deterministic evidence

The executable trajectory reached and checked:

```text
command_submit accepted=1 command=7 execution_epoch=4 effect=10
pre_issue_checkpoint captured=1 completion=NOT_COMMITTED dma_issued=0
dma_issue accepted=1 completion=UNKNOWN durable_issue_witness=1
stale_unknown_restore completion=UNKNOWN replay_authority=0 durable_issue_witness=1
exact_negative_evidence accepted=1 durable_negative_receipt=1 completion=NOT_COMMITTED replay_authority=1
post_negative_recovery durable_negative_receipt_preserved=1 runtime_closed=1
stale_unknown_restore negative_receipt_wins=1 completion=NOT_COMMITTED replay_authority=1
retry_issue accepted=1 negative_receipt_consumed=1 fresh_issue_witness=1 completion=UNKNOWN
fresh_attempt_restore old_negative_cannot_authorize=1 completion=UNKNOWN replay_authority=0
exact_committed_evidence accepted=1 durable_completion_receipt=1 effect_spent=1 replay_authority=0
command_retire accepted=1 completion=COMMITTED
CAPU_VCML_DMA_NEGATIVE_COMPLETION_V28_PASS
```

## Canonical checkpoint binding

Canonical v0.28 digest:

```text
5f47a4548f17f685c74fc50676b743a54c519946d929d218eaadbf1a3e157457
```

The canonical payload binds the verified v0.27 digest plus live/checkpoint completion state and the modeled issue, negative-completion and committed-completion evidence records.

Mutation checks PASS:

```text
durable_negative_to_unknown_mixed_state_rejected=1
foreign_negative_receipt_mixed_state_rejected=1
stale_negative_plus_fresh_issue_mixed_state_rejected=1
```

## Executable artifact

```text
name: capu-vcml-v28-dma-negative-evidence
artifact ID: 9169299763
ZIP SHA256: 53eb879b0b8ba06cc49bad0ee6e92d3ffb92ed17089dd1221f62040de3ea682f
```

Sealed hashes:

```text
RTL: 05172b6e37a655b29cb9cf88619c5b12592138e4043bce0411fa781dc54787ba
TB: 5c89b1198a5b95f8983381469d79e82233f5c6522100a153796787c3781948ab
canonical encoder: 6f9965db696f303639ed7066cadb1fd597a9c06e3c8570481d50121da3661979
canonical test: cf0218ba314b4c22a6f661735dc9df4a0be89b132608d3480ab679a828c95317
trajectory log: 242f944cd98a93cade22f4c7f27ac2a1e4d19963e6cbc687ef288b81fc34caad
canonical Python log: 51562d7d4870f14cc1f7e7c79f8b2a641b9cbc8335409d8843ce6b6da0de0d8b
v0.27 deterministic regression: 00118a5c6c4b40b1cec5b92a8ecbce7ee81cb4166e0a3f205d81b3a82af3ff17
v0.27 canonical regression: acc18a6d0fc6f833c38d8b75caebc2c4ef9a36c405440fc8d564b26c49d6501f
```

## Formal evidence

v0.28 deliberately uses **bounded model checking**, not an inductive or unbounded correctness claim.

```text
schema: capu.hardware.dma-negative-completion-formal-proof.v0.28
proof method: bounded model checking
formal identity width: 2 bits
safety depth: 18
safety: DONE (PASS, rc=0)
cover depth: 28
cover: DONE (PASS, rc=0)
VCD witnesses: 9
v0.27 bounded safety regression: PASS
```

Pinned toolchain:

```text
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input: 26fccc1dc3578f04edd2ac7ed9ba704c4da6b1a314ceeca74a258e992ff4d110
safety log: 4ebcf6b4c1ef0e95622642f658a6278a606ff79444f05db380ffd77efaa20dc8
cover log: 397340b7421909260aab3bad5414226f89d8a69021685e5cac4127d147a565c1
v0.27 regression log: f1bdd20e9df834123df8bae3862db57f67d3797d314eacb02049847a29621e68
```

Formal artifact:

```text
name: capu-vcml-v28-dma-negative-formal-evidence
artifact ID: 9169218324
ZIP SHA256: 37573836cdb39fea1aacc75fc72a3892069de67922b957f0d3bca8de94b7cb03
```

## Verified bounded invariants

```text
UNKNOWN
=> NO_REPLAY
&& NO_RETIRE

EXACT_EVIDENCE(NOT_COMMITTED)
=> DURABLE_NEGATIVE_RECEIPT
&& NOT_COMMITTED
&& ISSUE_WITNESS_CONSUMED

RECOVERY
=> NEGATIVE_RECEIPT_PRESERVED

RESTORE(stale UNKNOWN + matching negative receipt)
=> NOT_COMMITTED
&& !EVIDENCE_REQUIRED
&& REPLAY_MAY_REOPEN_IF_NO_NEW_BARRIER

DMA_RETRY_ACCEPT
=> NEGATIVE_RECEIPT_CONSUMED
&& FRESH_ISSUE_WITNESS
&& UNKNOWN

FRESH_UNKNOWN_ATTEMPT
=> OLD_NEGATIVE_EVIDENCE_CANNOT_AUTHORIZE_REPLAY

MATCHING_COMMITTED_RECEIPT
=> COMMITTED_PRECEDENCE
```

## Claim boundary

This is a **bounded reduced-width one-command / one-DMA-effect durable negative-completion convergence model** layered on verified v0.27.

The model treats issue, negative-completion and committed-completion receipts as authoritative durable evidence and assumes that consuming the matching negative receipt and creating the next issue witness is atomic inside the modeled persistence authority.

It does **not** prove how real accelerator hardware obtains trustworthy negative completion evidence; physical durability or authenticity of receipts; split or non-atomic persistence domains; multiple outstanding commands/effects; PCIe/CXL/NoC transport; IOMMU/cache/coherence; partial or multi-beat DMA visibility; queue ordering; completion interrupts; liveness when discriminating evidence never becomes available; production widths; or unbounded correctness.

## Research implication

v0.27 established the safe epistemic rule:

```text
UNKNOWN ≠ NOT_COMMITTED
```

v0.28 adds the complementary persistence rule:

```text
PROVEN_NOT_COMMITTED
+ durable exact evidence
> stale UNKNOWN checkpoint
```

That turns a purely fail-closed recovery state into a bounded evidence-driven convergence path without allowing old negative evidence to authorize a fresh in-flight attempt.
