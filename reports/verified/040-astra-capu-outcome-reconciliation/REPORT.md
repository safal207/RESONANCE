# RESONANCE Verified Report #040

# ASTRA–CaPU v1.0-A6 — Durable Attempt Outcome Reconciliation

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#101`  
**Verified CaPU content head:** `2cf971e6f9cdefd213e72b4e79d4840c6ed83808`  
**Base A5 head:** `b90dda3fe604b8a642b62e75d7f32db63fb0bceb`  
**Primary workflow:** `ASTRA-CaPU v1.0-A6 Durable Outcome Reconciliation`  
**Primary run:** `33231679617`

## Result

# **PASS — bounded durable UNKNOWN-outcome reconciliation verified**

A5 established restart-safe anti-replay by persistently reserving an attempt before its accelerator-like effect could occur. That ordering intentionally left a recovery window:

```text
persistent frontier advanced
        ↓
command forwarded
        ↓
external effect outcome unknown
        ↓
logic restart
```

A6 binds the persistent attempt frontier to a durable outcome state. An exact reserved attempt enters `UNKNOWN`; blind replay and successor dispatch remain closed until exact outcome evidence resolves that attempt.

```text
UNKNOWN
  ├─ exact NOT_COMMITTED evidence → unresolved cleared
  │                                  successor attempt may reserve
  ├─ exact COMMITTED evidence     → terminal committed
  └─ exact CONFLICT evidence      → terminal conflict / fail closed
```

## Persistent identity and state

Persistent lineage:

```text
authority_tag
+ queue_incarnation
+ queue_epoch
+ slot_id
+ command_id
+ effect_id
```

Per-lineage state:

```text
persistent_next_attempt
unresolved_valid
unresolved_attempt
last_outcome
last_resolved_attempt
terminal_committed
terminal_conflict
```

At most one unresolved attempt exists in the verified model.

## Deterministic evidence

The exact-head RTL trajectory produced:

```text
a6_frontier_provisioned next_attempt=0
a6_attempt0_forwarded effect_count=0 outcome=UNKNOWN next_attempt=1
a6_logic_restart_unknown_preserved unresolved_attempt=0 next_attempt=1
a6_same_attempt_after_restart_blocked reject_code=10 effect_count=0
a6_negative_reconcile_accepted attempt=0 outcome=NOT_COMMITTED
a6_attempt1_forwarded effect_count=1 outcome=UNKNOWN next_attempt=2
a6_successor_blocked_while_unknown reject_code=10 effect_count=1
a6_stale_reconcile_blocked reject_code=4
a6_committed_reconcile_accepted attempt=1 terminal_committed=1
a6_terminal_replay_blocked reject_code=11 effect_count=1
ASTRA_CAPU_V1_A6_OUTCOME_RECONCILIATION_PASS
```

The deterministic software mirror and 13 focused unit tests passed. The complete A5 RTL trajectory, all 11 A5 unit tests and the A5 bounded proof also remained green.

Canonical deterministic result:

```text
schema:
capu.astra.outcome-reconciliation.result.v1.0-a6

result digest SHA256:
6a7e969c724f7b441edb8cc701a03e0b8964dd0542a4e2fe64c961a4c9c4bae4

external_effect_count: 1
persistent_next_attempt: 2
last_outcome: COMMITTED
restart_replay_reject_code: 10
stale_reconcile_reject_code: 4
terminal_replay_reject_code: 11
```

## Exact-head CI

Verified content head:

```text
2cf971e6f9cdefd213e72b4e79d4840c6ed83808
```

GitHub Actions checked PR merge ref:

```text
3050b32eb6e23956c8788f8f602364323161f9e5
```

All exact-head workflows were green:

- `ASTRA-CaPU v1.0-A6 Durable Outcome Reconciliation` — run `33231679617` — PASS
  - deterministic job `99045481941` — PASS
  - formal job `99045482115` — PASS
- `Validate Examples` — run `33231679591` — PASS
- `CaPU Core v0 RTL Smoke` — run `33231679610` — PASS
- A5 deterministic and unit regressions — PASS
- A5 bounded-safety regression — PASS

## Formal evidence

