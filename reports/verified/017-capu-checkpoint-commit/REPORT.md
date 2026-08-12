# RESONANCE Verified Report #017

# CaPU v0.12 — Checkpoint Commit / Recovery Authority Creation

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU content head:** `ca64c3c7477e13dff64c0d3301f8a8d5a1364b06`  
**Workflow:** `CaPU vCML Checkpoint Commit v0.12`  
**GitHub Actions run:** `31582350253`

## Result

# **PASS — bounded persist-then-anchor checkpoint authority boundary verified**

CaPU v0.11 verified that recovery accepts only the exact externally anchored checkpoint. v0.12 addresses the complementary question:

> How does a new checkpoint become authoritative in the first place?

The unsafe conceptual shortcut is:

```text
checkpoint bytes written
        ↓
assume checkpoint authoritative
```

v0.12 instead models an explicit commit protocol:

```text
PREPARE checkpoint candidate
        ↓
PERSIST exact snapshot
        ↓
REQUEST external anchor compare-and-swap
        ↓
ACK exact base + candidate
        ↓
CHECKPOINT COMMIT EVENT
```

The central invariant is:

# **SNAPSHOT BYTES EXIST ≠ RECOVERY AUTHORITY COMMITTED**

A checkpoint becomes authoritative in the prototype only after the exact prepared snapshot has been acknowledged as persisted, the base anchor still matches the authoritative external anchor, and the external anchor boundary acknowledges the exact base-to-candidate update.

## Why this matters

Recovery metadata is consequential state. If a system treats any persisted snapshot as authoritative, a crash, stale writer, partial update or competing checkpoint creator can make the recovery path diverge from the state that was actually committed.

CaPU v0.12 separates three facts that are often collapsed:

```text
candidate exists
        !=
snapshot persisted
        !=
checkpoint authoritative
```

This mirrors the broader CaPU distinction between speculative/internal state and committed externally meaningful state.

## Commit protocol

### 1. Prepare

A checkpoint candidate is prepared against a latched view of the current external anchor.

The candidate must have:

- non-zero checkpoint reference;
- non-zero state-binding tag;
- exactly the next checkpoint epoch;
- no epoch wrap;
- no other pending candidate.

With no current anchor, the first checkpoint starts at epoch `1`.

With an existing anchor:

```text
candidate_epoch = current_anchor_epoch + 1
```

Skipped epochs fail closed.

### 2. Persist

The snapshot-persistence acknowledgement is accepted only when its checkpoint reference, epoch and state-binding tag exactly match the prepared candidate and the latched base anchor is still current.

A wrong persistence acknowledgement cannot set the candidate's `snapshot_durable` state.

### 3. Commit anchor

Only a durable candidate may request an update of the external recovery anchor.

The request carries both:

```text
expected base anchor
        +
new checkpoint candidate
```

The external boundary is expected to provide compare-and-swap or equivalent semantics. CaPU emits `checkpoint_commit_event` only when the acknowledgement exactly matches both the latched base and candidate.

An early or mismatched acknowledgement does not create recovery authority.

## Concurrent-writer fencing

A prepared candidate remembers the anchor it intended to replace.

If the external anchor changes before commit:

```text
latched base != current authoritative anchor
        ↓
STALE_BASE
        ↓
NO ANCHOR COMMIT REQUEST
        ↓
candidate discarded
```

This prevents a locally prepared checkpoint from silently committing over a concurrently advanced authority state in the modeled boundary.

## Abort semantics

Abort clears the pending local candidate and suppresses authority commit.

If the snapshot had already been persisted, an orphan snapshot may remain, but it is not authoritative because the external anchor was never committed to it.

Therefore:

# **PERSISTED SNAPSHOT + ABORT ⇒ NO CHECKPOINT AUTHORITY EVENT**

## Recovery composition

v0.12 composes the checkpoint commit protocol with the earlier recovery stack:

```text
checkpoint candidate / persistence / anchor commit   v0.12
                ↓
exact-anchor freshness / anti-rollback               v0.11
                ↓
replay-state restore across reset                    v0.10
                ↓
one-shot authorization replay guard                v0.9
                ↓
causal STORE retirement + vCML evidence
```

The v0.12 wrapper also binds recovery to an opaque checkpoint state tag carried by the authoritative external anchor. Equality is checked exactly, but the RTL does not compute a cryptographic digest or authenticate that tag.

## Deterministic trajectory

The executable v0.12 run reproduced and checked:

1. initial checkpoint `C001/epoch 1` prepared but not durable;
2. anchor acknowledgement before snapshot persistence rejected;
3. wrong persistence state tag rejected;
4. exact persistence acknowledgement opens the anchor-update request;
5. wrong external anchor acknowledgement rejected;
6. exact `C001/1` checkpoint commit succeeds;
7. the committed checkpoint restores spent authorization `A110`;
8. restored `A110` remains replay-rejected;
9. fresh `A120` still retires through the causal STORE path;
10. same checkpoint ref/epoch with a wrong state-binding tag is rejected;
11. concurrent external anchor advancement makes a prepared candidate stale;
12. skipped checkpoint epoch is rejected;
13. persisted candidate followed by abort leaves authority unchanged;
14. an exact non-empty-base update commits `C010/epoch 3`;
15. checkpoint epoch wrap is rejected fail-closed.

Marker:

`CAPU_VCML_BRIDGE_V12_CHECKPOINT_COMMIT_PASS`

## Bounded formal verification

The checkpoint commit controller was checked with:

```text
mode:          bounded safety
safety depth:  24
cover depth:   28
solver:        Z3 4.8.12
Yosys:         0.33
SBY revision:  b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
```

Literal safety result:

```text
DONE (PASS, rc=0)
```

Literal cover result:

```text
DONE (PASS, rc=0)
```

The cover run emitted five VCD witness traces. Six cover conditions are represented because two reachable conditions share one witness trajectory.

The reduced formal instance uses 3-bit checkpoint reference, epoch and state-tag fields.

## Formally checked invariants

```text
ANCHOR_COMMIT_REQUEST
  => CANDIDATE_PENDING
  && SNAPSHOT_DURABLE
  && BASE_STILL_CURRENT

STALE_BASE
  => NO_ANCHOR_COMMIT_REQUEST

CHECKPOINT_COMMIT_EVENT
  => EXACT_EXTERNAL_ACK
  && ANCHOR_COMMIT_REQUEST

NO_SNAPSHOT_PERSISTENCE
  => NO_ANCHOR_COMMIT_REQUEST

INVALID_OR_SKIPPED_EPOCH
  => NO_PREPARE_ACCEPT

EPOCH_EXHAUSTED
  => NO_PREPARE_ACCEPT

ABORT
  => NO_ANCHOR_COMMIT_REQUEST
  && NO_COMMIT_EVENT
```

## Evidence

Formal input SHA-256:

`15c524160dfa5e6dabdfe2fe067a6eab3067d0182431c066eb7177b60357cb23`

Final safety log SHA-256:

`0ce4200e1d341ca2410ba31d48b679cf6debe8451a33abd38fd512e4c038008d`

Final cover log SHA-256:

`54f0f36d036e21f50823cabbf02b71ff157b3bd93813e50cdeeaa0523ec4991c`

Executable evidence:

- artifact: `capu-vcml-v12-checkpoint-commit-evidence`
- artifact ID: `9135668015`
- ZIP SHA-256: `0e1c149d085b93e411cce1b737216227c8aab5e53b31d28c8372a96863502b17`

Formal evidence:

- artifact: `capu-vcml-v12-checkpoint-commit-formal-evidence`
- artifact ID: `9135695310`
- ZIP SHA-256: `0143c89396c9e3ce1091475133970f7a86013c12b97413bd56c93bc4d1b77371`

## Interpretation boundary

The current anchor, snapshot-persistence acknowledgement and external anchor compare-and-swap acknowledgement are trusted interface inputs in this prototype.

This report does **not** prove or certify:

- durable media correctness;
- cryptographic checkpoint authentication;
- correctness of the external compare-and-swap implementation;
- TPM, TEE, signature, MAC or attestation verification;
- checkpoint payload hashing inside hardware;
- filesystem, database or NVRAM crash consistency;
- distributed consensus or global multi-controller serialization;
- globally unique checkpoint identifiers;
- unbounded or parametric formal correctness;
- complete CPU, ISA, cache or coherence correctness;
- arbitrary agent or payment-system safety.

The bounded result verifies the explicit checkpoint-commit controller contract and deterministic composition trajectory only.

## Verdict

**In the bounded CaPU v0.12 prototype, checkpoint persistence alone does not create recovery authority. Authority is emitted only after an exact prepared candidate is durable, its base anchor remains current, and the external anchor boundary acknowledges the exact base-to-candidate transition; early acknowledgement, state mismatch, stale base, skipped epoch, abort and epoch wrap fail closed.**

---

**RESONANCE Verified Report #017**  
**Status:** Reproducible bounded checkpoint-commit run  
**Formal result:** PASS  
**Vulnerability claim:** No  
**External safety certification:** No
