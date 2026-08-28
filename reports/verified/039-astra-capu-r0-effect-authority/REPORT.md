# RESONANCE Verified Report #039

# ASTRA–CaPU R0 — Effect Authority Across Ambiguous Accelerator Completion

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Agentic Execution  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#96`  
**Verified CaPU content head:** `b8c658ef2cdbbf6bb59cb59113ade6281cee6368`  
**Architecture base head:** `c5cf812d731d582f0acc66c25c7ddf62f3699412`  
**Verified hardware-semantics ancestor:** CaPU v0.33 / `f9d3832d84dc2415617a782cb226af83943b5ecd`  
**Primary workflow:** `ASTRA-CaPU R0 Effect Authority`  
**Primary run:** `33181326366`

## Result

# **PASS — deterministic fault-injected effect-authority witness verified**

R0 is the first executable bridge from the ASTRA–CaPU v1 architecture package into a complete intent-to-effect recovery path:

```text
IntentEnvelope
  -> committed AuthorityTicket
  -> synthetic accelerator dispatch
  -> crash before completion receipt
  -> DISPATCHED_UNKNOWN
  -> exact OutcomeEvidence
  -> ProofReceipt
  -> trusted memory update
```

The result is intentionally comparative. An unsafe baseline retries after a missing completion receipt and duplicates an already-committed effect. The CaPU path preserves uncertainty, blocks blind replay and false success, rejects stale foreign-incarnation evidence, and updates trusted memory only after exact committed outcome evidence produces a proof receipt.

## Unsafe baseline witness

The baseline implements the flawed recovery rule:

```text
missing receipt / timeout
=> assume first attempt did not execute
=> retry
```

The injected first attempt did commit, so the deterministic result was:

```text
unsafe_baseline dispatches=2 external_effects=2 duplicate_effect=true
```

This is a synthetic negative control, not a measurement of a specific production accelerator.

## CaPU recovery boundary

After exact committed authority dispatches once, the simulated process crashes before storing completion evidence. A stale pre-dispatch checkpoint is then restored.

Durable issue evidence reconstructs:

```text
DISPATCHED_UNKNOWN
```

and enforces:

```text
DISPATCHED_UNKNOWN
=> NO_BLIND_REPLAY
&& NO_SUCCESS_CLAIM
&& NO_RETIRE
&& NO_TRUSTED_MEMORY_UPDATE
```

The deterministic witness produced:

```text
capu_unknown_boundary blind_replay_blocked=true success_claim_blocked=true memory_update_blocked=true
```

## Exact authority identity

Outcome evidence receives authority only when it matches:

```text
authority_id
+ authority_incarnation
+ queue_epoch
+ slot_id
+ command_id
+ execution_epoch
+ effect_id
```

The adversarial stale message reused the same numeric queue/command/execution/effect identifiers but carried a prior authority incarnation. It was rejected and counted as quarantined evidence without changing current `DISPATCHED_UNKNOWN` state.

Exact current evidence then resolved the effect as committed:

```text
capu_reconciled dispatches=1 external_effects=1 stale_evidence_quarantined=1 trusted_memory_updated=true
ASTRA_CAPU_R0_EFFECT_AUTHORITY_PASS
```

## Machine-readable result

```json
{
  "schema": "capu.astra.r0.result.v1",
  "baseline_dispatch_count": 2,
  "baseline_external_effect_count": 2,
  "baseline_duplicate_effect": true,
  "capu_dispatch_count": 1,
  "capu_external_effect_count": 1,
  "blind_replay_blocked": true,
  "success_claim_blocked": true,
  "memory_update_blocked": true,
  "stale_evidence_quarantined": 1,
  "trusted_memory_updated": true,
  "proof_receipt_digest": "201f12f4a796a757fb3981f7d98a0d4dbdbaf9d3da6871448d6e61441bce5b24"
}
```

## Exact-head CI

Verified content head:

```text
b8c658ef2cdbbf6bb59cb59113ade6281cee6368
```

GitHub Actions checked PR merge ref:

```text
fc597ae4de067309d629f7ebd0b71772e5122a49
```

All registered pull-request workflows were green:

- `ASTRA-CaPU R0 Effect Authority` — run `33181326366` — PASS
  - job `98882955334` — PASS
  - complete Rust suite: **81 tests passed**, 0 failed;
  - executable trajectory — PASS;
  - JSON result validation — PASS;
  - SHA-256 evidence sealing — PASS.
- `CMC Rust Simulator` — run `33181326345` — PASS
  - job `98882955125` — PASS;
  - legacy demos, sealed traces, fixtures, replay, audit, runtime examples and reviewer command — PASS.
- `Validate Examples` — run `33181326340` — PASS
  - job `98882955182` — PASS.

## Sealed evidence

```text
artifact: astra-capu-r0-effect-authority-evidence
artifact ID: 9689798660
ZIP SHA256:
7987ba65a274863b98760cf76682a69447a2a77707503e176f7725e39492af1f
```

Exact-head file/log hashes:

```text
R0 state machine:
44fd443ffc6b9dccee055babff16e4542c6a1c1c6daa4ec8c078e79407494f5a

CaPU module registry:
4862910002f0f70975574d8c520918775e063201c3405aaa140b02a16bd4c8bc

Executable witness:
e7ab8526d39c63f595fc8b1727eb1fd3ca61b201ccaf655b4f6441e13531d8aa

Trajectory log:
138585c63ba72dc0da3af526ad751291aa2b358ef81b83ba4f128bbbcfe9732b
```

## Verified software-reference invariants

```text
NO_COMMITTED_AUTHORITY
=> NO_DISPATCH

EXACT_COMMITTED_AUTHORITY
=> AT_MOST_ONE_DISPATCH_WHILE_OUTCOME_UNKNOWN

DISPATCHED_UNKNOWN
=> NO_BLIND_REPLAY
&& NO_SUCCESS_CLAIM
&& NO_TRUSTED_MEMORY_UPDATE

SAME_NUMERIC_IDS && FOREIGN_AUTHORITY_INCARNATION
=> REJECT_AND_QUARANTINE

EXACT_NOT_COMMITTED_EVIDENCE
=> ONE_REPLAY_AUTHORITY_MAY_REOPEN

EXACT_COMMITTED_EVIDENCE
=> REPLAY_CLOSED
&& PROOF_RECEIPT_CREATED
&& TRUSTED_MEMORY_UPDATE_MAY_PROCEED
```

## Claim boundary

This is **software-reference deterministic and fault-injected evidence**. It is not RTL/formal-hardware, FPGA, silicon, PPA, or production transport evidence.

The synthetic executor records whether a modeled external effect committed. It does not model real PCIe/CXL/NoC/DMA transport, payload values, partial writes, IOMMU/cache/coherence, device attestation, cryptographic evidence authenticity, durable storage failure, liveness/fairness, production widths, or unbounded correctness.

Within the defined scope, the result verifies that ambiguous completion does not become replay, success, retirement, or trusted-memory authority, while exact committed evidence closes replay and produces a deterministic proof receipt.

CaPU PR #96 remains draft and unmerged at publication time.