Schema:

```text
capu.hardware.astra-outcome-reconciliation-formal-proof.v1.0-a6
```

Result:

```text
proof method: bounded model checking
formal tag width: 3 bits
formal identity width: 3 bits
persistent lineage count: 1
maximum unresolved attempts: 1
safety depth: 28 — PASS
cover depth: 48 — PASS
VCD witnesses: 9
commit-before-effect: true
logic-reset persistence model: true
A5 bounded-safety regression: PASS
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
d630abf0d0c3890859ff6ed51a05decd984c27e085c784a842458bc661cfeff6

safety log SHA256:
bae52e101e38052f005d7776aaaa10d599cfc2f1ddb44e3fc6c50d5b06e6ec54

cover log SHA256:
0efb7610b2cf6f72e615bf149e019774e418650f330fbf48ab36ed18f6e3278d

A5 regression log SHA256:
7540b8b8517b41c19779eb743bbacc00276f43404d17a11c30a89fe5adc92de6
```

## Sealed artifacts

Executable evidence:

```text
artifact: astra-capu-v1-a6-outcome-reconciliation-evidence
artifact ID: 9708674313
ZIP SHA256:
0fbb85a5f64b15c0202954a85812c5c81fb8ba3209afa5a1469ab559831986c0
```

Formal evidence:

```text
artifact: astra-capu-v1-a6-outcome-reconciliation-formal-evidence
artifact ID: 9708693569
ZIP SHA256:
1d289a78f78157f0bfbe1e676fb5fa89d4f0798a5d58c4cf2c898eeeb81eb520
```

## Verified bounded invariants

```text
COMMAND_FORWARD
=> PERSISTENT_RESERVATION_ACCEPTED
&& OUTCOME_POST == UNKNOWN
```

```text
OUTCOME_UNKNOWN
=> NO_COMMAND_FORWARD
&& NO_BLIND_REPLAY
```

```text
NOT_COMMITTED_RECONCILIATION
=> UNRESOLVED_CLEARED
&& FRONTIER_NOT_DECREMENTED
&& ONLY_SUCCESSOR_ATTEMPT_MAY_FORWARD
```

```text
COMMITTED_RECONCILIATION
=> TERMINAL_COMMITTED
&& NO_LATER_ATTEMPT_MAY_FORWARD
```

```text
CONFLICT_RECONCILIATION
=> TERMINAL_CONFLICT
&& NO_LATER_ATTEMPT_MAY_FORWARD
```

```text
REJECTED_OR_STALE_EVIDENCE
=> NO_PERSISTENT_STATE_MUTATION
```

## Meaning of the result

A6 closes the safety/liveness split introduced by A5 for the exact bounded case:

- unknown external completion cannot silently become replay authority;
- exact negative evidence can restore progress without reusing the consumed attempt identity;
- exact committed evidence can establish terminal no-replay authority;
- stale or foreign evidence cannot rewrite the current unresolved outcome.

This moves ASTRA–CaPU from persistent anti-replay alone toward a restart-safe accelerator transaction protocol.

## Claim boundary

This is a **bounded reduced-width single-lineage model with one unresolved attempt**. Within scope it verifies commit-before-effect reservation, persistent `UNKNOWN` recovery, exact `NOT_COMMITTED / COMMITTED / CONFLICT` reconciliation, stale-evidence rejection and terminal replay closure.

The persistent outcome store is a retention-domain abstraction with explicit cold reset. It is not proof of actual NVRAM, flash, TPM, secure-element or battery-backed SRAM durability, complete power-loss survival, or atomic real persistent-media writes.

A6 checks exact evidence identity but **trusts the supplied outcome discriminator**. It does not prove:

- evidence truth or cryptographic authentication;
- Byzantine-resistant multi-source reconciliation;
- evidence-source availability;
- arbitrary concurrent lineages;
- multiple unresolved attempts;
- attempt-counter wrap handling;
- real GPU/TPU/NPU transport;
- CDC or memory-order correctness;
- FPGA timing or PPA;
- liveness or fairness;
- production widths;
- unbounded correctness.

CaPU PR #101 remains draft and unmerged at publication time.
