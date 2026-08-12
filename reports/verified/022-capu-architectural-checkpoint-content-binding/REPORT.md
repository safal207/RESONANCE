# RESONANCE Verified Report #022

# CaPU v0.17 — Architectural Checkpoint Content Binding

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#70`  
**Verified CaPU content head:** `d627b4d15e26bcda5ce2f0803db05fa8e750e9c2`  
**Workflow:** `CaPU vCML Architectural Checkpoint Binding v0.17`  
**GitHub Actions run:** `31618001622`

## Result

# **PASS — complete architectural + causal checkpoint content binding verified in the bounded model**

v0.16 proved that a minimal architectural execution context and the already-recovered causal/replay state can become live under one accepted recovery epoch.

v0.17 closes the upstream authority gap left by that result:

> Are the actual architectural bytes themselves part of the same checkpoint commitment as the causal and replay state, so that equal recovery epochs cannot be used to compose unrelated snapshots?

The authoritative record now includes:

```text
checkpoint ref + checkpoint epoch
+ recovery epoch
+ PC + GPR0..GPR3 + status
+ causal head + GEN + SEAL
+ canonical spent-authorization set
        ↓
one domain-separated canonical payload
        ↓
one SHA-256 commitment
        ↓
PREPARE → PERSIST → ANCHOR AUTHORITY → EXACT RESTORE
```

Central result:

# **ARCHITECTURAL, CAUSAL AND REPLAY BYTES MUST BELONG TO ONE EXACT COMMITTED CHECKPOINT RECORD**

## Same-epoch architectural substitution

The primary v0.17 threat is stronger than the epoch mismatch handled by v0.16:

```text
valid causal/replay snapshot A
+
valid architectural snapshot B
+
matching/copied recovery epoch
=
REJECT
```

The recovery epoch remains part of the record, but equality of epoch labels is no longer sufficient. `PC`, all four GPRs, status, causal head, GEN, SEAL and the finite spent-authorization set are all content-bound to the same commitment.

Mutation tests confirm that changing any of those authoritative fields changes the canonical SHA-256 digest.

## Authority lifecycle

The complete payload is preserved through each checkpoint authority transition:

```text
PREPARE_ACCEPT
  => CANDIDATE_PAYLOAD == AUTHORITATIVE_LIVE_PAYLOAD

PERSIST_ACCEPT
  => PERSISTED_PAYLOAD == REQUEST_PAYLOAD

AUTHORITY_COMMIT
  => ACK_PAYLOAD == REQUEST_PAYLOAD

RESTORE_ACCEPT
  => VERIFIED_SNAPSHOT_PAYLOAD == ANCHOR_PAYLOAD

MIXED_SNAPSHOT
  => NO_RESTORE_ACCEPT
```

Recovery and every restore attempt are authority barriers. They block overlapping prepare/persist/commit activity and discard an older pending/durable candidate.

This closes a real boundary discovered during the audit: a candidate prepared against an earlier live state must not remain pending and later acquire authority after recovery or restore has changed the world it described.

## Deterministic and canonical verification

The deterministic path exercises complete-payload mutation across prepare, persistence, authority commit and restore, plus exact acceptance.

The canonical test digest is:

```text
fd768d0de2d11af63765e2d21e1beeda70979c9f0a31baa00f06debc208ee4d1
```

The tests verify digest changes for:

- PC;
- each GPR;
- status;
- recovery epoch;
- causal head transition ID;
- GEN;
- SEAL;
- replay spent-authorization set.

A valid causal state mixed with a foreign architectural state fails verification under the original commitment.

## Formal verification

Exact-head workflow:

- run `31618001622`;
- deterministic/canonical job `94185501677` — **success**;
- bounded formal job `94185608852` — **success**.

Safety:

```text
depth: 24
solver: Z3
DONE (PASS, rc=0)
```

Reachability:

```text
cover depth: 28
VCD witness files: 5
DONE (PASS, rc=0)
```

The same workflow also reran the v0.16 deterministic and bounded-safety paths successfully.

Pinned formal input hash:

```text
8f09087bb2d1f72c0ba0b1e4e748267fb2043619493b06f78f360881e9aaf61c
```

Formal log hashes:

```text
safety:
99ae1b1a4f2cbb8be7ae19d9c01bc37b70fa122a1254857a49f7b45cd854dc18

cover:
e2d927c448ad4d131c7644bec4e1e90bd4ec1ddb061345d0b80b8a5dde13ebe5

v0.16 safety regression:
378904e96faa11bfc11d368b5c585b77939c3949d8129c9182ff0fe3f156fdfa
```

Evidence artifacts:

```text
capu-vcml-v17-arch-checkpoint-evidence
artifact ID: 9150053641
ZIP SHA-256: bf1dd140809d42526170cd46111c3d59863ca6d234a145118d0786110119cf3f

capu-vcml-v17-arch-checkpoint-formal-evidence
artifact ID: 9150143252
ZIP SHA-256: 84ba71cec3671adc309ab73f27e0df14f9a58b7ab574a8281069a272a32ec425
```

## Exact-head regression status

On `d627b4d15e26bcda5ce2f0803db05fa8e750e9c2`, these registered pull-request workflows completed successfully:

```text
CaPU vCML Architectural Checkpoint Binding v0.17
CaPU vCML Architectural Causal Resume v0.16
CaPU Core v0 RTL Smoke
Validate Examples
```

The v0.17 workflow itself contains the v0.16 deterministic and bounded-safety regression paths.

## Formal-driven development note

Formal first exposed an over-constrained genesis base-anchor shadow assertion: when `base_anchor_valid=0`, bytes for a nonexistent base payload have no authority semantics. The equality requirement was narrowed to the valid-base case without weakening binding of the actual candidate/full payload.

A later audit then closed the real recovery-boundary authority issue described above: pending checkpoint authority is discarded on recovery or restore, so stale pre-boundary bytes cannot become authoritative later.

## Claim boundary

v0.17 is a **bounded reduced-width checkpoint-content binding result**. SHA-256 calculation and commitment verification are trusted off-path; the result does not implement or prove SHA-256 inside RTL.

It also does not establish:

- full ISA or production-width register-file recovery;
- complete CSR state;
- precise exception or interrupt recovery;
- privilege-state recovery;
- MMU/TLB or page-fault recovery;
- cache/coherence/multicore recovery;
- durable-media correctness;
- verifier trustworthiness;
- unbounded or parametric correctness.

The verified result is: **the bounded minimal architectural state introduced in v0.16 is now cryptographically content-bound, off-path, to the same authoritative checkpoint record as recovery epoch, causal head/GEN/SEAL and replay spent-state; mixed architectural/causal snapshots cannot pass the exact committed checkpoint authority merely by sharing an epoch.**

## Why this matters

v0.16 answered: **can architectural and causal execution resume together under one recovery epoch?**  
v0.17 answers: **are those exact bytes themselves the bytes the checkpoint authority committed to?**

The next architectural boundary is therefore not another content-binding patch. It is the control state that changes *how* execution is legally resumed: privilege mode, exceptions, interrupts and trap return context.
