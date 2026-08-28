# RESONANCE Verified Report #048

# ASTRA–CaPU v1.0-A3 — Separate-Process Icarus Device Adapter

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Hardware-Simulator Recovery  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#95`  
**Verified CaPU content head:** `99adcd8cb0d83bec4b0fe89999f3483b923870a1`  
**A2 base head:** `5038d3c76d649006323d2ba026ab9bafb46d01f2`  
**Workflow:** `ASTRA-CaPU v1.0-A3 Icarus Device Adapter`  
**GitHub Actions run:** `33181084529`

## Result

# **PASS — evidence-gated recovery verified across separate hardware-simulator processes**

A3 moves the A1 authority contract and A2 duplicate/false-success controls across a real process boundary into Icarus Verilog.

Every device reset, dispatch and readback launches a fresh `vvp` process. The synthetic external effect counter is persisted outside the process by the testbench, allowing a later process to observe an effect committed by a process that no longer exists.

```text
host authority ticket
-> vvp dispatch process
-> optional effect commit
-> dropped receipt / process termination
-> fresh vvp readback process
-> exact A1 outcome evidence
-> retry / retirement / proof receipt
```

## Exact-head verification

All registered workflows passed on one exact content head:

```text
A3 workflow run:       33181084529  PASS
A3 adapter job:        98882130906  PASS
A1 regression:         12 / 12      PASS
A2 regression:         11 / 11      PASS
A3 test suite:          8 / 8       PASS
Machine result:                     PASS

Core RTL Smoke:        33181084412  PASS
RTL smoke job:         98882130737  PASS
STORE proof job:       98882229045  PASS

Validate Examples:     33181084556  PASS
Validate job:          98882131195  PASS
```

## Hardware-simulator boundary

A3 adds a synthesizable effect-counter device model:

```text
rtl/astra_capu_effect_counter_a3.sv
```

and a testbench process bridge:

```text
rtl/tb/astra_capu_effect_counter_a3_tb.sv
```

The bridge accepts plusarg operations:

```text
reset
dispatch(commit, drop_receipt)
readback
```

and persists the external effect count in a host file between simulator invocations.

The direct smoke trajectory passed:

```text
process 1: reset   -> count=0
process 2: dispatch(commit=1, drop_receipt=1) -> count=1, receipt=0
process 3: readback -> count=1
```

This establishes that the readback is not retained Python or Verilog process memory. It comes from a fresh simulator process loading durable external state.

## Unsafe duplicate path

```text
vvp process 1:
effect commits
receipt dropped
process exits

vvp process 2:
missing receipt treated as non-commit
same effect blindly retried

vvp process 3:
readback count = 2
```

Result:

```text
unsafe duplicate effects = 1
```

## ASTRA–CaPU committed path

```text
pre-dispatch A1 checkpoint
-> durable issue witness
-> vvp effect commits, receipt dropped
-> process exits
-> recovery reconstructs UNKNOWN
-> fresh vvp readback count = 1
-> exact COMMITTED evidence
-> no retry
-> SEALED
```

Result:

```text
CaPU duplicate effects = 0
```

## Unsafe false-success path

```text
vvp dispatch accepts command
external effect does not commit
host treats acceptance as success
fresh readback count = 0
```

Result:

```text
unsafe false successes = 1
```

## ASTRA–CaPU negative path

```text
dispatch accepted, effect not committed
-> process exits
-> durable issue witness reconstructs UNKNOWN
-> fresh readback count = 0
-> exact NOT_COMMITTED evidence
-> one authorized next attempt
-> new vvp process commits
-> fresh readback count = 1
-> SEALED
```

Result:

```text
CaPU false successes = 0
CaPU authorized retries = 1
```

## Aggregate result

```text
simulator process launches: 15
persistent restart verified: true

unsafe duplicate effects: 1
CaPU duplicate effects:   0

unsafe false successes:   1
CaPU false successes:     0

CaPU UNKNOWN recoveries:  2
CaPU authorized retries:  1
CaPU sealed successes:    2
```

Final device counts:

```text
unsafe duplicate path:       2
CaPU committed path:         1
unsafe false-success path:   0
CaPU negative/retry path:    1
```

## Benchmark digest

```text
96ee8c56c1459b300a32f120ff99a619a1345a8d949bff098773257cb684db3e
```

## Executable artifacts

