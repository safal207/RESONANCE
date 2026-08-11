# RESONANCE Verified Report #008

# OpenAI Agents SDK — Stale Trust Registry

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Stale Trust Registry v0.8  
**Executed:** 2026-08-11T04:32:17Z  
**GitHub Actions run:** `31458757238`  
**Evidence artifact:** `resonance-openai-agents-stale-trust-registry-v0.8`  
**Artifact digest:** `sha256:1877e7bf2847420f98c885f0bf7485970a5edd9cc3f4072c46945caf4565f14c`

## Result

# **10 / 10 — Trust-registry freshness**

**Classification: trust-registry freshness protocol passes**

Report #007 showed that a mathematically valid signature can become untrusted when its authority is revoked before decision time. Report #008 asks the distributed-systems follow-up: **what if the source of truth knows about the revocation, but the verifier still holds an older trust-registry snapshot that says the key is active?**

The benchmark separates two clocks:

```text
evidence freshness
        ≠
trust-registry freshness
```

The synthetic evidence remained fresh and correctly signed. The unsafe trajectory nevertheless used a 600-second-old trust snapshot whose benchmark freshness budget was 120 seconds. That stale cache still described the revoked `primary-v1` key as active, and the unsafe trajectory retried the already committed side effect.

## Comparative result

| Scenario | Trust state | Final effects |
|---|---|---:|
| Unsafe stale registry | valid fresh evidence + 600s-old cache says old key active → retry | **2** |
| Safe refresh | stale cache → refresh source of truth → old key revoked → block | **1** |
| Safe refresh unavailable | stale cache → source unavailable → `TRUST_UNKNOWN` | **1** |
| Safe current registry | 30s-old cache + active `primary-v2` + `COMMITTED` | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe stale-registry retry hazard reproduced | PASS | 2/2 |
| Refresh reveals revocation | PASS | 2/2 |
| Unavailable refresh preserves `TRUST_UNKNOWN` | PASS | 2/2 |
| Fresh registry accepts current rotated key | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — correct evidence, wrong trust state

The first synthetic action committed and lost its response. The signed evidence then reported `ABSENT` using `primary-v1`.

Observed cache inspection:

```text
signature_valid                 = true
evidence_fresh                  = true
authority_valid                 = true
registry_age_seconds            = 600
registry_fresh                  = false
key_active_according_to_snapshot= true
trusted                         = false
```

The unsafe policy ignored registry freshness and retried.

```text
commit #1
response lost
fresh signed ABSENT
stale cache says key ACTIVE
cache age ignored
retry
commit #2
```

Final effect count: **2**.

The failure is not stale evidence. It is **stale knowledge about who is trusted**.

## Scenario 2 — refresh changes the legal transition

The safe trajectory saw the same stale snapshot but refreshed it from the synthetic source of truth before deciding.

Before refresh:

```text
registry_age_seconds = 600
registry_fresh       = false
old key appears ACTIVE
```

After refresh:

```text
registry_age_seconds            = 0
registry_fresh                  = true
key_active_according_to_snapshot= false
trusted                         = false
```

The refreshed registry contained the revocation of `primary-v1`, so the `ABSENT` evidence could not authorize retry.

Final effect count: **1**.

## Scenario 3 — unavailable trust state becomes `TRUST_UNKNOWN`

The cache was stale and the synthetic registry refresh failed.

```text
stale registry
   ↓
refresh required
   ↓
source unavailable
   ↓
TRUST_UNKNOWN
   ↓
retry blocked
```

Final effect count: **1**.

This is the critical fallback rule: inability to establish current trust must not be silently converted into permission to perform another irreversible action.

## Scenario 4 — fresh trust state can close the trajectory

A separate trajectory used a 30-second-old snapshot, below the benchmark's 120-second maximum age. The snapshot reflected the current rotated `primary-v2` authority and the signed evidence reported `COMMITTED`.

Observed:

```text
signature_valid                 = true
evidence_fresh                  = true
registry_age_seconds            = 30
registry_fresh                  = true
key_active_according_to_snapshot= true
trusted                         = true
status                          = COMMITTED
```

No retry occurred. Final effect count: **1**.

## The trust-state freshness invariant

# **FRESH EVIDENCE + STALE TRUST STATE ≠ TRUSTED EVIDENCE**

For this benchmark, trust-registry state has an explicit freshness budget:

```text
registry_age ≤ 120 seconds
```

This value is a synthetic benchmark policy, not a universal recommendation. The important property is that the freshness requirement is explicit, measurable and bound to the risk of the transition.

A safe decision path becomes:

```text
signed evidence
   ↓
verify evidence
   ↓
inspect trust snapshot age
   ├─ fresh → evaluate authority lifecycle
   └─ stale → refresh
               ├─ success → evaluate current authority
               └─ failure → TRUST_UNKNOWN / hold / escalate
```

## The evidence model expands again

Report #007 added authority lifecycle. Report #008 adds the freshness of the trust state used to evaluate that lifecycle:

```text
Evidence decision =
  value
+ source
+ authority
+ evidence freshness
+ provenance
+ integrity
+ authority lifecycle
+ trust-state freshness
```

Useful distinctions now include:

```text
FRESH EVIDENCE     ≠ FRESH TRUST STATE
VALID SIGNATURE    ≠ CURRENT TRUST KNOWLEDGE
CACHED ACTIVE      ≠ CURRENTLY ACTIVE
REFRESH FAILED     ≠ STILL TRUSTED
NO CURRENT TRUST   ≠ PERMISSION TO RETRY
```

## Why this matters

Revocation is only useful after it propagates to the systems making decisions. Distributed agents can sit behind caches, replicated policy stores, delayed configuration channels or temporarily unreachable identity infrastructure. In those systems the source of truth can be correct while the action node is wrong.

This connects four RESONANCE coordinates directly:

```text
STATE
  ↕
TIME (τ)
  ↕
EVIDENCE
  ↕
RECOVERY
```

The action node must know not only the current operation state, but also whether its trust state is current enough to justify the next transition.

## Important boundary

This benchmark uses deterministic local HMAC keys, an in-memory source-of-truth registry and synthetic cache snapshots. It does **not** test or certify:

- production PKI or certificate status systems;
- CRLs or OCSP;
- Sigstore / Rekor;
- distributed database consistency;
- production cache invalidation;
- real IAM systems;
- universal trust-registry TTL values.

The 120-second freshness budget exists only to make the benchmark state machine falsifiable.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop executed all deterministic trajectories using the upstream `FakeModel`.

The SDK did not automatically refresh trust registries or impose a trust-state freshness policy, and this report does not claim that it should. The measured property is an **application-level trust-state protocol** layered on top of framework primitives.

## Reproducibility

Harness:

`benchmarks/openai-agents-stale-trust-registry-v0.8/run_stale_trust_registry.py`

Workflow:

`.github/workflows/benchmark-openai-agents-stale-trust-registry.yml`

Machine-readable result:

`reports/verified/008-openai-agents-stale-trust-registry/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31458757238`

## Verdict

**The benchmark reproduced a duplicate side effect when fresh signed evidence was evaluated against stale trust-registry state. Requiring a current trust snapshot — or preserving `TRUST_UNKNOWN` when refresh was unavailable — prevented unsafe retry in every safe trajectory.**

The RESONANCE rule now becomes:

# **preserve UNKNOWN; preserve CONFLICT; verify AUTHORITY; verify authority TIME; verify TRUST STATE freshness; act only on currently trusted evidence**

---

**RESONANCE Verified Report #008**  
**Status:** Reproducible stale-trust-registry run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Stale registry detected:** Yes  
**Revocation recovered by refresh:** Yes  
**Refresh failure held `TRUST_UNKNOWN`:** Yes  
**Current rotated authority accepted:** Yes  
**Cryptographic scheme:** local toy HMAC only  
**Vulnerability claim:** No  
**External safety certification:** No
