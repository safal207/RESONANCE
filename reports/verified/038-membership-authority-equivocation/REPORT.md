# RESONANCE Verified Report #038

# Membership Authority Equivocation / Same-Epoch Fork

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Membership Authority Equivocation / Same-Epoch Fork v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, membership authority, recovery authority and witness identities (test-only)  
**GitHub Actions run:** `31618790089`  
**Job:** `94188104629`  
**Benchmark head SHA:** `a90f9d903e74103dfead69134104c44761848982`  
**Evidence artifact:** `resonance-membership-authority-equivocation-v1.0`  
**Artifact ID:** `9150364287`  
**Artifact digest:** `sha256:bbd0de53bf4cc9690a4df11893ccaa7fbb5469d60fa4353aa96d2ff62bf8039b`

## Result

# **10 / 10 — Membership authority equivocation protocol passes**

Verified #037 showed that an authentic old membership record must not be replayed below a trusted membership high-watermark. Report #038 asks the next question:

> What if the membership authority itself signs two different membership records for the same epoch?

# **SAME AUTHORITY + SAME MEMBERSHIP EPOCH + DIFFERENT AUTHENTIC MEMBERSHIP DIGESTS = EQUIVOCATION EVIDENCE**

## One predecessor, two epoch-2 histories

Both branches extend the same authenticated epoch-1 predecessor:

```text
M1
set-A / epoch 1
membership_digest = sha256:d246e109...
```

Branch A:

```text
M2-A
issuer = membership-authority-demo-key-v1
set-B / epoch 2
members = W4, W5, W6
threshold = 2
predecessor = digest(M1)
membership signature = valid
membership digest =
sha256:aa0ad1f938ebde6911b5678bd40aaf0df1f2294c8925e8658b088f2c70557402
```

Branch B:

```text
M2-B
issuer = membership-authority-demo-key-v1
set-C / epoch 2
members = W7, W8, W9
threshold = 2
predecessor = digest(M1)
membership signature = valid
membership digest =
sha256:b1586f4db5d001f30c64587bfdc960b625748d55048d30b94f350ddeebeca24c
```

The same authority, same namespace, same epoch and same predecessor produced two different authentic membership digests.

## Both local branches validate

Each branch has its own 2-of-3 quorum over the same authenticated H9 authority head:

```text
QC-A = W4 + W5
set-B / epoch 2
H9
valid = true

QC-B = W7 + W8
set-C / epoch 2
H9
valid = true
```

No witness signature is forged. No threshold is miscounted. The fork is in membership authority itself.

## Unsafe: isolated branch becomes live authority

A verifier shown only M2-B and QC-B obtains:

```text
M2-B authentic = true
QC-B valid = true
H9 authentic = true
regional R2 / generation 9 / ACTIVE = true

→ isolated_membership_branch_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

The verifier cannot infer the hidden sibling branch from local validity alone.

## Safe: cross-view comparison turns two valid records into conflict evidence

When M2-A and M2-B meet:

```text
same membership namespace = true
same issuer = true
same set_epoch = 2
same predecessor digest = true
both signatures authentic = true
different membership digest = true

→ membership_authority_equivocation_detected
```

The safe path does not choose set-B or set-C merely because both are locally valid.

Both disputed branches are held:

```text
branch A → adoption rows = 0 → effects = 0
branch B → adoption rows = 0 → effects = 0
issuer membership-authority-demo-key-v1 → quarantine
```

## Recovery must bind the conflict, not hide it

Recovery uses a separate recovery authority and advances to a higher epoch:

```text
M3
issuer = membership-recovery-authority-demo-key-v1
set-D / epoch 3
members = W10, W11, W12
threshold = 2

