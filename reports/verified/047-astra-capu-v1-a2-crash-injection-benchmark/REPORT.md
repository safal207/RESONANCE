# RESONANCE Verified Report #047

# ASTRA–CaPU v1.0-A2 — Accelerator Crash-Injection Benchmark

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Recovery Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#94`  
**Verified CaPU content head:** `5038d3c76d649006323d2ba026ab9bafb46d01f2`  
**A1 base head:** `41ffe240cc7be0be2e614cba590851f84a63e949`  
**Workflow:** `ASTRA-CaPU v1.0-A2 Crash-Injection Benchmark`  
**GitHub Actions run:** `33180380564`

## Result

# **PASS — unsafe duplicate/false-success failures reproduced and prevented by the A1 recovery contract**

A2 is the first discriminating end-to-end benchmark built on the ASTRA–CaPU A1 Accelerator Effect Authority Interface.

The benchmark uses a synthetic, deliberately non-idempotent accelerator target. Every physical commit increments an effect counter, so a repeated command produces a visible duplicate rather than being hidden by an idempotent API.

It compares two recovery strategies after local completion state is lost:

```text
unsafe baseline:
missing receipt -> assume NOT_COMMITTED -> retry
or
dispatch acknowledgement -> claim success

ASTRA–CaPU:
durable issue witness -> UNKNOWN
-> no replay / retirement / success claim
-> exact device readback
-> evidence-gated retry or retirement
```

## Exact-head verification

All registered workflows on the exact content head passed:

```text
A2 workflow run:       33180380564  PASS
A2 benchmark job:      98879808438  PASS
A1 regression:         12 / 12      PASS
A2 test suite:         11 / 11      PASS
Machine result:                     PASS

Validate Examples:     33180380536  PASS
Validate job:          98879808248  PASS
```

No Core RTL workflow was expected because A2 adds a deterministic software benchmark and no RTL.

## Four injected scenarios

### 1. Crash before the external effect

The initial device operation does not commit.

```text
unsafe baseline:
blind retry -> 1 physical effect

ASTRA–CaPU:
UNKNOWN -> exact NOT_COMMITTED evidence
-> one authorized next attempt
-> 1 physical effect
```

Both eventually produce one effect, but only the CaPU path establishes the authority to retry.

### 2. Crash after effect, before receipt

The external effect commits, but the process crashes before local completion state is available.

```text
unsafe baseline:
missing receipt -> blind retry
-> 2 physical effects
-> 1 duplicate

ASTRA–CaPU:
durable issue witness -> UNKNOWN
-> exact COMMITTED readback
-> no retry
-> 1 physical effect
-> sealed receipt
```

### 3. Dispatch acknowledgement mistaken for completion

The device accepts dispatch but does not commit the external effect.

```text
unsafe baseline:
dispatch ACK -> claims success
-> 0 physical effects
-> 1 false success

ASTRA–CaPU:
UNKNOWN -> exact NOT_COMMITTED readback
-> one authorized retry
-> exact COMMITTED readback
-> 1 effect and sealed success
```

### 4. Conflicting readback

The evidence provider returns `CONFLICT`.

```text
unsafe baseline:
blind retry -> 2 effects -> 1 duplicate

ASTRA–CaPU:
CONFLICT
-> no replay
-> no retirement
-> no success claim
```

## Aggregate discriminator

```text
unsafe duplicate effects: 2
CaPU duplicate effects:   0

unsafe false successes:   1
CaPU false successes:     0

unsafe retries:           3
CaPU retries:             2
CaPU UNKNOWN blocks:      4
CaPU sealed successes:    3
CaPU conflict fail-closed:1
```

The unsafe baseline is required to exhibit real failure. Without a reproduced duplicate and false-success path, the benchmark would not establish that the A1 contract changes the outcome.

## Benchmark digest

```text
a75674fb89ffbf84148421b13c6490c096ebf614c10eafad6f02f8200ff01b87
```

## Executable artifacts

```text
tools/astra_capu_crash_benchmark_a2.py
tests/test_astra_capu_crash_benchmark_a2.py
schemas/hardware/astra-capu-crash-benchmark-v1.0-a2.schema.json
examples/hardware/astra-capu-v1-a2-expected.json
docs/hardware/ASTRA_CAPU_V1_A2_CRASH_INJECTION_BENCHMARK.md
.github/workflows/astra-capu-v1-a2-crash-injection.yml
```

The A2 workflow also reruns the complete A1 contract suite on the same exact head.

## Sealed evidence

```text
artifact:
astra-capu-v1-a2-crash-benchmark-evidence

artifact ID:
9689425557

ZIP SHA256:
929fcc0b9f695dc6b721a06ce1fc172f930f9dc82c972c167f409d4491f04503
```

Exact hashes:

```text
A1 reference engine:
813a913035bae1e5ca358091dd3ce5c8e2e040d97e6dc2e0535282daf1c776a1

A2 benchmark engine:
5a2a03456a0587ab05777e4bf5a1462e52326e81a85502a5b922acc39581a63e

A1 regression suite:
8327abfde44b109e9c41c6de46a7b3ec18222f02ef1047874a07d405e3270fb7

A2 test suite:
2b485f00d25a8e2374a63d0855c9d366b04bb0f7082ed96c4649aaa59f4c5818

A1 schema:
e7b18d94916ad5e1b9547c3775b882b0dfbe29fd0ea757732441b5ba92bef1cc

A2 result schema:
b0c86d14bb8169dd9fcf9313c6e122edc1aadd72f41abfdd88b9c5b40197daa6

expected fixture:
4c1cc3d93a3c29c16e019db93e69b4b665505b1d4f36d3c602f919cdc1be0cd8

benchmark document:
a14c7a953a4be42c1aaccc4ea9b2b4c22519105148374008eb49821daa1f9342

A1 regression log:
1d5c23a1d43587fc830222862d87f367c9c83b36aa1001cbffb9870d34af51a3

A2 test log:
804460279d3e08f7801b51e1b3666406962b50f7f272197a1529be9820fa3001

benchmark log:
649fa98f560347bb70edd2d47ba0817f0fac111931867477993c584491e4702a

machine result:
b00b54ab0cbd35a177c27e6dd54a492808ae58b055241381c02cef71bdef9092
```

## What changed scientifically

A1 established the rule that ambiguous completion must remain `UNKNOWN`. A2 now demonstrates why the rule matters:

```text
ambiguous completion
+ blind replay
= duplicate external effect

or

dispatch acknowledgement
+ assumed outcome
= false success
```

The benchmark therefore moves ASTRA–CaPU from an interface-level safety claim to a falsifiable system-level comparison with a failing control path.

## Claim boundary

This result verifies deterministic software behavior over a synthetic non-idempotent accelerator target and synthetic device readback.

It does **not** claim:

```text
real GPU / TPU / NPU command-queue integration
PCIe / CXL / NoC transport behavior
real device reset semantics
production durable storage
evidence authenticity
hardware performance or PPA
FPGA or silicon implementation
formal proof of the A2 composition
arbitrary concurrency
liveness / fairness
unbounded correctness
external certification
```

The next discriminating milestone is **A3 — a real local accelerator API or hardware-simulator adapter**. It must preserve the A1 identity and evidence boundaries while exposing actual command submission, completion/readback, restart, and negative controls without importing unsupported semantics by assertion.
