# RESONANCE Verified Report #032

# CaPU v0.27 — In-Flight DMA Completion Uncertainty

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#80`  
**Verified CaPU content head:** `99470d9106a4ba8e38c92e831611d2739868004e`  
**Workflow:** `CaPU vCML DMA Completion Uncertainty v0.27`  
**GitHub Actions run:** `31664439172`

## Result

# **PASS — bounded tri-state DMA completion uncertainty authority verified**

CaPU v0.27 extends the explicit AI-accelerator recovery layer from v0.26 into the harder epistemic window where a DMA command was issued but the external completion outcome is not yet known when recovery begins.

The model does not guess. An issued-but-unresolved effect becomes `UNKNOWN`, and `UNKNOWN` is treated as an authority state rather than as an approximation of `NOT_COMMITTED`.

```text
pre-issue checkpoint
  ↓
DMA issue
  ↓
UNKNOWN
  ↓
recovery before completion evidence
  ↓
stale pre-issue checkpoint restore
  ↓
matching durable issue witness
  ↓
UNKNOWN reconstructed
  ↓
NO REPLAY / NO RETIRE
  ↓
exact discriminating evidence
  ├─ NOT_COMMITTED → replay may reopen
  └─ COMMITTED     → completion receipt + effect spent
```

The key bounded result is fail-closed: restoring an older checkpoint cannot erase a surviving issue witness and silently reclassify an unresolved DMA as safe to replay. Exact `NOT_COMMITTED` evidence may reopen replay authority when no new recovery barrier is active. Exact `COMMITTED` evidence creates a modeled durable completion receipt, marks the effect spent and keeps replay authority closed. A later stale checkpoint cannot override that matching completion receipt.

## Threat model

The central failure window is:

```text
checkpoint says NOT_COMMITTED
→ DMA issue accepted
→ external device may or may not commit
→ no discriminating completion evidence yet
→ crash / recovery
→ old checkpoint restored
```

Two naive policies are unsafe:

```text
"probably not committed" → replay → possible duplicate effect
"probably committed"     → retire → possible lost effect
```

v0.27 instead requires:

```text
UNKNOWN
=> NO_DMA_REPLAY_AUTHORITY
&& NO_RETIRE_AUTHORITY
&& REQUIRE_DISCRIMINATING_EVIDENCE
```

## Modeled identity

Evidence is bound to:

```text
command_id + execution_epoch + effect_id
```

Foreign completion evidence cannot resolve the live command.

## Deterministic evidence

The exact verified trajectory produced:

```text
command_submit accepted=1 command=7 execution_epoch=4 effect=10
pre_issue_checkpoint captured=1 completion=NOT_COMMITTED dma_issued=0
dma_issue accepted=1 completion=UNKNOWN durable_issue_witness=1
unknown_live_replay rejected=1 no_guess_replay=1
unknown_live_retire rejected=1 no_guess_commit=1
recovery volatile_state_cleared=1 pre_issue_checkpoint_preserved=1 issue_witness_preserved=1
stale_checkpoint_restore accepted=1 completion=UNKNOWN evidence_required=1 replay_authority=0 retire_authority=0
post_restore_unknown_replay rejected=1 require_discriminating_evidence=1
foreign_completion_evidence rejected=1 exact_identity_required=1
exact_evidence_not_committed accepted=1 replay_authority_reopened=1
retry_issue accepted=1 completion=UNKNOWN
exact_evidence_committed accepted=1 durable_completion_receipt=1 effect_spent=1 replay_authority=0
post_commit_dma_replay rejected=1 exactly_once_effect=1
command_retire accepted=1 completion_evidence_resolved=COMMITTED
late_stale_checkpoint_restore completion_receipt_wins=1 completion=COMMITTED replay_authority=0
CAPU_VCML_DMA_COMPLETION_UNCERTAINTY_V27_PASS
```

## Canonical state binding

The v0.27 canonical SHA-256 commitment is:

```text
0e823705c97b662ea3b49c0642a336fb8db240410e8a2f50881db760ac86120f
```

It binds the verified v0.26 digest plus:

- live command identity and runtime state;
- DMA-issued state;
- tri-state completion state;
- evidence-required state;
- checkpoint identity and completion state;
- modeled durable issue witness;
- modeled durable completion receipt.

Mutation checks rejected an `UNKNOWN → replayable NOT_COMMITTED` mixed reconstruction and a foreign completion-receipt reconstruction under the unchanged commitment.

## Exact-head CI

All workflows registered on exact head `99470d9106a4ba8e38c92e831611d2739868004e` passed:

- v0.27 workflow run `31664439172` — PASS;
  - deterministic job `94335876373` — PASS;
  - formal job `94335876325` — PASS;
  - v0.26 deterministic + canonical regressions — PASS;
  - v0.26 bounded formal regression — PASS;
- Validate Examples run `31664439177` — PASS;
- Core RTL Smoke run `31664439206` — PASS.

## Executable evidence

Artifact:

```text
capu-vcml-v27-dma-completion-evidence
ID: 9167387692
ZIP SHA256:
1e8fa03a41dfb65caf7cd8c0e7e808f14b8e1ae6ab2dbb331c8ac94c7322b81c
```

Sealed hashes:

