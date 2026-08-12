# RESONANCE Verified Report #041

# Constitutional Root Authority Replay / Root Currentness

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Constitutional Root Authority Replay / Root Currentness v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, constitutional root and witness identities (test-only)  
**GitHub Actions run:** `31621380899`  
**Job:** `94196799768`  
**Benchmark head SHA:** `7590bd8ce2c894d5a72ffb9c639896e87ce3dbfd`  
**Evidence artifact:** `resonance-constitutional-root-replay-v1.0`  
**Artifact ID:** `9151370681`  
**Artifact digest:** `sha256:672ef3a413da475bb038989add5d97f109198a5b41cd865da4207823b67f6bf2`

## Result

# **10 / 10 — Constitutional root currentness protocol passes**

Verified #040 recovered from conflicting governance finality through a constitutional/root authority. Report #041 asks whether calling an authority `root` makes an old authentic root record permanently reusable.

# **ROOT AUTHORITY ≠ TIMELESS AUTHORITY**

## Root history

Historical root:

```text
C3
issuer = constitutional-root-resolution-demo-key-v1
root namespace = resonance-constitutional-root
root epoch = 3
set-R = {W25,W26,W27}
threshold = 2
H9 binding = true
authentic = true
root digest =
sha256:4378e3e85eea7912642969d0b6adb6c3668063c9c5cba8c1a5c59c16d0417a45
```

Current root:

```text
C5
same root issuer
root epoch = 5
set-H = {W22,W23,W24}
threshold = 2
predecessor_root_digest = digest(C3)
H9 binding = true
authentic = true
root digest =
sha256:07826e04fd06ff733141b8f4a97117d819b2ee26b27554e4d16883fe4e5875f7
```

Both root records remain cryptographically authentic. Their local 2-of-3 witness certificates also validate.

## Establishing root currentness

After observing C5, the verifier persists:

```text
root_namespace = resonance-constitutional-root
max_root_epoch = 5
root_record_digest = digest(C5)
```

The benchmark keeps this checkpoint intact during the replay attack. Storage rollback is not part of this test.

## Unsafe: authentic historical root is treated as current

A verifier that checks only root authenticity, quorum validity and H9 binding sees replayed C3:

```text
C3 authentic = true
QC-root-epoch3 valid = true
H9 authentic = true
root binds H9 = true

→ presented_root_treated_as_current
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

Nothing in the old signature announces that a newer root epoch has already been observed.

## Safe: monotonic root high-watermark blocks replay

The same C3 is compared with the trusted root checkpoint:

```text
presented root epoch = 3
trusted max root epoch = 5

3 < 5
→ root_authority_rollback_detected
→ adoption rows = 0
→ effects = 0
```

The historical root record remains valid evidence about the past but cannot regain live authorization power.

## Fresh current-root control

C5 is then presented through the same currentness gate:

```text
presented root epoch = 5
presented digest = trusted digest(C5)
QC-root-epoch5 valid = true
H9 binding = true

→ current_root_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Historical C3 and current C5 authenticate; both local quorums validate | PASS | 2/2 |
| Observing C5 establishes monotonic root high-watermark epoch 5 | PASS | 2/2 |
| Unsafe verifier accepts replayed C3 and commits one effect | PASS | 2/2 |
| Root-currentness verifier rejects C3 below high-watermark with zero effects | PASS | 2/2 |
| Fresh C5 passes currentness gate and restores liveness once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I123 — ROOT AUTHORITY ≠ TIMELESS AUTHORITY**

Being the highest configured authority does not make every historically authentic root record current forever.

# **I124 — AUTHENTIC ROOT RECORD BELOW A TRUSTED ROOT HIGH-WATERMARK = ROOT-AUTHORITY ROLLBACK EVIDENCE**

A valid root signature cannot override already-observed monotonic root history.

# **I125 — ROOT CURRENTNESS MUST BIND A MONOTONIC ROOT EPOCH AND ROOT-RECORD DIGEST BEFORE CONSEQUENTIAL AUTHORIZATION**

Epoch prevents backward movement; digest prevents substituting different content at the trusted epoch.

# **I126 — A RETIRED ROOT RECORD MAY REMAIN HISTORICALLY VALID BUT MUST NOT REGAIN LIVE AUTHORITY AFTER A NEWER ROOT EPOCH IS OBSERVED**

Historical validity and current authorization are separate properties even at the trust root.

## TTP root-currentness rule

```text
RECEIVE ROOT RECORD R
        ↓
AUTHENTICATE R
        ↓
VALIDATE LOCAL ROOT QUORUM + HEAD BINDING
        ↓
READ TRUSTED ROOT HIGH-WATERMARK H*
        ↓
R.root_epoch < H*.root_epoch ?
  ├─ yes → ROOT AUTHORITY ROLLBACK → HOLD
  └─ no
       ↓
SAME EPOCH BUT DIFFERENT DIGEST ?
  ├─ yes → ROOT SAME-EPOCH CONFLICT → HOLD
  └─ no
       ↓
CURRENT ROOT AUTHORITY
       ↓
FENCED CONSEQUENCE
```

## Relationship to #040–#041

```text
#040 → can authenticated governance finality fork into two histories?
#041 → can an older authentic constitutional/root record be replayed after newer root history is known?
```

## Interpretation boundary

The benchmark uses deterministic HMAC fixtures and PostgreSQL as a local durable root checkpoint. It does not claim the checkpoint is itself rollback-resistant; that storage problem was isolated in Verified #033. It does not implement production PKI, hardware trust anchors, transparency logs, BFT or constitutional governance, social/legal consensus, or real incident response.

A same-epoch constitutional/root equivocation remains a separate verification surface.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions or another external product.

## Reproducibility

Benchmark: `benchmarks/constitutional-root-replay-v1.0/`  
Workflow: `.github/workflows/benchmark-constitutional-root-replay.yml`  
Machine result: `reports/verified/041-constitutional-root-replay/result.json`  
GitHub Actions: `31621380899`

## Verdict

**An authentic historical constitutional root at epoch 3 retained a valid local quorum and H9 binding. An unsafe verifier treated the replayed record as current and committed one external effect. After the verifier had already persisted epoch 5 / digest(C5) as its root high-watermark, the same C3 replay was rejected as `root_authority_rollback_detected` with zero effects, while fresh C5 remained live and succeeded exactly once.**
