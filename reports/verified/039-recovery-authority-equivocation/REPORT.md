# RESONANCE Verified Report #039

# Recovery Authority Equivocation / Conflicting Resolution Fork

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Recovery Authority Equivocation / Conflicting Resolution Fork v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, recovery authority, governance-resolution authority and witness identities (test-only)  
**GitHub Actions run:** `31619761478`  
**Job:** `94191344408`  
**Benchmark head SHA:** `fbb8d596e526785676b10f5c0dcf3d666d0cae3f`  
**Evidence artifact:** `resonance-recovery-authority-equivocation-v1.0`  
**Artifact ID:** `9150741985`  
**Artifact digest:** `sha256:14f960e31edaabab4e599910387685cdf6dca51cd89cda995a0d6ebe29384677`

## Result

# **10 / 10 — Recovery authority equivocation protocol passes**

Verified #038 resolved a membership-authority same-epoch fork by introducing a separate recovery authority. Report #039 asks the recursive question:

> What if the recovery authority itself signs two different resolutions for the same recovery epoch?

# **AUTHENTIC RECOVERY RECORD ≠ UNIQUE RECOVERY HISTORY**

## The inherited dispute

The recovery layer begins with the two preserved membership-fork digests from #038:

```text
M2-A digest =
sha256:aa0ad1f938ebde6911b5678bd40aaf0df1f2294c8925e8658b088f2c70557402

M2-B digest =
sha256:b1586f4db5d001f30c64587bfdc960b625748d55048d30b94f350ddeebeca24c
```

Both recovery branches explicitly claim to resolve this same dispute set.

## One recovery issuer, two epoch-3 resolutions

Branch A:

```text
R3-A
issuer = membership-recovery-authority-demo-key-v1
set-D / epoch 3
members = W10, W11, W12
threshold = 2
resolves = [digest(M2-A), digest(M2-B)]
authentic = true
resolution digest =
sha256:96ba32f275d54015845336d0b24baccae2ad3d2985322ebdebf53f27579639ae
```

Branch B:

```text
R3-B
issuer = membership-recovery-authority-demo-key-v1
set-E / epoch 3
members = W13, W14, W15
threshold = 2
resolves = [digest(M2-A), digest(M2-B)]
authentic = true
resolution digest =
sha256:fc5034190cbfe2727441388e204f44d7904d3000680712a31d9cb7a04ef25ac0
```

The records have the same recovery issuer, namespace, recovery epoch and dispute set, but different authentic resolution digests.

## Both local recovery branches validate

```text
QC-A = W10 + W11
set-D / epoch 3
H9
valid = true

QC-B = W13 + W14
set-E / epoch 3
H9
valid = true
```

Each branch is a locally complete recovery path. No signature or threshold check fails.

## Unsafe: isolated recovery branch becomes live authority

A verifier shown only `R3-B` and `QC-B` obtains:

```text
R3-B authentic = true
QC-B valid = true
H9 authentic = true

→ isolated_recovery_branch_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

The verifier cannot infer a hidden sibling recovery record from local validity alone.

## Safe: cross-view comparison exposes recovery equivocation

When `R3-A` and `R3-B` meet:

```text
same recovery issuer = true
same namespace = true
same recovery epoch = 3
same inherited dispute set = true
same predecessor membership digests = true
both records authentic = true
different recovery-resolution digest = true

→ recovery_authority_equivocation_detected
```

The safe verifier holds both disputed resolution branches:

```text
R3-A branch → adoption rows = 0 → effects = 0
R3-B branch → adoption rows = 0 → effects = 0
recovery issuer → quarantine
```

## Recovery from recovery equivocation

A distinct governance-resolution authority advances the recovery history to epoch 4:

```text
R4
issuer = membership-governance-resolution-demo-key-v1
set-F / epoch 4
members = W16, W17, W18
threshold = 2