```text
RTL
3aa3d7b3384e790b42eb8620cb77ce789a678705455943c1a6e9de4b1c3bc8c8

TB
b18826f4a7b4802b3185ab00c66fbf01d293aa374909390a46f31a5486059a49

canonical encoder
1c631cd39a1835f8b9121d758b78c1fc45d7c0a8be83b082a91269ee2b49c7eb

canonical test
4936c0f2802bd1ec8ef7fd8007bc3e4b035951ea66cd45ec38e4415510aaa6ab

trajectory log
00118a5c6c4b40b1cec5b92a8ecbce7ee81cb4166e0a3f205d81b3a82af3ff17

canonical Python log
acc18a6d0fc6f833c38d8b75caebc2c4ef9a36c405440fc8d564b26c49d6501f

v0.26 deterministic regression log
8e48910d24336844ad0e32ef6366ef56a54004188e19682cbde21f674d93f137

v0.26 canonical regression log
a091d0fc080b55cbca0d590a71ee3da3012eb132e37239872f7edf9209c982a9
```

## Formal evidence

v0.27 deliberately makes a bounded claim. Its safety result is **bounded model checking**, not an inductive or unbounded proof.

```text
schema:
capu.hardware.dma-completion-uncertainty-formal-proof.v0.27

formal identity widths:
2 bits each for command ID, execution epoch and effect ID

safety method:
bounded model checking

safety depth:
16

safety result:
DONE (PASS, rc=0)

cover depth:
24

cover result:
DONE (PASS, rc=0)

VCD witnesses:
9

v0.26 bounded safety regression:
PASS
```

Pinned toolchain:

```text
SBY
b1a1e98cba941ec8433f8dc27f416cd7bb7f14be

Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Formal hashes:

```text
formal input SHA256
cca6504ed48c6cf7aafe26b558f3255597a180f4302601aaf0b13e38b3a88ff4

safety log SHA256
3531a420137329dc89ab9708dd8de95f9c49cdebcc4bb1ba3e66cfb5d54ddf6e

cover log SHA256
c88b7f0cfa2566fb8cba36a2dd600b24cc1d193cfca548c57f07688200dbc88a

v0.26 regression log SHA256
0e78c5a59226d25c13bde0ad1dadf182bba6a85a292977fe73f9bcca4be8b8e1
```

Formal artifact:

```text
capu-vcml-v27-dma-completion-formal-evidence
ID: 9167432692
ZIP SHA256:
df0a2d94c6dbe3267d9bd06a9d94f4e030b1aa621eb071c4892d93f29a894285
```

## Verified bounded invariants

```text
DMA_ISSUE_ACCEPT
=> EXACT_COMMAND_EPOCH_EFFECT
&& PRIOR_COMPLETION == NOT_COMMITTED
&& DMA_REPLAY_AUTHORITY

DMA_ISSUE_ACCEPT
=> NEXT_COMPLETION == UNKNOWN
&& EVIDENCE_REQUIRED
&& ISSUE_WITNESS_EXISTS

UNKNOWN
=> !DMA_REPLAY_AUTHORITY
&& !RETIRE_AUTHORITY

RECOVERY
=> VOLATILE_COMMAND_STATE_CLEARED
&& CHECKPOINT_PRESERVED
&& ISSUE_WITNESS_PRESERVED
&& COMPLETION_RECEIPT_PRESERVED

RESTORE(pre-issue checkpoint + matching issue witness)
=> UNKNOWN
&& EVIDENCE_REQUIRED
&& !DMA_REPLAY_AUTHORITY

EXACT_EVIDENCE(NOT_COMMITTED)
=> NOT_COMMITTED
&& REPLAY_MAY_REOPEN_IF_NO_NEW_RECOVERY_BARRIER

EXACT_EVIDENCE(COMMITTED)
=> COMMITTED
&& COMPLETION_RECEIPT_EXISTS
&& EFFECT_SPENT
&& !DMA_REPLAY_AUTHORITY

MATCHING_COMPLETION_RECEIPT
=> STALE_CHECKPOINT_CANNOT_RECREATE_REPLAY_AUTHORITY
```

## Liveness boundary discovered during verification

The safety model is intentionally fail-closed. A future-work convergence case remains: if a stale checkpoint itself records `UNKNOWN`, while a later exact `NOT_COMMITTED` resolution is not preserved as durable negative evidence, a subsequent recovery can reconstruct an unresolved state without a surviving witness sufficient to resolve it automatically.

This does not create unauthorized replay or retirement and therefore does not violate the v0.27 safety result. It does mean v0.27 does **not** claim progress/liveness from every stale-UNKNOWN recovery state. Durable negative completion evidence is the natural next refinement.

## Claim boundary

This report verifies a **bounded reduced-width one-command / one-DMA-effect tri-state completion uncertainty authority model** layered on verified v0.26.

The issue witness and discriminating completion evidence are modeled as authoritative durable evidence. This report does **not** establish:

- how real hardware obtains trustworthy completion evidence;
- evidence authenticity or physical durability;
- PCIe, CXL, NoC or device transport correctness;
- partial or multi-beat DMA write semantics;
- device-memory visibility;
- IOMMU, cache or coherence correctness;
- multiple outstanding commands/effects or queue ordering;
- completion-interrupt semantics;
- liveness/fairness;
- production widths;
- unbounded correctness;
- compatibility with or adoption by any specific commercial accelerator design.

Within that bounded scope, v0.27 verifies the central safety rule: **unknown external-effect completion does not become execution authority merely because an older checkpoint is available.**