```text
rtl/astra_capu_effect_counter_a3.sv
rtl/tb/astra_capu_effect_counter_a3_tb.sv
tools/astra_capu_icarus_adapter_a3.py
tests/test_astra_capu_icarus_adapter_a3.py
schemas/hardware/astra-capu-icarus-adapter-v1.0-a3.schema.json
examples/hardware/astra-capu-v1-a3-expected.json
docs/hardware/ASTRA_CAPU_V1_A3_ICARUS_DEVICE_ADAPTER.md
.github/workflows/astra-capu-v1-a3-icarus-device-adapter.yml
```

## Sealed evidence

```text
artifact:
astra-capu-v1-a3-icarus-device-evidence

artifact ID:
9689706365

ZIP SHA256:
35793036b198249a220b46d5c5abfb0450b53661f111c9e736322ec1c629059a
```

Exact hashes:

```text
RTL device:
73a5af7d6104777def043430e4fa6171dc858f1ee63a4a53469a78623c407742

RTL testbench:
33a86aa0a67bd4831d6e6acdfe58d12e3a08c1dd9646bb3b86ef565f8dfa80bc

A1 engine:
813a913035bae1e5ca358091dd3ce5c8e2e040d97e6dc2e0535282daf1c776a1

A2 engine:
5a2a03456a0587ab05777e4bf5a1462e52326e81a85502a5b922acc39581a63e

A3 adapter:
a0b8b11300b8c35c2ea8cbafa1125372d22417fefdcfb6da4fadb0878c327f2b

A3 tests:
da686a69b08d8d10d818c3c38207aaed0d935851bf9c9eb776d67231b3c3a6ab

A3 schema:
6a5ef74c6dd5cb6351bea0b1a04b0f1600536cd086ec2ebc0c485ddb92963cc2

expected fixture:
1d32bed17ca637827a4a9673fd78a910ef063794088f9a5c2c56852812177f02

A3 document:
f4ce6be6e771cac358f39b7708957293061671493d9365ec7df9567a25345df1

compiled simulator executable:
b0b62127231f5ffdb351a77858dbbefc3a22cd110fddb7199427da6db10afcd7

reset smoke log:
b7c6eaa9d405d41d7f9002e4d1020dd37a2a1a6dc7613a52342b320412cba2d3

dropped-receipt dispatch log:
5a2a061788306eb20afc074f33b0f1c0ec429c90877308ebf009c682f606136e

fresh-process readback log:
8cba3ff462d0160e5f02c3206e014e410b1f1aae154a652c31b7cc6a8e973e8c

A1 regression log:
1d5c23a1d43587fc830222862d87f367c9c83b36aa1001cbffb9870d34af51a3

A2 regression log:
804460279d3e08f7801b51e1b3666406962b50f7f272197a1529be9820fa3001

A3 test log:
6d9b3bb5cd58a0a8084f2550dffddd9cabc000a3a8a1319a55b80c774abb11f3

A3 benchmark log:
468ba7654f4e6dba6ec7dabe382361826572dd79cc522e994a9640874e35efc7

A3 machine result:
218c4446b5aa0557df954181e8ceadd83b4f9cc725607bc446f412d2a6020274
```

## What changed scientifically

A2 demonstrated the benefit of the A1 contract inside a software benchmark. A3 establishes a stronger composition boundary:

1. command execution occurs in a hardware simulator;
2. the simulator process that commits the effect terminates;
3. durable external state survives that process;
4. outcome evidence is obtained from a fresh simulator process;
5. the same exact A1 rules still prevent duplicate effects and false success.

This is the first ASTRA–CaPU milestone where the authority contract controls recovery around an executable hardware model rather than only a software target.

## Claim boundary

The effect-counter RTL is synthesizable. However, durable state is provided by testbench host-file persistence, not by synthesizable nonvolatile memory.

A3 does **not** claim:

```text
real GPU / TPU / NPU integration
production accelerator command queue
PCIe / CXL / NoC behavior
real power-loss persistence
cryptographic evidence authenticity
hardware-rooted identity
performance or PPA
FPGA deployment
formal proof of the A3 composition
arbitrary concurrency
liveness / fairness
unbounded correctness
external certification
```

The next milestone is **A4 — a synthesizable authority shim in front of the simulated command interface**. It must physically prevent command issue when the bounded authority token is absent, uncommitted, stale, or identity-mismatched, while preserving the A3 process-restart negative controls.
