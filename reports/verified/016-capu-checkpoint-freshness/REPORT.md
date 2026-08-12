# RESONANCE Verified Report #016

# CaPU v0.11 — Checkpoint Freshness / Anti-Rollback Boundary

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU head:** `2495b8ec669b836b7c4d487400fbd62352ce8aac`  
**Workflow:** `CaPU vCML Checkpoint v0.11`  
**GitHub Actions run:** `31580821379`

## Result

# **PASS — exact-anchor checkpoint freshness boundary verified**

CaPU v0.10 restored spent root-authorization references after reset, but treated the replay snapshot itself as trusted input. The next failure mode is rollback:

```text
newer replay snapshot exists
        ↓
controller resets
        ↓
older structurally valid snapshot is presented
        ↓
old spent-state could be forgotten
```

CaPU v0.11 inserts a checkpoint-freshness gate before v0.10 recovery.

With an external trusted anchor, restore is allowed only when the presented checkpoint identity matches the anchor exactly:

```text
checkpoint_trusted
&& snapshot_ref   == anchor_ref
&& snapshot_epoch == anchor_epoch
```

An older epoch, wrong checkpoint reference or untrusted checkpoint fails closed before the replay recovery gate can reopen.

## Why this matters

Recovery correctness is not only about reconstructing state. It is also about reconstructing the **right version** of state.

A stale snapshot may be internally well formed and still be unsafe if it omits already-consumed authority.

The new invariant is:

# **A STRUCTURALLY VALID RECOVERY SNAPSHOT MUST NOT BECOME AUTHORITATIVE IF IT IS OLDER THAN THE TRUSTED RECOVERY ANCHOR.**

## Exact-anchor policy

v0.11 deliberately does not accept any numerically newer checkpoint merely because its epoch is greater than the anchor.

The policy is stricter:

```text
anchor = (ref, epoch)
        ↓
accepted restore must equal
        ↓
(ref, epoch)
```

This prevents the hardware from treating an arbitrary larger counter value as proof of freshness.

## Deterministic composition trajectory

The executable RTL trajectory verifies:

1. reset starts with recovery closed;
2. stale checkpoint epoch is rollback-rejected;
3. same epoch with wrong checkpoint ref is rejected;
4. exact metadata without the trusted binding verdict is rejected;
5. the exact trusted checkpoint restores spent ref `A110`;
6. restored `A110` remains replay-rejected by the v0.10/v0.9 layers;
7. fresh `A120` may still retire through the existing causal STORE path;
8. recovery begins again and the external checkpoint anchor advances;
9. the previously valid checkpoint is now rollback-rejected;
10. the new exact checkpoint restores both spent refs;
11. without an external anchor, an empty cold start remains fail-closed until explicitly authorized.

Marker:

```text
CAPU_VCML_BRIDGE_V11_CHECKPOINT_PASS
```

## Bounded formal verification

The standalone checkpoint freshness guard was checked with SymbiYosys / Yosys / Z3.

Reduced formal instance:

```text
CHECKPOINT_REF_WIDTH   = 4
CHECKPOINT_EPOCH_WIDTH = 4
```

Safety:

```text
BMC depth = 16
DONE (PASS, rc=0)
```

Reachability:

```text
cover depth = 20
6 VCD witnesses
DONE (PASS, rc=0)
```

Witnesses cover:

- exact anchored restore acceptance;
- stale-epoch rollback rejection;
- same-epoch wrong-ref rejection;
- untrusted checkpoint rejection;
- explicit cold-start acceptance;
- unauthorized cold-start rejection.

## Primary bounded invariants

```text
ANCHORED_RESTORE_ACCEPT
    => CHECKPOINT_TRUSTED
    && SNAPSHOT_REF == ANCHOR_REF
    && SNAPSHOT_EPOCH == ANCHOR_EPOCH

SNAPSHOT_EPOCH < ANCHOR_EPOCH
    => ROLLBACK_DETECTED
    && NO_RESTORE_ACCEPT

SAME_EPOCH_WRONG_REF
    => NO_RESTORE_ACCEPT

UNTRUSTED_ANCHORED_CHECKPOINT
    => NO_RESTORE_ACCEPT

RECOVERY_BEGIN
    => NO_RESTORE_ACCEPT

COLD_START_ACCEPT
    => !ANCHOR_VALID
    && COLD_START_AUTHORIZED
    && REF == 0
    && EPOCH == 0
```

## Evidence

Executable evidence artifact:

- name: `capu-vcml-v11-checkpoint-evidence`
- artifact ID: `9135065535`
- ZIP SHA-256: `d74686470349b3835bb156d51744ae55bc6e55c1eb9bc916b6a0d7450295ea11`

Formal evidence artifact:

- name: `capu-vcml-v11-checkpoint-formal-evidence`
- artifact ID: `9135079466`
- ZIP SHA-256: `e5fc4dff0baf65552b632eb80a8ac28aae04504f1ca3c855498b1ef16668f8ff`

The formal workflow pins SymbiYosys revision:

`b1a1e98cba941ec8433f8dc27f416cd7bb7f14be`

## Layered interpretation

The recovery stack is now:

```text
external checkpoint anchor      ← v0.11
        ↓
checkpoint freshness gate
        ↓
replay-state restore            ← v0.10
        ↓
spent authorization replay guard← v0.9
        ↓
parent / GEN / SEAL / CTAG
        ↓
causal commit
        ↓
STORE + vCML retirement evidence
```

The new layer does not weaken the older layers; it decides whether a recovery snapshot is allowed to reach them.

## Interpretation boundary

This report does **not** prove or certify:

- cryptographic checkpoint authentication inside CaPU;
- signature, MAC, TPM, TEE, key, certificate or attestation verification;
- implementation of monotonic durable storage;
- persistence or correctness of the external checkpoint anchor;
- checkpoint generation or atomic checkpoint commit;
- journal durability or omission resistance;
- power-loss persistence implemented by the CaPU RTL itself;
- distributed or multi-controller recovery;
- complete processor / ISA / cache / coherence correctness;
- unbounded or parametric proof.

`checkpoint_trusted` and the external anchor remain explicit trusted inputs.

## Next discriminating boundary

The next useful experiment is not another comparison rule. It is a **checkpoint commit protocol**:

```text
causal + replay state
      ↓
checkpoint candidate
      ↓
integrity/authentication
      ↓
monotonic anchor commit
      ↓
checkpoint becomes recovery authority
```

That would move durability and anchor advancement from an external assumption into the causal state-transition protocol itself.

## Verdict

**CaPU v0.11 demonstrated, within its bounded prototype scope, that a stale, mismatched or untrusted checkpoint cannot reopen replay recovery when an external trusted anchor is present; only the exact anchored checkpoint passes to the existing v0.10 replay-state recovery path.**

---

**RESONANCE Verified Report #016**  
**Status:** Reproducible bounded hardware/formal result  
**Result:** PASS  
**Vulnerability claim:** No  
**External safety certification:** No
