# RESONANCE Verified Report #046

# ASTRA–CaPU v1.0-A1 — Accelerator Effect Authority Interface

**Domain:** Trust & Verification / AI Accelerator Infrastructure / Execution Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#93`  
**Verified CaPU content head:** `41ffe240cc7be0be2e614cba590851f84a63e949`  
**Architecture base head:** `26790adb404686fc0e309ef165afbeb53e2caa5f`  
**Workflow:** `ASTRA-CaPU v1.0-A1 Effect Authority Interface`  
**GitHub Actions run:** `33179590650`

## Result

# **PASS — exact-head deterministic accelerator-effect authority contract verified**

A1 is the first executable slice of the ASTRA–CaPU v1 reference architecture. It does not claim a new tensor accelerator. It defines and tests the authority boundary that decides whether an accelerator command or DMA-like external effect may dispatch, retry, retire, and update trusted memory after a crash or ambiguous completion.

The exact authority identity is:

```text
queue_incarnation
+ queue_epoch
+ slot_id
+ command_id
+ attempt_id
+ effect_id
```

The authority record additionally binds:

```text
intent commitment
+ state commitment
+ policy commitment
+ checkpoint commitment
```

The central verified contract is:

```text
UNKNOWN
=> NO BLIND REPLAY
&& NO RETIRE
&& NO SUCCESS CLAIM
&& NO TRUSTED MEMORY UPDATE
```

Absence of completion evidence is not treated as evidence that an effect did not occur.

## Lifecycle

```text
PROPOSED
  -> GROUNDED
  -> AUTHORIZED
  -> COMMITTED
  -> DISPATCHED / UNKNOWN
      -> exact NOT_COMMITTED -> RECONCILED_NOT_COMMITTED -> next attempt
      -> exact COMMITTED     -> RECONCILED_COMMITTED     -> SEALED
      -> exact CONFLICT      -> CONFLICT / fail closed
```

## Exact-head verification

All registered pull-request workflows for the exact A1 content head passed:

```text
A1 workflow run:       33179590650  PASS
A1 deterministic job: 98877058541  PASS
Tests:                 12 / 12      PASS

Validate Examples:    33179590652  PASS
Validate job:         98877058380  PASS
```

No Core RTL workflow was expected or registered because A1 changes an implementation-neutral software contract, schema, fixtures, documentation and CI—not RTL.

## Verified adversarial cases

The executable suite verifies that:

- dispatch before durable commitment is rejected;
- an unresolved dispatched attempt remains `UNKNOWN` and cannot replay, retire or seal;
- foreign `authority_id` evidence is rejected;
- stale or foreign incarnation, epoch, slot, command, attempt or effect identity is rejected;
- exact durable `NOT_COMMITTED` evidence authorizes only the next attempt;
- evidence for an earlier attempt cannot resolve a newer attempt;
- `CONFLICT` remains fail closed;
- a stale checkpoint cannot override a newer durable issue witness;
- a stale checkpoint cannot override a durable completion receipt;
- cross-authority checkpoint/durable-record mixing is rejected;
- every authority-identity dimension and each intent/state/policy/checkpoint commitment affects the canonical SHA-256 digest.

## Executable artifacts

```text
tools/astra_capu_effect_authority_a1.py
tests/test_astra_capu_effect_authority_a1.py
schemas/hardware/astra-capu-effect-authority-v1.0-a1.schema.json
examples/hardware/astra-capu-v1-a1-valid.json
examples/hardware/astra-capu-v1-a1-adversarial.json
docs/hardware/ASTRA_CAPU_V1_A1_EFFECT_AUTHORITY_INTERFACE.md
.github/workflows/astra-capu-v1-a1-effect-authority.yml
```

## Sealed evidence

```text
artifact:
astra-capu-v1-a1-effect-authority-evidence

artifact ID:
9689108326

ZIP SHA256:
c5d956f5844d8fc5e954db9a607ededddfe85f086839dbad12e9f1c39846b24e
```

Exact file and log hashes:

```text
reference engine:
813a913035bae1e5ca358091dd3ce5c8e2e040d97e6dc2e0535282daf1c776a1

test suite:
8327abfde44b109e9c41c6de46a7b3ec18222f02ef1047874a07d405e3270fb7

JSON schema:
e7b18d94916ad5e1b9547c3775b882b0dfbe29fd0ea757732441b5ba92bef1cc

valid fixture:
e157fdc36633388895de9d3d9dce0efc93b71b755f38f12b4f7a6fdc95cc5cd1

adversarial fixture:
01b7ee05e572ddef56aa17fe9782d0a102aef983d17ab22c248d4feda1ac08d1

contract document:
25ecd54e07821231cceae358722f741223e4733002e580e6cca0682ef9571569

test log:
1d5c23a1d43587fc830222862d87f367c9c83b36aa1001cbffb9870d34af51a3
```

## Architectural significance

The verified v0.26–v0.33 line explored effect uncertainty, durable positive and negative evidence, partial and overlapping DMA recovery, concurrent queue ordering, slot reuse, epoch wrap and authority incarnation as separate bounded mechanisms.

A1 turns those mechanisms into one stable, implementation-neutral interface that can be targeted by:

```text
agent runtime adapter
accelerator command queue
DMA/effect controller
checkpoint recovery manager
outcome-evidence provider
proof-receipt consumer
```

This is the transition from a collection of research proofs toward a composable accelerator-facing contract.

## Claim boundary

This result verifies a deterministic software reference contract, canonical encoding, schema and adversarial fixtures on one exact Git head.

It does **not** claim:

```text
real GPU / TPU / NPU integration
synthesizable A1 controller
FPGA implementation
silicon performance or PPA
cryptographic evidence authenticity
production persistent storage
arbitrary queue depth or concurrency
liveness / fairness
formal RTL proof of the composed A1 contract
unbounded correctness
external certification
```

The next discriminating milestone is **A2 — synthetic accelerator command-queue and crash-injection benchmark**. It must demonstrate a concrete unsafe baseline that duplicates an ambiguous external effect or reports false success, while the A1 path preserves `UNKNOWN`, obtains discriminating evidence, and completes with zero duplicate effects.