predecessor_membership_digests = [digest(M2-A), digest(M2-B)]
resolves_equivocation_digests = [digest(M2-A), digest(M2-B)]
```

A fresh quorum:

```text
QC-recovery = W10 + W11
set-D / epoch 3
H9
```

passes only because M3 is authenticated by the separate recovery authority, advances beyond epoch 2, and explicitly binds both conflicting branch digests:

```text
→ equivocation_resolved_by_fresh_recovery_membership
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Same-authority same-epoch membership branches both authenticate and validate locally | PASS | 2/2 |
| Isolated verifier accepts one fork branch and commits one effect | PASS | 2/2 |
| Cross-view comparison detects same-epoch membership-authority equivocation | PASS | 2/2 |
| Safe verifier holds both disputed branches with zero effects | PASS | 2/2 |
| Higher-epoch recovery binds both conflict digests and restores liveness once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I111 — SAME AUTHORITY + SAME MEMBERSHIP EPOCH + DIFFERENT AUTHENTIC MEMBERSHIP DIGESTS = EQUIVOCATION EVIDENCE**

Two authentic successor records at one membership epoch are not two candidate truths. Their conflict is itself evidence.

# **I112 — AUTHENTIC MEMBERSHIP RECORD ≠ UNIQUE MEMBERSHIP HISTORY**

A valid signature proves origin and integrity of one record; it does not prove the issuer produced only one record for that epoch.

# **I113 — MEMBERSHIP-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED BRANCHES AND QUARANTINE THE EQUIVOCATING ISSUER BEFORE CONSEQUENCE**

A verifier must not select a disputed branch merely because its local quorum and signatures are valid.

# **I114 — RECOVERY REQUIRES A FRESH HIGHER-EPOCH MEMBERSHIP FROM NON-EQUIVOCATING AUTHORITY OR EXPLICIT GOVERNANCE RESOLUTION BINDING ALL CONFLICTING BRANCH DIGESTS**

Recovery must preserve the fork as evidence and explicitly resolve it before live authority resumes.

## TTP membership-authority equivocation rule

```text
RECEIVE MEMBERSHIP M
        ↓
AUTHENTICATE M
        ↓
LOOK FOR AUTHENTIC PEER VIEW AT SAME NAMESPACE + EPOCH
        ↓
same issuer + same epoch + same predecessor + different digest?
  ├─ yes → MEMBERSHIP-AUTHORITY EQUIVOCATION
  │        → quarantine issuer
  │        → hold every disputed branch
  │        → 0 consequence
  └─ no
        ↓
CHECK MEMBERSHIP ANTI-ROLLBACK / CURRENTNESS
        ↓
VALIDATE QUORUM + HEAD + AUTHORITY VIEW
        ↓
FENCED CONSEQUENCE

RECOVERY:
  higher epoch
+ non-equivocating recovery authority / governance resolution
+ bind every disputed membership digest
+ fresh quorum
→ resume
```

## Relationship to #036–#038

```text
#036 → is the quorum's membership still authorized?
#037 → is the membership record itself replayed from an older epoch?
#038 → did the membership authority fork one epoch into two authentic histories?
```

## Interpretation boundary

The benchmark uses deterministic HMAC identities and an explicit separate recovery-authority fixture. It does not implement production PKI, BFT reconfiguration, governance voting, transparency logs, consensus finality, key revocation, synchrony or a real-world incident response process.

A later benchmark should separately test conflicting recovery authorities or conflicting higher-epoch resolution records.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions or another external product.

## Reproducibility

Benchmark: `benchmarks/membership-authority-equivocation-v1.0/`  
Workflow: `.github/workflows/benchmark-membership-authority-equivocation.yml`  
Machine result: `reports/verified/038-membership-authority-equivocation/result.json`  
GitHub Actions: `31618790089`

## Verdict

**The same authenticated membership authority issued two different authentic epoch-2 memberships from the same predecessor. Each branch had a locally valid 2-of-3 quorum. An isolated verifier shown only set-C accepted it and committed one external effect. Cross-view comparison exposed same-issuer, same-epoch, same-predecessor, different-digest equivocation and held both branches with zero effects. A separate recovery authority then issued epoch-3 set-D explicitly binding both disputed digests; W10+W11 restored liveness exactly once.**
