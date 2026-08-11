# RESONANCE Verified Report #006

# OpenAI Agents SDK — Evidence Authority Failure

**Target:** `openai/openai-agents-python`  
**Target version:** `0.19.4`  
**Pinned target SHA:** `2231eb5d40cd4a9d6b86f79492e984eeb3301263`  
**Benchmark:** RESONANCE Evidence Authority Failure v0.6  
**Executed:** 2026-08-11T04:18:31Z  
**GitHub Actions run:** `31458046404`  
**Evidence artifact:** `resonance-openai-agents-evidence-authority-v0.6`  
**Artifact digest:** `sha256:9003d6e28664b1538d4022ad2d63b6709f60d1b06ad8a679d658eae75aabe953`

## Result

# **10 / 10 — Evidence authority**

**Classification: verified-authority evidence protocol passes**

Report #005 showed that evidence sources can disagree. Report #006 asks the next question: **what if a source merely claims to be authoritative?**

The benchmark created a synthetic side effect that committed and then lost its response. It then supplied evidence records containing a status, source, claimed authority, key identity, validity window and integrity tag.

The unsafe policy trusted the label `authority=primary` without verifying the record and produced a duplicate effect. The safe policies required integrity, freshness and authority binding before allowing the evidence to influence a retry decision.

```text
raw evidence
   ↓
claimed authority
   ↓
VERIFY
   ├─ integrity valid?
   ├─ fresh?
   ├─ key identity trusted?
   └─ authority binding valid?
           ↓
       trusted evidence
           ↓
       legal action
```

## Comparative result

| Scenario | Evidence decision | Final effects |
|---|---|---:|
| Unsafe trust in claimed authority | forged `ABSENT`, labelled `primary` → retry | **2** |
| Safe forged-signature handling | integrity verification fails → retry blocked | **1** |
| Safe expired-attestation handling | signature valid but freshness fails → retry blocked | **1** |
| Safe trusted evidence | fresh trusted `COMMITTED` → complete | **1** |

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Unsafe claimed-authority → retry hazard reproduced | PASS | 2/2 |
| Forged signature rejected | PASS | 2/2 |
| Expired attestation rejected | PASS | 2/2 |
| Valid fresh authority accepted | PASS | 2/2 |
| Pinned reproducible evidence | PASS | 2/2 |
| **Total** |  | **10/10** |

## Scenario 1 — a label is not an authority proof

The synthetic operation committed once and the response was lost. The next record said:

```text
status    = ABSENT
authority = primary
key_id    = primary-v1
```

but its integrity tag had been produced with a different local benchmark key.

The unsafe trajectory did not verify any of that. It trusted the metadata and retried.

```text
commit #1
response lost
raw evidence → ABSENT / claimed primary
NO verification
retry
commit #2
```

Final effect count: **2**.

The failure is not that evidence was missing. It is that **asserted provenance was mistaken for verified provenance**.

## Scenario 2 — forged evidence is rejected before action

The safe trajectory read the same kind of forged `ABSENT` record, then ran the verification step.

Observed verification:

```text
signature_valid = false
fresh           = true
authority_valid = true
trusted         = false
```

Because integrity failed, the record could not authorize retry.

Final effect count: **1**.

## Scenario 3 — integrity is not enough if the evidence is expired

A second record had a valid integrity tag from the trusted local benchmark key and correctly claimed primary authority, but its validity window had already expired.

Observed:

```text
signature_valid = true
fresh           = false
authority_valid = true
trusted         = false
```

The safe protocol still blocked retry.

Final effect count: **1**.

This matters because a perfectly authentic statement can still be the wrong basis for a present-time transition.

## Scenario 4 — trusted fresh evidence can close the trajectory

The final record was fresh, integrity-valid and bound to the trusted local benchmark key for the synthetic primary authority. It reported `COMMITTED`.

Observed:

```text
signature_valid = true
fresh           = true
authority_valid = true
trusted         = true
status          = COMMITTED
```

The application completed without retry.

Final effect count: **1**.

## The evidence model expands again

Report #005 proposed:

```text
Evidence = value + source + authority + freshness + provenance
```

