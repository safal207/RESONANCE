# RESONANCE Verified Report #033

# CaPU v0.28 — Durable Negative Completion Evidence / UNKNOWN Convergence

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#81`  
**Verified CaPU content head:** `bc3594b187b4f5901d90db3bd76e1abaa60a80e4`  
**Workflow:** `CaPU vCML Durable Negative Completion v0.28`  
**GitHub Actions run:** `31668560389`

## Result

# **PASS — bounded durable negative completion authority and UNKNOWN convergence verified**

CaPU v0.28 closes the liveness/convergence gap intentionally left by v0.27. v0.27 safely represented issued-but-unresolved DMA completion as `UNKNOWN` and refused to guess whether replay was safe. v0.28 adds a modeled durable negative-completion receipt for the case where exact discriminating evidence establishes that the effect did **not** commit.

That negative result now survives a later crash and can dominate a stale checkpoint that still records `UNKNOWN`.

```text
DMA issue
  ↓
UNKNOWN
  ↓
exact NOT_COMMITTED evidence
  ↓
durable negative receipt
  ↓
crash
  ↓
stale UNKNOWN checkpoint restore
  ↓
negative receipt wins
  ↓
NOT_COMMITTED
  ↓
replay may reopen
```

The receipt is attempt-sensitive. A new retry consumes the old negative receipt and creates a fresh issue witness, returning the effect to `UNKNOWN`. Therefore evidence that the previous attempt did not commit cannot silently authorize replay of or describe a newer unresolved attempt.

## Exact-head verification

Verified content head:

```text
bc3594b187b4f5901d90db3bd76e1abaa60a80e4
```

All pull-request workflow runs registered on this exact head completed successfully:

- `CaPU vCML Durable Negative Completion v0.28` — run `31668560389` — PASS
  - deterministic job `94348334634` — PASS
  - formal job `94348334759` — PASS
  - v0.27 deterministic + canonical regression — PASS
  - v0.27 bounded safety regression — PASS
- `CaPU Core v0 RTL Smoke` — run `31668560414` — PASS
- `Validate Examples` — run `31668560406` — PASS

## Deterministic trajectory

The verified executable path produced:

```text
command_submit accepted=1 command=9 execution_epoch=5 effect=12
dma_issue accepted=1 completion=UNKNOWN durable_issue_witness=1
unknown_checkpoint captured=1 completion=UNKNOWN dma_issued=1
exact_evidence_not_committed accepted=1 durable_negative_receipt=1 replay_authority=1
recovery stale_unknown_checkpoint_preserved=1 negative_receipt_preserved=1
stale_unknown_restore negative_receipt_wins=1 completion=NOT_COMMITTED replay_authority=1
retry_issue accepted=1 old_negative_receipt_consumed=1 completion=UNKNOWN
retry_crash_restore current_issue_witness_wins=1 completion=UNKNOWN replay_authority=0
foreign_completion_evidence rejected=1 exact_identity_required=1
exact_evidence_committed accepted=1 durable_completion_receipt=1 effect_spent=1 replay_authority=0
command_retire accepted=1 completion=COMMITTED
late_stale_unknown_restore completion_receipt_wins=1 completion=COMMITTED replay_authority=0
CAPU_VCML_DURABLE_NEGATIVE_COMPLETION_V28_PASS
```

This trajectory demonstrates both branches required for safe convergence:

1. exact negative completion evidence survives recovery and defeats stale `UNKNOWN`;
2. once a retry is issued, that old negative evidence is consumed and the current issue witness again forces `UNKNOWN` until new evidence arrives.

## Canonical checkpoint binding

Canonical v0.28 digest:

```text
2ef0d09873fa10b8e0c73ad436222b98b3d89f9ab2176a00862e8b20c94a0d53
```

The domain-separated commitment binds:

- verified v0.27 digest;
- live command identity and completion state;
- checkpoint identity and completion state;
- durable current-issue witness;
- durable negative-completion receipt;
- durable committed-completion receipt.

Mutation checks passed:

```text
durable_negative_to_unknown_mixed_state_rejected=1
foreign_negative_receipt_mixed_state_rejected=1
stale_negative_receipt_survives_retry_mixed_state_rejected=1
VCML_DURABLE_NEGATIVE_CHECKPOINT_V28_PASS
```

## Executable evidence

Artifact:

```text
name: capu-vcml-v28-durable-negative-evidence
artifact ID: 9168872581
ZIP SHA256:
4caa9f6a163446ea81bb3f5ba914a176cbbd6c82e809ede3a34b9cb06a4f5973
```

Sealed hashes:

