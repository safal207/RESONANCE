# RESONANCE Verified Report #040

# Governance Resolution Equivocation / Conflicting Finality

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Governance Resolution Equivocation / Conflicting Finality v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, governance-resolution authority, constitutional/root authority and witness identities (test-only)  
**GitHub Actions run:** `31620538601`  
**Job:** `94193979974`  
**Benchmark head SHA:** `2afaf1c3bbcda266ec7cbbefb478ff63d27232c4`  
**Evidence artifact:** `resonance-governance-resolution-equivocation-v1.0`  
**Artifact ID:** `9151038853`  
**Artifact digest:** `sha256:6df3501a46124054bdfef7de7c64c9c4597eb5d57a598b247767167ab435f220`

## Result

# **10 / 10 — Governance resolution equivocation protocol passes**

Verified #039 recovered from recovery-authority equivocation through a separate governance-resolution authority. Report #040 asks the next recursive question:

> What if the governance authority that is supposed to establish finality signs two different final resolutions for the same governance epoch?

# **AUTHENTIC GOVERNANCE RESOLUTION ≠ UNIQUE FINALITY**

## The inherited recovery fork

The governance layer receives the preserved recovery-fork evidence from #039:

```text
R3-A digest =
sha256:96ba32f275d54015845336d0b24baccae2ad3d2985322ebdebf53f27579639ae

R3-B digest =
sha256:fc5034190cbfe2727441388e204f44d7904d3000680712a31d9cb7a04ef25ac0
```

Both governance branches explicitly claim to resolve this same inherited dispute set.

## One governance issuer, two epoch-4 finalities

Branch A:

```text
G4-A
issuer = membership-governance-resolution-demo-key-v1
set-F / epoch 4
members = W16, W17, W18
threshold = 2
resolves = [digest(R3-A), digest(R3-B)]
authentic = true
finality digest =
sha256:934092cbe1425ed433555d72e10081cbbe9d1933a421cc901a6e5f9a09d8d45d
```

Branch B:

```text
G4-B
issuer = membership-governance-resolution-demo-key-v1
set-G / epoch 4
members = W19, W20, W21
threshold = 2
resolves = [digest(R3-A), digest(R3-B)]
authentic = true
finality digest =
sha256:117325df07b62b8609a395cf6da32860b309052fd322509005bf1a2cd1b40773
```

Same governance issuer, same namespace, same governance epoch and same inherited dispute set — but two different authentic finality digests.

## Both local finality branches validate

```text
QC-A = W16 + W17
set-F / epoch 4
H9
valid = true

QC-B = W19 + W20
set-G / epoch 4
H9
valid = true
```

No signature, threshold or H9 binding fails locally.

## Unsafe: isolated governance branch becomes live finality

A verifier shown only `G4-B` and `QC-B` obtains:

```text
G4-B authentic = true
QC-B valid = true
H9 authentic = true

→ isolated_governance_branch_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

A locally complete governance proof cannot reveal a hidden sibling finality by itself.

## Safe: cross-view comparison exposes governance equivocation

When `G4-A` and `G4-B` meet:

```text
same governance issuer = true
same namespace = true
same governance epoch = 4
same inherited recovery-fork set = true
same predecessor-resolution digests = true
both records authentic = true
different governance-finality digest = true

→ governance_resolution_equivocation_detected
```

Both disputed finality branches are held:

```text
G4-A branch → adoption rows = 0 → effects = 0
G4-B branch → adoption rows = 0 → effects = 0
governance issuer → quarantine
```

## Recovery from conflicting finality

A distinct constitutional/root authority advances the finality history to epoch 5:

```text
G5
issuer = constitutional-root-resolution-demo-key-v1
set-H / epoch 5
members = W22, W23, W24
threshold = 2

predecessor_governance_resolution_digests = [digest(G4-A), digest(G4-B)]
resolves_governance_equivocation_digests = [digest(G4-A), digest(G4-B)]
```

A fresh quorum:

```text
QC-final = W22 + W23
set-H / epoch 5
H9
```

succeeds only because the independent epoch-5 record authenticates, advances beyond epoch 4 and explicitly binds both conflicting governance branches:

```text
→ governance_equivocation_resolved_by_constitutional_epoch5
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Same governance issuer + same epoch branches both authenticate and validate locally | PASS | 2/2 |
| Isolated verifier accepts one governance fork and commits one effect | PASS | 2/2 |
| Cross-view comparison detects same-epoch governance-resolution equivocation | PASS | 2/2 |
| Safe verifier holds both disputed governance branches with zero effects | PASS | 2/2 |
| Higher-epoch constitutional resolution binds both governance forks and restores liveness once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I119 — AUTHENTIC GOVERNANCE RESOLUTION ≠ UNIQUE FINALITY**

A valid governance signature proves origin and integrity of one finality record; it does not prove the issuer produced only one finality for that epoch.

# **I120 — SAME GOVERNANCE AUTHORITY + SAME GOVERNANCE EPOCH + SAME DISPUTE SET + DIFFERENT AUTHENTIC FINALITY DIGESTS = EQUIVOCATION EVIDENCE**

Two authentic finality records for the same inherited dispute at one governance epoch are a fork, not interchangeable resolutions.

# **I121 — GOVERNANCE-RESOLUTION EQUIVOCATION MUST HOLD ALL DISPUTED FINALITY BRANCHES AND QUARANTINE THE EQUIVOCATING GOVERNANCE ISSUER BEFORE CONSEQUENCE**

A verifier must not prefer a disputed finality merely because its local quorum and signatures validate.

# **I122 — RECOVERY FROM GOVERNANCE EQUIVOCATION REQUIRES A HIGHER-EPOCH INDEPENDENT CONSTITUTIONAL RESOLUTION THAT BINDS EVERY CONFLICTING GOVERNANCE DIGEST**

Finality history must advance explicitly through the conflict rather than silently select or erase one branch.

## Interpretation boundary

The benchmark uses deterministic HMAC fixtures and one explicit constitutional/root recovery authority. It does not implement production PKI, constitutional governance, BFT finality, transparency logs, social consensus, legal authority, key revocation or real incident response.

The current benchmark intentionally exposes a further recursive surface: the constitutional/root authority itself is still an authority and could be replayed, rolled back or equivocate. That is not solved here.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions or another external product.

## Reproducibility

Benchmark: `benchmarks/governance-resolution-equivocation-v1.0/`  
Workflow: `.github/workflows/benchmark-governance-resolution-equivocation.yml`  
Machine result: `reports/verified/040-governance-resolution-equivocation/result.json`  
GitHub Actions: `31620538601`

## Verdict

**The same authenticated governance-resolution authority issued two different authentic epoch-4 finalities for the same preserved recovery-fork evidence. Each branch carried a locally valid 2-of-3 quorum over H9. An isolated verifier accepted set-G and committed one external effect. Cross-view comparison exposed same-issuer, same-epoch, same-dispute-set, different-digest governance equivocation and held both finality branches with zero effects. A distinct constitutional/root authority then advanced to epoch 5, explicitly bound both conflicting governance digests, and restored liveness exactly once.**