predecessor_resolution_digests = [digest(R3-A), digest(R3-B)]
resolves_recovery_equivocation_digests = [digest(R3-A), digest(R3-B)]
```

The fresh quorum:

```text
QC-final = W16 + W17
set-F / epoch 4
H9
```

succeeds only because the independent epoch-4 resolution binds both conflicting recovery branches:

```text
→ recovery_equivocation_resolved_by_governance_epoch4
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Same recovery issuer + same epoch branches both authenticate and validate locally | PASS | 2/2 |
| Isolated verifier accepts one recovery fork and commits one effect | PASS | 2/2 |
| Cross-view comparison detects same-epoch recovery-authority equivocation | PASS | 2/2 |
| Safe verifier holds both disputed recovery branches with zero effects | PASS | 2/2 |
| Higher-epoch governance resolution binds both recovery forks and restores liveness once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I115 — AUTHENTIC RECOVERY RECORD ≠ UNIQUE RECOVERY HISTORY**

A valid recovery signature proves origin and integrity of one resolution record; it does not prove that the recovery authority produced only one resolution for that epoch.

# **I116 — SAME RECOVERY AUTHORITY + SAME RECOVERY EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC RESOLUTION DIGESTS = EQUIVOCATION EVIDENCE**

Two authentic resolutions of the same dispute at one recovery epoch are a fork, not interchangeable candidates.

# **I117 — RECOVERY-AUTHORITY EQUIVOCATION MUST HOLD ALL DISPUTED RESOLUTION BRANCHES AND QUARANTINE THE EQUIVOCATING RECOVERY ISSUER BEFORE CONSEQUENCE**

A verifier must not select a disputed recovery branch merely because its local quorum is valid.

# **I118 — RECOVERY FROM RECOVERY-EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT RESOLUTION THAT BINDS EVERY CONFLICTING RECOVERY DIGEST**

Resolution history must advance explicitly through the conflict rather than erase or ignore one branch.

## TTP recovery-authority consistency rule

```text
RECEIVE RECOVERY RECORD R
        ↓
AUTHENTICATE R
        ↓
LOOK FOR PEER RECOVERY VIEW
AT SAME NAMESPACE + RECOVERY EPOCH + DISPUTE SET
        ↓
same issuer + same epoch + same dispute + different digest?
  ├─ yes → RECOVERY-AUTHORITY EQUIVOCATION
  │        → quarantine recovery issuer
  │        → hold every disputed resolution branch
  │        → 0 consequence
  └─ no
        ↓
CHECK RECOVERY CURRENTNESS / MEMBERSHIP / QUORUM / HEAD
        ↓
FENCED CONSEQUENCE

RECOVERY FROM RECOVERY FORK:
  higher recovery epoch
+ independent resolver / governance authority
+ bind every conflicting recovery digest
+ fresh quorum
→ resume
```

## Relationship to #038–#039

```text
#038 → did membership authority fork one epoch into two authentic membership histories?
#039 → did the recovery authority fork the resolution itself into two authentic recovery histories?
```

## Interpretation boundary

The benchmark uses deterministic HMAC fixtures and one explicit governance-resolution authority. It does not implement production PKI, real governance voting, BFT reconfiguration, transparency logs, finality, key revocation or a real-world incident response process.

Conflicting governance-resolution authorities and governance-finality currentness remain separate verification surfaces.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions or another external product.

## Reproducibility

Benchmark: `benchmarks/recovery-authority-equivocation-v1.0/`  
Workflow: `.github/workflows/benchmark-recovery-authority-equivocation.yml`  
Machine result: `reports/verified/039-recovery-authority-equivocation/result.json`  
GitHub Actions: `31619761478`

## Verdict

**The same recovery authority issued two different authentic epoch-3 resolutions for the same preserved membership-fork evidence. Each branch carried a locally valid 2-of-3 quorum over H9. An isolated verifier accepted set-E and committed one external effect. Cross-view comparison exposed same-issuer, same-epoch, same-dispute-set, different-digest recovery equivocation and held both branches with zero effects. A distinct governance-resolution authority then advanced to epoch 4, explicitly bound both conflicting recovery digests, and restored liveness exactly once.**
