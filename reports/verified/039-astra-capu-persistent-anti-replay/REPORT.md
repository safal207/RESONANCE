# RESONANCE Verified Report #039

# ASTRA–CaPU v1.0-A5 — Restart-Safe Persistent Anti-Replay Frontier

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#100`  
**Verified CaPU content head:** `b90dda3fe604b8a642b62e75d7f32db63fb0bceb`  
**Base integrated A1–A4 head:** `290df2599a476f271160660e47d9ef0d53fbfe21`  
**Primary workflow:** `ASTRA-CaPU v1.0-A5 Persistent Anti-Replay Frontier`  
**Primary run:** `33230310578`

## Result

# **PASS — bounded logic-restart anti-replay frontier verified**

A4 physically gated a synthetic accelerator effect using one exact committed authority token, but its `attempt_spent` bit was volatile. Resetting the command-gate logic and reloading the same token was explicitly outside the A4 anti-replay claim.

A5 closes that bounded restart gap with a persistent/retention-domain attempt frontier:

```text
exact committed authority
+ exact persistent lineage
+ attempt == persistent_next_attempt
        ↓
persistent frontier advances
        ↓
command reaches the effect device
```

After a logic restart, volatile authority state is cleared while the modeled persistent frontier and external effect count remain. Reloading the same full attempt identity then fails closed because its attempt ID is behind the persistent frontier.

## Exact persistent lineage

```text
authority_tag
+ queue_incarnation
+ queue_epoch
+ slot_id
+ command_id
+ effect_id
= persistent lineage
```

The attempt identity is the lineage plus `attempt_id`. The command may advance only when:

```text
attempt_id == persistent_next_attempt
```

The frontier is advanced before / atomically with command forwarding. A persistence-advance rejection keeps the external command gate closed.

## Deterministic evidence

The exact-head RTL trajectory produced:

```text
a5_frontier_provisioned next_attempt=0
a5_attempt0_forwarded forward=1 effect_count=1 persistent_next_attempt=1
a5_logic_restart active_valid=0 effect_count=1 persistent_next_attempt=1
a5_same_attempt_after_restart_blocked reject_code=8 effect_count=1
a5_successor_attempt_forwarded attempt=1 effect_count=2 persistent_next_attempt=2
a5_future_attempt_blocked attempt=3 frontier=2 reject_code=8
ASTRA_CAPU_V1_A5_PERSISTENT_ANTI_REPLAY_PASS
```

The deterministic software mirror and 11 focused unit tests passed. The complete A4 RTL trajectory and all 10 A4 unit tests also remained green.

Canonical deterministic result:

```text
schema:
capu.astra.persistent-anti-replay.result.v1.0-a5

result digest SHA256:
a3a16fa02149f260352780aa48806bba54320eef7f6bcbe31500e920d9545502

external_effect_count: 2
persistent_next_attempt: 2
restart_replay_reject_code: 8
future_attempt_reject_code: 8
```

## Exact-head CI

Verified content head:

```text
b90dda3fe604b8a642b62e75d7f32db63fb0bceb
```

GitHub Actions checked PR merge ref:

```text
b6536990371d69b292e74a6d435116e203d5f41f
```

All exact-head pull-request workflows were green:

- `ASTRA-CaPU v1.0-A5 Persistent Anti-Replay Frontier` — run `33230310578` — PASS
  - deterministic job `99041862743` — PASS
  - formal job `99041862630` — PASS
- `Validate Examples` — run `33230310574` — PASS
- `CaPU Core v0 RTL Smoke` — run `33230310560` — PASS
- `FCRP Credential Boundary` — run `33230310858` — PASS
- A4 deterministic and unit regressions — PASS
- A4 bounded-safety regression — PASS

## Formal evidence

Schema:

```text
capu.hardware.astra-persistent-anti-replay-formal-proof.v1.0-a5
```

Result:

```text
proof method: bounded model checking
formal tag width: 3 bits
formal identity width: 3 bits
persistent lineage count: 1
safety depth: 24 — PASS
cover depth: 36 — PASS
VCD witnesses: 5
commit-before-effect: true
logic-reset persistence model: true
A4 bounded-safety regression: PASS
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
24a1789ebdcef5e0644bfb5ea0f8803ca49828132f82b6f9f18bb203dfb97e9b

safety log SHA256:
f232553a0e1c98d54a7cdab975a17f8d1fbe78adbdc042fcc0268ad049fbfa63

cover log SHA256:
c486adad4cb184469bbced53d6729aef9118afadaf57621f3e294d53d622424b

A4 regression log SHA256:
78a183cf1aef1bb312d8f9e7d5f164ee8ab26580b7db7245026b70d0cedecd61
```

## Sealed artifacts

Executable evidence:

```text
artifact: astra-capu-v1-a5-persistent-anti-replay-evidence
artifact ID: 9708271101
ZIP SHA256:
af0df4c5f351664a4dace903ad9352aa33139e73eab3fca2572632ee3180d933
```

Formal evidence:

```text
artifact: astra-capu-v1-a5-persistent-anti-replay-formal-evidence
artifact ID: 9708277793
ZIP SHA256:
1d4afe8ef2303272f1e5b5f91cf88f26947a06ce31ff4be78696becf77197bc1
```

## Verified bounded invariants

```text
COMMAND_FORWARD
=> ACTIVE
&& COMMITTED
&& EXACT_VOLATILE_IDENTITY
&& EXACT_PERSISTENT_LINEAGE
&& ATTEMPT == PERSISTENT_NEXT_ATTEMPT_PRE
&& PERSIST_ADVANCE_ACCEPT
```

```text
SAME_FULL_ATTEMPT_IDENTITY_AFTER_LOGIC_RESTART
=> NO_COMMAND_FORWARD
&& NO_EXTERNAL_EFFECT_INCREMENT
```

```text
SUCCESSOR_ATTEMPT
=> MAY_FORWARD
only when attempt == persistent frontier
```

```text
FUTURE_OR_SKIPPED_ATTEMPT
=> REJECT_PERSISTENT_FRONTIER
```

```text
FRONTIER_EXHAUSTED
=> NO_COMMAND_FORWARD
```

## Safety/liveness tradeoff

A5 intentionally uses commit-before-effect ordering. If the frontier advances and the external device effect subsequently fails or remains unknown, replay authority for that attempt may be conservatively lost. This preserves duplicate-effect safety but does not guarantee progress.

The next recovery milestone should bind the persistent frontier to durable outcome evidence and explicitly resolve the `frontier advanced / effect unknown` window.

## Claim boundary

This is a **bounded reduced-width single-lineage retention-domain model**. Within scope it verifies logic-restart anti-replay, exact persistent-lineage matching, monotonic no-wrap attempt progression, stale same-attempt rejection after volatile reset, successor-attempt acceptance, future-attempt rejection and fail-closed frontier exhaustion.

It does **not** prove:

- actual NVRAM, flash, TPM, secure-element or battery-backed SRAM durability;
- complete power-loss persistence;
- atomicity of real persistent-media writes;
- cryptographic verification of `authority_tag`;
- arbitrary concurrent lineages;
- attempt-counter wrap handling;
- real GPU/TPU/NPU transport;
- CDC correctness;
- FPGA timing or PPA;
- liveness or fairness;
- production widths;
- unbounded correctness.

CaPU PR #100 remains draft and unmerged at publication time.
