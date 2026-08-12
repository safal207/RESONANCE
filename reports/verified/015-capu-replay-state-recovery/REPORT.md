# RESONANCE Verified Report #015

# CaPU v0.10 — Replay-State Recovery Across Reset

**Domain:** Trust & Verification / Agent Infrastructure / Hardware Semantics  
**Project:** `safal207/CaPU`  
**CaPU pull request:** `#69`  
**Verified CaPU head:** `54e8d1ac78eda47c5a6ee0c11ba3835955a92c92`  
**Recovery workflow:** `CaPU vCML Recovery v0.10`  
**GitHub Actions run:** `31574359848`

## Result

# **PASS — bounded replay-state recovery boundary verified**

CaPU v0.9 already prevented reuse of a consumed root authorization reference within one volatile controller lifetime. The unresolved failure mode was reset:

```text
spent authorization ref
        ↓
hardware reset
        ↓
volatile spent-set disappears
        ↓
old ref could look fresh again
```

CaPU v0.10 adds an explicit fail-closed recovery state so reset does not silently erase the semantic fact that an authorization was previously consumed.

The recovery trajectory is:

```text
RESET / RECOVERY_BEGIN
        ↓
recovery_ready = 0
        ↓
NEW ROOT AUTHORIZATION FAILS CLOSED
        ↓
trusted CMC / vCML replay snapshot
        ↓
structural validation
        ↓
restore accepted
        ↓
recovery_ready = 1
        ↓
restored spent refs remain rejected
fresh refs may enter the existing causal path
```

## Why this matters

A permission system that remembers only live in-memory state can become weaker after restart.

For agent infrastructure, programmable wallets, payment controls, delegated authority and other consequential systems, the semantic invariant is not merely:

```text
authorization_ref was spent before reset
```

It is:

# **A CONSUMED AUTHORIZATION MUST NOT BECOME FRESH MERELY BECAUSE THE CONTROLLER RESTARTED.**

v0.10 makes that recovery boundary explicit.

## Deterministic trajectory

The executable RTL / software path verifies:

1. reset starts fail-closed;
2. root admission before restore is rejected;
3. an explicit empty cold-start snapshot may open a new replay window;
4. authorization ref `A110` retires and becomes spent;
5. reset clears volatile RAM and closes the recovery gate;
6. `A110` is rejected during the recovery gap;
7. snapshot `{A110}` is restored;
8. restored `A110` remains a replay and is rejected;
9. fresh `A120` may retire and joins the recovered spent set;
10. malformed duplicate snapshot `{A110, A110}` is rejected;
11. valid snapshot `{A110, A120}` is accepted;
12. restored `A120` remains rejected;
13. a restore attempt over live recovered state is rejected rather than silently erasing replay history.

Expected executable marker:

```text
CAPU_VCML_BRIDGE_V10_RECOVERY_PASS
```

## Formal verification

The standalone replay recovery guard was checked with SymbiYosys / Yosys / Z3 using a reduced-width bounded instance.

```text
AUTHORIZATION_REF_WIDTH = 4
SPENT_AUTHORIZATION_SLOTS = 4
Safety BMC depth = 20
Cover depth = 24
Solver = Z3
Yosys = 0.33
Z3 = 4.8.12
Pinned SBY = b1a1e98cba941ec8433f8dc27f416cd7bb7f14be
```

Observed workflow gates:

```text
Safety: DONE (PASS, rc=0)
Cover:  DONE (PASS, rc=0)
Cover witnesses: 5
```

Primary bounded invariants:

```text
RECOVERY_NOT_READY
    => NO_ROOT_AUTHORIZATION_ACCEPT

RESTORE_ACCEPT
    => SNAPSHOT_WELL_FORMED
    && !RECOVERY_READY

MALFORMED_SNAPSHOT
    => NO_RESTORE_ACCEPT

RESTORED_SPENT_REF
    => NO_ROOT_AUTHORIZATION_ACCEPT

RECOVERY_BEGIN
    => NEXT_STATE_NOT_READY_AND_EMPTY_LOCAL_SET

LIVE_RECOVERY_STATE + RESTORE_VALID
    => RESTORE_REJECTED

AUTHORIZATION_CAPACITY_EXHAUSTED
    => NO_FRESH_ROOT_ACCEPT
```

Formal input SHA-256:

`a5a1ab60af021f76f93216a6243adfd9d5fc7415032d77eae74d7cc3545a776e`

## Evidence

Executable recovery artifact:

- artifact ID: `9132556770`
- ZIP SHA-256: `4081d092c2baaf0667a01e621a4c2040a5fd85b0ceaaa6e14247afcd05033b74`

Formal recovery artifact:

- artifact ID: `9132595097`
- ZIP SHA-256: `60319783a2a2fc322d5614e51678c49d5c2a7d286140d5b8de15d2656896bdac`

On the same verified CaPU head, the pre-existing repository checks also completed successfully, including the v0.9 causal / one-shot authorization baseline, Core RTL smoke tests and example validation.

## Causal interpretation

The useful architecture split is:

```text
v0.9
consume authorization once during a live controller lifetime
        ↓
v0.10
recover the consumed-reference state after reset
        ↓
future boundary
authenticate freshness and rollback-resistance of the recovered checkpoint
```

This is a concrete example of the broader RESONANCE verification model:

```text
state
→ cause
→ phase
→ transition
→ time
→ recovery
→ verification
→ evidence
```

The recovery phase is not an afterthought. It is part of the legitimacy of the state transition itself.

## Interpretation boundary

This result is deliberately narrow.

CaPU v0.10 does **not** prove or certify:

- nonvolatile hardware persistence;
- autonomous power-loss recovery;
- cryptographic authentication of the restore snapshot;
- snapshot freshness;
- rollback resistance;
- issuer identity or capability authenticity;
- distributed or multi-controller replay recovery;
- unbounded replay history;
- a complete CPU, ISA, cache or coherence implementation;
- production readiness or external safety certification.

The restore snapshot remains trusted upstream input with structural validation. The formal proof covers the finite recovery guard in its stated bounded configuration.

## Next discriminating step

The next meaningful boundary is not “more tests” of the same reset trajectory. It is an authenticated checkpoint contract:

```text
snapshot_id
+ monotonic recovery epoch
+ integrity / authenticity
+ rollback rejection
```

That would move the claim from **recoverable replay state** toward **provably fresh recovery state**.

## Verdict

**CaPU v0.10 demonstrates, under a bounded and explicitly scoped hardware model, that reset can be made fail-closed for root authorization replay: previously consumed authorization references are restored from a replay snapshot and remain rejected after recovery, while fresh references may proceed through the existing causal commit path.**

---

**RESONANCE Verified Report #015**  
**Status:** Verified bounded recovery boundary  
**Result:** PASS  
**Vulnerability claim:** No  
**Production certification:** No  
**External safety certification:** No
