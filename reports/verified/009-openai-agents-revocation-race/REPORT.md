# RESONANCE Verified Report #009

# OpenAI Agents SDK — Revocation Race / TOCTOU

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Revocation Race / TOCTOU v0.9  
**Executed:** 2026-08-11T04:38:45Z  
**GitHub Actions run:** `31459107395`  
**Evidence artifact:** `resonance-openai-agents-revocation-race-v0.9`  
**Artifact digest:** `sha256:97e81a88b3ad67e5ea8f42a1b0b5241afd67a2de516a99db58c6871be98d7485`

## Result

# **10 / 10 — Execution-bound trust preconditions**

**Classification: execution-bound trust precondition protocol passes**

Report #008 established that a stale trust registry cannot safely authorize action. Report #009 moves the race closer to the side effect: **what if trust is fresh and the key is active when checked, but the key is revoked after verification and before commit?**

That is a classic time-of-check / time-of-use boundary.

```text
T0  verify authority → ACTIVE / trust_epoch=41
T1  authority revoked → trust_epoch=42
T2  irreversible commit attempted
```

The experiment compares reusing the old authorization with two safer approaches: binding commit to the verified trust epoch, and re-verifying authority at commit time.

## Comparative result

| Scenario | Execution decision | Final effects |
|---|---|---:|
| Unsafe TOCTOU | verified ACTIVE at epoch 41 → revoked → blind retry | **2** |
| Epoch-bound commit | expected epoch 41, current epoch 42 → precondition failed | **1** |
| Commit-time re-verification | current epoch 42, key inactive → retry blocked | **1** |
| Control: unchanged trust | first timeout before commit + epoch 41 unchanged → retry allowed | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe TOCTOU duplicate reproduced | PASS | 2/2 |
| Epoch-bound commit blocks revocation race | PASS | 2/2 |
| Commit-time re-verification sees revocation | PASS | 2/2 |
| Unchanged epoch allows required retry | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — a correct check can become wrong before use

The first synthetic side effect committed and then lost its response. The application verified `primary-v1` while the key was still active:

```text
key_active  = true
trust_epoch = 41
verified_at = T0
```

The benchmark then revoked the key and advanced trust state to epoch 42 before the retry executed.

The unsafe path reused the earlier authorization without testing whether its precondition still held:

```text
commit #1
response lost
verify ACTIVE / epoch 41
revocation / epoch 42
reuse old decision
retry
commit #2
```

Final effect count: **2**.

The verification itself was not false. It simply stopped being current before it was used.

## Scenario 2 — bind authorization to the state it verified

The safe path carried `expected_trust_epoch=41` into the retry operation.

At execution:

```text
expected_trust_epoch = 41
current_trust_epoch  = 42
epoch_matches         = false
key_active_at_commit  = false
allowed               = false
```

The commit returned a synthetic precondition failure before another side effect occurred.

Final effect count: **1**.

This is structurally similar to optimistic concurrency control: the action is allowed only while the state version used to authorize it is still current.

## Scenario 3 — re-verification also closes the race

A second safe trajectory did not rely on the old decision. It checked authority again at the synthetic commit time:

```text
trust_epoch = 42
key_active  = false
```

Retry remained blocked. Final effect count: **1**.

Version binding and commit-time re-verification are different implementation strategies for the same rule: **the authorization precondition must hold when the irreversible transition executes.**

## Scenario 4 — safe checks must still permit legitimate progress

A control path made the first request time out **before** any commit. It then verified the current `primary-v2` key at epoch 41. No trust mutation occurred between verification and execution.

At conditional retry:

```text
expected_trust_epoch = 41
current_trust_epoch  = 41
epoch_matches         = true
key_active_at_commit  = true
allowed               = true
```

Exactly one side effect committed.

This matters because a safety protocol that only blocks is incomplete. A useful protocol must reject stale authorization while still permitting a valid transition when its preconditions remain true.

## The TOCTOU invariant

# **VERIFIED THEN ≠ AUTHORIZED NOW**

A safe action path becomes:

```text
verify authority
   ↓
issue decision bound to trust state/version
   ↓
prepare irreversible transition
   ↓
validate same precondition at commit
   ├─ unchanged → execute
   └─ changed   → abort / re-verify
```

The forbidden edge is:

```text
VERIFIED(epoch=N)
      ↓
trust state changes
      ↓
COMMIT using epoch=N   ← illegal
```

unless the action is otherwise provably safe under the new state.

## Trust decisions become versioned objects

Reports #007 and #008 established authority lifecycle and trust-state freshness. Report #009 adds **execution binding**:

```text
Trust decision =
  authority
+ evidence state
+ trust state
+ trust version / epoch
+ verification time
+ execution precondition
```

Useful distinctions now include:

```text
ACTIVE AT CHECK       ≠ ACTIVE AT COMMIT
FRESH SNAPSHOT        ≠ IMMUTABLE SNAPSHOT
VERIFIED DECISION     ≠ PERMANENT PERMISSION
CHECK PASSED          ≠ COMMIT PRECONDITION HOLDS
AUTHORIZATION         ≠ UNVERSIONED BOOLEAN
```

## Why this matters

Agent workflows can separate planning, approval, tool preparation and external commit by seconds or minutes. During that interval permissions can be revoked, policy can change, ownership can transfer, limits can be consumed, or another actor can mutate the state that made the action legal.

The failure therefore crosses several RESONANCE coordinates at once:

```text
STATE
  ↕
TIME (τ)
  ↕
TRANSITION
  ↕
EVIDENCE
  ↕
VERIFICATION
```

The crucial property is not only that a check happened. It is that the checked preconditions remained valid across the transition boundary.

## Important boundary

This benchmark uses synthetic in-memory trust epochs, deterministic revocation and local side effects. It does **not** test or certify:

- production IAM systems;
- distributed transactions;
- database compare-and-swap implementations;
- real certificate or token revocation;
- production authorization leases;
- cryptographic capability systems;
- arbitrary applications built with the SDK.

The epoch mechanism is a benchmark model for a versioned precondition, not a universal implementation prescription.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop executed all deterministic trajectories using the upstream `FakeModel`.

The SDK did not automatically bind application authorization to a trust epoch, and this report does not claim that it should impose a universal policy. The measured property is an **application-level execution-time authorization protocol** layered on top of framework primitives.

No live model, production API key, real credential or external side-effecting service was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-revocation-race-v0.9/run_revocation_race.py`

Workflow:

`.github/workflows/benchmark-openai-agents-revocation-race.yml`

Machine-readable result:

`reports/verified/009-openai-agents-revocation-race/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31459107395`

## Verdict

**The benchmark reproduced a duplicate side effect when an authorization that was correct at verification time was reused after revocation. Binding execution to the verified trust epoch — or re-verifying at commit time — prevented the unsafe transition while still allowing a required retry when trust state remained unchanged.**

The RESONANCE rule now becomes:

# **preserve UNKNOWN; preserve CONFLICT; verify AUTHORITY; verify authority TIME; verify TRUST STATE freshness; bind verification to EXECUTION; act only while the verified preconditions still hold**

---

**RESONANCE Verified Report #009**  
**Status:** Reproducible revocation-race run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Epoch mismatch blocked:** Yes  
**Commit-time revocation detected:** Yes  
**Legitimate unchanged-state retry allowed:** Yes  
**Vulnerability claim:** No  
**External safety certification:** No
