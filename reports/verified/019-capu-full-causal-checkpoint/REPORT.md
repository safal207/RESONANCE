# RESONANCE Verified Report #019

# CaPU v0.14 — Full Causal Checkpoint State Binding

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU content head:** `604e8e437c1bc09058213e3c374e9b9fd8ce0c8e`  
**Workflow:** `CaPU vCML Full Causal Checkpoint v0.14`  
**GitHub Actions run:** `31587270416`

## Result

# **PASS — bounded full causal checkpoint-state binding verified**

CaPU v0.13 bound a canonical finite replay-state commitment across checkpoint prepare, persistence, authority commit and anchored recovery. v0.14 addresses the next missing state boundary:

> Does the checkpoint bind the committed causal position of the processor, or only the replay guard state?

v0.14 extends the checkpoint content to include:

- finite spent root-authorization references;
- `causal_head_valid`;
- `causal_head_transition_id`;
- committed 4-bit `GEN`;
- committed `SEAL` / `sealed_chain`;
- checkpoint identity.

The resulting chain is:

```text
replay spent-set
        +
committed causal head
        +
committed GEN
        +
committed SEAL
        ↓
canonical full causal checkpoint snapshot
        ↓
off-path SHA-256 commitment
        ↓
PREPARE exact committed state
        ↓
PERSIST exact state
        ↓
ANCHOR COMMIT exact state
        ↓
RESET / RECOVERY
        ↓
verify exact commitment + exact causal state
        ↓
recovered causal checkpoint record
```

Central invariant:

# **CHECKPOINT AUTHORITY ≠ FULL CAUSAL STATE UNLESS THE SAME COMMITTED CAUSAL STATE SURVIVES PREPARE → PERSIST → AUTHORITY COMMIT → RECOVERY**

## Canonical content model

The v0.14 reference encoder is `tools/vcml_causal_checkpoint_v14.py` in CaPU.

The canonical commitment is SHA-256 computed outside the RTL critical path. It binds the finite replay spent-set together with the explicit committed causal-head state.

The reference tests verify:

- equivalent spent-ref set ordering produces the same digest;
- changing the causal head changes the digest;
- changing committed GEN changes the digest;
- changing SEAL changes the digest;
- changing the replay spent-set changes the digest;
- speculative/buffered fields are rejected rather than silently included;
- malformed empty causal-state encodings fail closed.

Speculative state is therefore outside the checkpoint contract by construction.

## Hardware state binding

The v0.14 RTL layer wraps the already verified v0.13 commitment lifecycle and adds explicit causal-state equality checks.

### Prepare

```text
PREPARE_ACCEPT
=> CANDIDATE_CAUSAL_STATE == COMMITTED_CAUSAL_STATE
```

A checkpoint candidate cannot describe a different head, GEN or SEAL than the current authoritative committed state.

### Persistence

```text
PERSIST_ACCEPT
=> PERSISTED_CAUSAL_STATE == REQUEST_CAUSAL_STATE
```

A correct checkpoint reference or commitment cannot compensate for changed causal metadata.

### Authority commit

```text
CHECKPOINT_COMMIT_EVENT
=> ACK_CAUSAL_STATE == REQUEST_CAUSAL_STATE
```

The external anchor acknowledgement must preserve the pending checkpoint causal state and its base-anchor causal metadata.

### Recovery

```text
ANCHORED_RESTORE_ACCEPT
=> SNAPSHOT_COMMITMENT == ANCHOR_COMMITMENT
&& SNAPSHOT_CAUSAL_STATE == ANCHOR_CAUSAL_STATE
```

The accepted restore emits an explicit recovered record containing causal-head validity, transition ID, GEN and SEAL while the existing v0.10 recovery layer restores the finite spent-authorization set.

## Deterministic trajectory

The executable v0.14 trajectory passes the following independent failure points:

```text
wrong causal head at PREPARE       → reject
changed GEN at persistence         → reject
changed SEAL at anchor ACK         → reject
exact authority commit             → accept
wrong causal state during restore  → reject
exact full-state restore           → accept
```

The exact restore reproduced:

```text
causal head = 0x2201
GEN         = 6
SEAL        = 0
spent refs  = 1
```

Marker: `CAPU_VCML_CHECKPOINT_FULL_STATE_V14_PASS`.

## Formal verification

Final documented-head workflow:

- run `31587270416`;
- RTL/composition job `94083890867` — **success**;
- bounded formal job `94083964805` — **success**.

Safety:

```text
depth: 16
solver: Z3
Yosys: 0.33
SBY: b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
DONE (PASS, rc=0)
```

Reachability:

```text
cover depth: 20
VCD witnesses: 6
DONE (PASS, rc=0)
```

The cover witnesses make successful commit/recovery and multiple mismatch-rejection paths non-vacuous.

Formal hashes:

```text
formal input SHA-256:
51eb509935488ccd082ffa05564bed1df7a37306ce2d7132fb3cc5db6517bd1f

safety log SHA-256:
767ad83379cf46c41e1e49073e19eb6975d963e894474ccc478b75e95360545a

cover log SHA-256:
fdba25c06f29489f342a228080382566e58d1583ba5d38b7ccdde74451496d00
```

Evidence artifacts:

```text
capu-vcml-v14-full-causal-state-evidence
artifact ID: 9137624035
ZIP SHA-256: 45de55d34cb3a7a58498c99a1764eeb0726dc0c726164f8967f5c863e20d6400

capu-vcml-v14-full-causal-state-formal-evidence
artifact ID: 9137691431
ZIP SHA-256: 8704431b8d4c3c031d168979a98f57dd80cdbac412ddc86ea20d75c3ad1348f3
```

## Claim boundary

This result is deliberately narrow.

v0.14 does **not** establish:

- complete CPU architectural-state checkpointing;
- cache, predictor, register-file, ISA or coherence recovery;
- cryptographic SHA-256 implementation or verification inside RTL;
- correctness of the trusted off-path commitment engine;
- durable-media correctness;
- correctness of the external monotonic/CAS anchor;
- source-history omission resistance;
- distributed checkpoint consensus;
- unbounded or parametric verification.

Most importantly, **the recovered causal checkpoint record is not yet wired back into the live v0.9 parent / GEN / SEAL continuation controller after reset**.

The verified result is checkpoint construction, exact state binding and recovery of the causal record. Live causal execution resumption is a separate boundary.

## Why this matters

v0.10 answered: **which root authorizations were already spent?**  
v0.11 answered: **which recovery checkpoint is current?**  
v0.12 answered: **when does a checkpoint become recovery authority?**  
v0.13 answered: **which replay-state bytes does that authority refer to?**  
v0.14 now answers: **which committed causal position does that checkpoint represent?**

The next missing question is whether the recovered causal state can safely become the live continuation state after reset without creating a new causal history by accident.
