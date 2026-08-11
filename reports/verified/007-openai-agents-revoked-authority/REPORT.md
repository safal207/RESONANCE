# RESONANCE Verified Report #007

# OpenAI Agents SDK — Revoked Authority / Key Rotation

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Revoked Authority / Key Rotation v0.7  
**Executed:** 2026-08-11T04:25:12Z  
**GitHub Actions run:** `31458387817`  
**Evidence artifact:** `resonance-openai-agents-revoked-authority-v0.7`  
**Artifact digest:** `sha256:0947cc82b86db36a48a7209e97719a42906233c8fc99c5e27ee1168577188847`

## Result

# **10 / 10 — Authority lifecycle**

**Classification: decision-time authority lifecycle protocol passes**

Report #006 verified that a claimed authority must be bound to valid integrity, freshness and identity. Report #007 asks the temporal follow-up: **what if the signature is mathematically valid, the evidence is still fresh, but the signing authority has already been revoked?**

The benchmark creates one synthetic side effect that commits and loses its response. It then evaluates signed evidence against a local toy trust registry with key activation and revocation times.

```text
signed evidence
    ↓
signature valid?
    ↓
evidence fresh?
    ↓
authority binding valid?
    ↓
key active at decision time?
    ↓
trusted evidence
    ↓
legal action
```

## Comparative result

| Scenario | Trust decision | Final effects |
|---|---|---:|
| Unsafe signature-only acceptance | valid old signature, key already revoked → retry | **2** |
| Safe revoked-key handling | signature valid + evidence fresh + authority valid, but key inactive now | **1** |
| Safe not-yet-active key handling | signature valid, future key not active yet | **1** |
| Safe current rotated key | current active key + trusted `COMMITTED` | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe valid-but-revoked retry hazard reproduced | PASS | 2/2 |
| Revoked key rejected at decision time | PASS | 2/2 |
| Not-yet-active key rejected | PASS | 2/2 |
| Current rotated key accepted | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — a valid signature can still be unsafe to trust

The first synthetic action committed and then timed out. A later evidence record reported `ABSENT` and was signed correctly with `primary-v1`.

The unsafe trajectory checked only that the record looked authentic enough to use and did not consult the key lifecycle.

```text
commit #1
response lost
signed ABSENT / primary-v1
signature mathematically valid
revocation ignored
retry
commit #2
```

Final effect count: **2**.

The failure is temporal: the evidence is authentic, but the authority is no longer valid for a current decision.

## Scenario 2 — authentic, fresh, authoritative — and still untrusted

The safe trajectory used the same old-key pattern but explicitly checked the registry at decision time.

Observed:

```text
signature_valid       = true
evidence_fresh        = true
authority_valid       = true
key_active_at_issue   = true
key_active_at_decision= false
trusted               = false
```

The old key was valid when the evidence was issued, then revoked 60 seconds before the benchmark decision time.

Retry was blocked. Final effect count: **1**.

This benchmark adopts a deliberately strict **current-state policy**: evidence used to authorize a new current action must come from an authority that is active at decision time. Other systems may define historical-signature semantics differently; the key requirement is that the rule be explicit and testable.

## Scenario 3 — future authority is not current authority

A scheduled `primary-v3` key produced a mathematically valid signature, but its activation time was still in the future.

Observed:

```text
signature_valid        = true
evidence_fresh         = true
authority_valid        = true
key_active_at_decision = false
trusted                = false
```

Retry remained blocked. Final effect count: **1**.

## Scenario 4 — rotation succeeds when the new key is active

The current `primary-v2` key was active before decision time and had no revocation timestamp. Its fresh trusted evidence reported `COMMITTED`.

```text
signature_valid        = true
evidence_fresh         = true
authority_valid        = true
key_active_at_decision = true
trusted                = true
status                 = COMMITTED
```

The application completed without retry. Final effect count: **1**.

## The temporal trust invariant

# **VALID SIGNATURE ≠ CURRENTLY TRUSTED AUTHORITY**

For this benchmark policy:

```text
activated_at ≤ decision_time < revoked_at
```

when a revocation time exists.

That adds a lifecycle dimension to the evidence model:

```text
Evidence =
  value
+ source
+ authority
+ freshness
+ provenance
+ integrity
+ authority_lifecycle
```

Useful distinctions now include:

```text
AUTHENTIC            ≠ CURRENTLY AUTHORIZED
VALID AT ISSUE       ≠ VALID AT DECISION
KNOWN KEY            ≠ ACTIVE KEY
ROTATED KEY          ≠ FUTURE KEY
VALID SIGNATURE      ≠ LEGAL TRANSITION
```

## Why this matters

Agent systems may consume signed approvals, webhook receipts, audit records, payment evidence, policy grants or tool attestations long after those artifacts were created. During that interval, keys can be rotated, identities can lose privileges, organizations can revoke credentials and trust policies can change.

That means time is not merely metadata on evidence. **Time participates in the authorization decision.**

```text
EVIDENCE
   ↕
TIME (τ)
   ↕
AUTHORITY LIFECYCLE
   ↓
TRUST DECISION
```

This is a direct connection between the RESONANCE `Evidence` and `Time` coordinates.

## Important cryptographic boundary

This benchmark intentionally uses deterministic local HMAC keys and an in-memory toy trust registry. It tests state-machine semantics around activation and revocation. It does **not** test or certify:

- production PKI;
- certificate revocation lists or OCSP;
- Sigstore / Rekor;
- timestamp authorities;
- key transparency;
- hardware-backed keys;
- production identity providers;
- historical-signature or long-term-validation standards.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop executed all deterministic trajectories using the upstream `FakeModel`.

The SDK did not automatically enforce key revocation semantics, and this report does not claim that it should. The measured property is an **application-level authority-lifecycle protocol** layered on top of framework primitives.

## Interpretation boundary

This run uses synthetic local effects, toy keys and an explicit benchmark revocation policy. It is not a vulnerability claim, cryptographic certification or safety certification for arbitrary applications built with the SDK.

No production API key, live model, real credential or external side-effecting service was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-revoked-authority-v0.7/run_revoked_authority.py`

Workflow:

`.github/workflows/benchmark-openai-agents-revoked-authority.yml`

Machine-readable result:

`reports/verified/007-openai-agents-revoked-authority/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31458387817`

## Verdict

**The benchmark reproduced a duplicate side effect when a mathematically valid but revoked authority was trusted without a lifecycle check. Explicit activation/revocation verification blocked unsafe retry and accepted only the current rotated authority.**

The RESONANCE evidence rule now becomes:

# **preserve UNKNOWN; preserve CONFLICT; verify AUTHORITY; verify authority TIME; act only on currently trusted evidence**

---

**RESONANCE Verified Report #007**  
**Status:** Reproducible authority-lifecycle run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Revoked valid signature rejected:** Yes  
**Future key rejected:** Yes  
**Current rotated key accepted:** Yes  
**Cryptographic scheme:** local toy HMAC only  
**Vulnerability claim:** No  
**External safety certification:** No