This run shows that provenance itself needs a verification property:

# **Evidence = value + source + authority + freshness + provenance + integrity**

A useful evidence consumer should be able to distinguish:

```text
CLAIMED AUTHORITY  ≠ VERIFIED AUTHORITY
SIGNED             ≠ FRESH
AUTHENTIC          ≠ CURRENT
KNOWN KEY ID       ≠ VALID SIGNATURE
VALID RECORD       ≠ LEGAL ACTION
```

## The authority invariant

# **Claimed authority must not authorize action until integrity, freshness and authority binding are verified.**

The dangerous shortcut is:

```text
metadata says "primary"
        ↓
      TRUST
        ↓
      ACTION
```

The safer transition is:

```text
CLAIM
  → VERIFY INTEGRITY
  → VERIFY FRESHNESS
  → VERIFY IDENTITY / AUTHORITY BINDING
  → TRUSTED EVIDENCE
  → DECIDE
```

## Important cryptographic boundary

This benchmark intentionally uses a deterministic **local HMAC toy attestation**. It is enough to test the state-machine decision — whether the application verifies evidence before acting — but it is **not** a production signing architecture.

This report does not claim to test or certify:

- Sigstore;
- PKI or certificate-chain validation;
- transparency logs;
- hardware-backed keys;
- key rotation or revocation infrastructure;
- production identity providers;
- real cryptographic adversaries.

Those are possible future layers of the benchmark.

## What the SDK did — and did not do

The pinned OpenAI Agents SDK tool loop executed all four deterministic trajectories using the upstream `FakeModel`.

As in Reports #003–#005, the SDK faithfully executes the application protocol supplied to it. This report does **not** claim that OpenAI Agents SDK automatically verifies provenance, signatures or authority metadata, nor that it should impose a universal evidence model.

The measured property is an **application-level evidence-verification protocol** layered on the framework.

## Why this matters

Agent systems can increasingly consume approvals, receipts, audit logs, database records, webhook payloads, tool outputs and signed artifacts. If the agent treats a self-declared role or source label as proof, then provenance exists only cosmetically.

A trustworthy action path needs a stronger distinction:

```text
observation
  → provenance claim
  → provenance verification
  → authority decision
  → state transition
```

This connects the RESONANCE Evidence coordinate directly to identity, attestation and trust-chain design.

## Interpretation boundary

This report verifies a **synthetic application protocol** on one pinned OpenAI Agents SDK revision. It does **not** verify:

- arbitrary applications built with the SDK;
- live-model reasoning quality;
- production cryptography;
- a real identity or attestation provider;
- universal authority rules;
- real payment or production side effects;
- automatic SDK authenticity guarantees.

No production API key, live model, real credential or external side-effecting service was used.

## Reproducibility

Harness:

`benchmarks/openai-agents-evidence-authority-v0.6/run_evidence_authority.py`

Workflow:

`.github/workflows/benchmark-openai-agents-evidence-authority.yml`

Machine-readable result:

`reports/verified/006-openai-agents-evidence-authority/result.json`

Pinned upstream commit:

`https://github.com/openai/openai-agents-python/commit/2231eb5d40cd4a9d6b86f79492e984eeb3301263`

GitHub Actions run:

`https://github.com/safal207/RESONANCE/actions/runs/31458046404`

## Verdict

**The benchmark reproduced a duplicate side effect when claimed authority was trusted without verification. Requiring evidence integrity, freshness and authority binding blocked unsafe retry in every safe trajectory.**

The RESONANCE evidence rule now becomes:

# **preserve UNKNOWN; preserve CONFLICT; verify AUTHORITY; act only on trusted evidence**

---

**RESONANCE Verified Report #006**  
**Status:** Reproducible evidence-authority run  
**Score:** 10/10  
**Unsafe duplicate reproduced:** Yes  
**Forged signature rejected:** Yes  
**Expired attestation rejected:** Yes  
**Fresh trusted COMMITTED accepted:** Yes  
**Cryptographic scheme:** local toy HMAC only  
**Vulnerability claim:** No  
**External safety certification:** No
