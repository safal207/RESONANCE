# RESONANCE Verified Report #018

# CaPU v0.13 — Checkpoint Content Commitment Boundary

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU content head:** `5c69c997a30c872eee86137607feef816a98f289`  
**Workflow:** `CaPU vCML Checkpoint Content v0.13`  
**GitHub Actions run:** `31584426137`

## Result

# **PASS — bounded checkpoint-content commitment binding verified**

CaPU v0.12 established that persisted checkpoint bytes are not automatically recovery authority. v0.13 addresses the next missing binding:

> Does the authority commit refer to the same recovery content that is later restored?

The unsafe conceptual shortcut is:

```text
checkpoint ref + epoch committed
        ↓
assume arbitrary persisted recovery bytes belong to it
```

v0.13 instead composes:

```text
canonical finite replay snapshot
        ↓
off-path SHA-256 commitment
        ↓
PREPARE exact commitment
        ↓
PERSIST exact commitment
        ↓
ANCHOR COMMIT exact commitment
        ↓
anchored recovery verifies the same commitment
```

The central invariant is:

# **CHECKPOINT AUTHORITY ≠ CHECKPOINT CONTENT UNLESS THE SAME CONTENT COMMITMENT SURVIVES THE COMMIT / RECOVERY BOUNDARY**

## Canonical content commitment

The v0.13 reference encoder binds the finite replay-state snapshot currently restored by CaPU v0.10:

- checkpoint reference;
- checkpoint epoch;
- authorization-reference width;
- finite replay-slot count;
- semantic set of spent root-authorization references.

Spent refs are sorted before encoding because replay semantics treat them as a set. The representation is domain-separated as `CaPU-vCML-checkpoint-content-v0.13` and hashed with SHA-256.

The deterministic reference tests verify:

- the same spent set in a different input order produces the same canonical commitment;
- changing a spent authorization ref changes the commitment;
- changing checkpoint ref or epoch changes the commitment;
- malformed / duplicate replay snapshots are rejected;
- exact digest verification succeeds and mismatched verification fails.

SHA-256 is intentionally computed **outside** the RTL critical path.

## Hardware binding

The v0.13 RTL adapter maps the already exact-bound v0.12 state-tag channel to an explicit checkpoint commitment ABI.

A candidate reaches checkpoint prepare only when its external commitment verdict is accepted and the commitment is non-zero.

```text
PREPARE_ACCEPT
=> candidate_commitment_verified
&& candidate_commitment != 0
```

Persistence must echo the exact prepared commitment:

```text
PERSIST_ACCEPT
=> persisted_commitment == request_commitment
```

Checkpoint authority commit must carry the exact same candidate commitment:

```text
CHECKPOINT_COMMIT_EVENT
=> ack_commitment == request_commitment
```

When an existing authoritative anchor is used for a compare-and-swap transition, the request also carries the exact base-anchor commitment.

## Anchored recovery

An anchored restore is allowed to reach the existing replay-state recovery path only when the presented recovery content commitment has passed the off-path verifier and exactly equals the authoritative anchor commitment:

```text
ANCHORED_RESTORE_ACCEPT
=> commitment_verified
&& snapshot_commitment != 0
&& anchor_commitment != 0
&& snapshot_commitment == anchor_commitment
```

Therefore an unverified or mismatched commitment fails closed before replay recovery can reopen.

The unanchored cold-start path is outside this v0.13 content-binding claim.

## Deterministic trajectory

The final executable trajectory demonstrates:

- unverified candidate rejection;
- verified commitment preparation;
- wrong persistence commitment rejection;
- exact persistence commitment acceptance;
- wrong anchor acknowledgement commitment rejection;
- exact checkpoint authority commit;
- unverified anchored restore rejection;
- mismatched anchored commitment rejection;
- exact anchored replay-state restore;
- fail-closed behavior when the off-path verifier rejects tampered recovery content;
- a second checkpoint whose CAS transition binds the old commitment as base and the new commitment as candidate.

Marker:

`CAPU_VCML_CHECKPOINT_CONTENT_V13_PASS`

The separate canonical reference suite ends with:

`VCML_CHECKPOINT_COMMITMENT_V13_PASS`

## Bounded formal result

The final bounded proof used:

- Yosys `0.33`;
- Z3 `4.8.12`;
- pinned SBY `b1a1e98cba941ec8433f8dc27f416cd7bb7f14be`;
- safety depth `16`;
- cover depth `20`;
- reduced formal instance: authorization ref width `4`, replay slots `2`, checkpoint ref width `3`, checkpoint epoch width `3`, commitment width `4`.

Safety result:

`DONE (PASS, rc=0)`

Cover result:

`DONE (PASS, rc=0)`

The solver emitted **4 VCD witness files** covering the successful and fail-closed reachability conditions.

Primary formal invariants:

```text
ANCHORED_RESTORE_ACCEPT
=> COMMITMENT_VERIFIED
&& SNAPSHOT_COMMITMENT == ANCHOR_COMMITMENT

UNVERIFIED_OR_MISMATCHED_ANCHORED_COMMITMENT
=> NO_RESTORE_ACCEPT

PREPARE_ACCEPT
=> CANDIDATE_COMMITMENT_VERIFIED
&& CANDIDATE_COMMITMENT != 0

PERSIST_ACCEPT
=> PERSISTED_COMMITMENT == REQUEST_COMMITMENT

CHECKPOINT_COMMIT_EVENT
=> ACK_COMMITMENT == REQUEST_COMMITMENT

ANCHOR_COMMIT_REQUEST
=> REQUEST_COMMITMENT != 0
```

## Evidence

Executable evidence:

- artifact: `capu-vcml-v13-checkpoint-content-evidence`
- artifact ID: `9136482452`
- ZIP SHA-256: `96e782266fc0ceff4961afa5f9efe3157e0c4b3b1d7d1867c8eed5149cee5827`

Formal evidence:

- artifact: `capu-vcml-v13-checkpoint-content-formal-evidence`
- artifact ID: `9136522097`
- ZIP SHA-256: `117cd96a67f088ff4fbcda35d8aab8588c5e051e500988cae679c2ba57acfd7f`

Formal evidence hashes:

- formal input SHA-256: `372a43625956a5812e1d645119aa0810de1ce219f4860020c7e8f11cef5390f3`
- safety log SHA-256: `3ce9e657b35b76c1c18ef399a5ae3c1bb298230e80ec701e3e03c51ec2717476`
- cover log SHA-256: `50be06ba8d7d49d0726c7dbd222eacb90cde481629d274cc78831a4c2fe6d0e5`

## Claim boundary

This report does **not** claim that:

- SHA-256 is implemented or formally verified inside CaPU RTL;
- the external commitment engine/verifier is trustworthy or uncompromised;
- the source vCML history is complete or omission-resistant;
- the checkpoint currently commits the full CaPU architectural causal state;
- causal head, GEN and SEAL are currently included in the canonical checkpoint payload;
- durable-media or crash-consistent storage internals are correct;
- external anchor CAS correctness is proven;
- signatures, MACs, TPMs, TEEs or key management are implemented;
- the full CPU is proven;
- the proof is unbounded or parametric across the full-width system.

The narrow result is:

> **Given a trustworthy off-path canonical commitment verdict and the existing v0.12 checkpoint-authority protocol, the finite replay-state checkpoint commitment cannot be silently changed between candidate admission, persistence acknowledgement, authority commit and anchored recovery.**