```text
RTL:
4004219ce9e0e10f870b60cbd04f6b071553c07fc23f0339d152af4d96285f38

TB:
4f0fc5c9600c479d4ccdeef05f6eee38400935b66a0d1dfe9ab772a53ad41705

canonical encoder:
2f43eb394b1bdbf276dd3a3bed391bc5f9d29fba955968179353e6fafd2662ed

canonical test:
1dc2adae74dba5f128a1a78584bfe9703629669c4f87a8c1b716f7cfa24c0ea0

trajectory log:
1dab18550b919b10c90a1c6983381bc5cdf3032b75c7337e474d8d2929b22a6c

canonical Python log:
397306fcec5e07393de58c285407f807b9c3f5897b4644f6e11024d7d5a3c964

v0.27 deterministic regression log:
00118a5c6c4b40b1cec5b92a8ecbce7ee81cb4166e0a3f205d81b3a82af3ff17

v0.27 canonical regression log:
acc18a6d0fc6f833c38d8b75caebc2c4ef9a36c405440fc8d564b26c49d6501f
```

## Formal evidence

v0.28 uses **bounded model checking**, not an inductive or unbounded correctness claim.

```text
schema:
capu.hardware.durable-negative-completion-formal-proof.v0.28

formal identity width:
2 bits per command / execution epoch / effect field

safety method:
bounded model checking

safety depth:
18
result: DONE (PASS, rc=0)

cover depth:
28
result: DONE (PASS, rc=0)

VCD witnesses:
9

v0.27 bounded safety regression:
PASS
```

Pinned toolchain:

```text
SBY:
b1a1e98cba941ec8433f8dc27f416cd7bb7f14be

Yosys 0.33 (git sha1 2584903a060)
Z3 4.8.12
```

Exact-head formal hashes:

```text
formal input SHA256:
047fa3373af10af585dbc0a4e2e5efe026778a9a659e2da21cd961d3d6b6d8d4

safety log SHA256:
d0a125cc759556cabb1c754272607662fba7a0c7017c5e7bbf41942a212e8b0d

cover log SHA256:
e536c2d91114d715a93d5134aeca3f10ce442d471db011b53f66ab11c24d8fd6

v0.27 regression log SHA256:
6bee628b25d3666792368ae9e5e737600c959ba9e9ae153bde214f5c7a0d56bc
```

Formal artifact:

```text
name: capu-vcml-v28-durable-negative-formal-evidence
artifact ID: 9168927093
ZIP SHA256:
2c576cb0399c57f0ea00e1aa7a70dbaa4b1fb55eba71ad96bb81746675ebe581
```

## Verified bounded invariants

```text
UNKNOWN
=> NO_DMA_REPLAY_AUTHORITY
&& NO_RETIRE_AUTHORITY
&& EVIDENCE_REQUIRED

EXACT_EVIDENCE(NOT_COMMITTED)
=> DURABLE_NEGATIVE_RECEIPT
&& NOT_COMMITTED
&& OLD_ISSUE_WITNESS_CONSUMED

RECOVERY
=> NEGATIVE_RECEIPT_PRESERVED

RESTORE(STALE_UNKNOWN + MATCHING_NEGATIVE_RECEIPT)
=> NOT_COMMITTED
&& !EVIDENCE_REQUIRED
&& REPLAY_MAY_REOPEN_IF_NO_NEW_BARRIER

RETRY_ISSUE
=> OLD_NEGATIVE_RECEIPT_CONSUMED
&& UNKNOWN
&& NEW_ISSUE_WITNESS

MATCHING_CURRENT_ISSUE_RECEIPT
=> UNKNOWN
&& NEGATIVE_RECEIPT_CANNOT_OVERRIDE_NEWER_ATTEMPT

MATCHING_COMPLETION_RECEIPT
=> COMMITTED
&& STALE_UNKNOWN_CANNOT_RECREATE_REPLAY_AUTHORITY
```

## Verification note

The first deterministic CI attempt exposed a testbench scheduling issue rather than a semantic RTL failure. After an accepted restore, the TB deasserted `restore_valid` and sampled combinational `dma_replay_authority` in the same delta cycle. The fix added a one-unit settle before sampling. RTL and formal properties were unchanged. The final exact-head run re-executed deterministic, canonical, formal, predecessor-regression and repository guardrails after that TB-only correction.

## Claim boundary

This is a **bounded reduced-width one-command / one-DMA-effect durable negative completion evidence and UNKNOWN-convergence model** layered on verified v0.27.

Issue, negative-completion and committed-completion receipts are modeled as authoritative durable evidence. The result does **not** prove how real hardware or software obtains, authenticates, persists, orders or transports those receipts; PCIe/CXL/NoC semantics; device-memory visibility; IOMMU/cache/coherence; partial or multi-beat DMA writes; multiple outstanding commands or effects; queue ordering; completion interrupts; production widths; or unbounded correctness.

## Next boundary

The next natural research boundary is **partial / multi-beat DMA recovery authority**:

```text
beat 0 committed
beat 1 committed
beat 2 UNKNOWN
crash
→ preserve per-segment completion authority
→ never duplicate committed visible beats
→ replay only exact unresolved / NOT_COMMITTED segments
```

That moves the accelerator recovery model from one atomic external effect toward partially visible external progress while preserving the same evidence-first rule: recovery authority must come from exact causal evidence, not from guessed completion.
