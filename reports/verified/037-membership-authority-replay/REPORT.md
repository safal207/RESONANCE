# RESONANCE Verified Report #037

# Membership Authority Replay / Stale Rotation View

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Membership Authority Replay / Stale Rotation View v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, membership authority and six witness identities (test-only)  
**GitHub Actions run:** `31617837571`  
**Job:** `94184983666`  
**Benchmark head SHA:** `13e4820054cdd9305c169ce27c1d4a39e8b6d18d`  
**Evidence artifact:** `resonance-membership-authority-replay-v1.0`  
**Artifact ID:** `9149995371`  
**Artifact digest:** `sha256:c01bf51e10708674b29316e006556f298456080b7416e2b662226cceff8e1392`

## Result

# **10 / 10 — Membership authority replay protocol passes**

Verified #036 showed that a valid quorum from an old witness membership must not authorize a new consequence after rotation. Report #037 asks the next question:

> What if the verifier is shown the old membership record itself and that record is still perfectly authentic?

# **AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY**

## Membership history

Historical membership `M1`:

```text
set-A / epoch 1
members = W1, W2, W3
threshold = 2
issued_for_generation = 7
membership signature = valid
```

Current membership `M2`:

```text
set-B / epoch 2
members = W4, W5, W6
threshold = 2
issued_for_generation = 9
predecessor_membership_digest = digest(M1)
membership signature = valid
```

The authenticated successor relationship establishes that epoch 2 has already been observed.

The verifier persists:

```text
membership namespace = resonance-witness-membership
max_set_epoch_seen = 2
set_id = set-B
membership_digest = digest(M2)
```

## The replayed membership is still authentic

An attacker or stale cache later presents `M1` together with the historical quorum:

```text
QC-old-epoch1
W1 + W2
set-A / epoch 1
head = H7 / generation 7
```

Every cryptographic check remains valid:

```text
M1 authentic = true
QC-old valid under M1 = true
H7 authentic = true
regional R1 / generation 7 / ACTIVE = true
```

No signature has been forged. The record is simply old.

## Unsafe: presented membership is treated as current

A verifier that treats the membership record supplied with the quorum as current obtains:

```text
M1 signature valid
QC-old valid
H7 valid
regional R1 valid

→ presented_membership_treated_as_current
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

The stale membership view resurrects the retired set-A authority.

## Safe: monotonic membership checkpoint dominates

The same authentic M1 is compared with the verifier's trusted membership high-watermark:

```text
presented membership:
set-A / epoch 1

trusted checkpoint:
set-B / epoch 2

1 < 2
→ membership_authority_rollback_detected
→ adoption rows = 0
→ external effects = 0
```

Critically, the safe path does not reject M1 because its signature is bad. It rejects the use of M1 as **current authority** because newer authenticated membership history has already been observed.

## Fresh current-membership recovery

With current M2 and a fresh current-set quorum:

```text
QC-current-epoch2
W4 + W5
set-B / epoch 2
head = H9 / generation 9
```

The checkpoint matches exactly:

```text
presented epoch = 2
trusted epoch = 2
presented digest = trusted digest
presented set_id = set-B

→ current_membership_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

Membership currentness therefore advances monotonically while preserving historical records for audit.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Authenticated M1→M2 successor chain establishes epoch-2 membership checkpoint | PASS | 2/2 |
| Unsafe verifier accepts replayed authentic M1 and commits one effect | PASS | 2/2 |
| Safe verifier detects membership-authority rollback before consequence | PASS | 2/2 |
| Replayed M1, old QC and H7 remain cryptographically valid despite being stale | PASS | 2/2 |
| Fresh M2 + current quorum succeeds exactly once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I107 — AUTHENTIC MEMBERSHIP RECORD ≠ CURRENT MEMBERSHIP AUTHORITY**

A membership record may remain cryptographically valid after a successor membership has taken over live authority.

# **I108 — MEMBERSHIP CURRENTNESS MUST BIND TO A MONOTONIC SET-EPOCH / MEMBERSHIP-DIGEST CHECKPOINT OR EQUIVALENT ANTI-ROLLBACK EVIDENCE**

Signature validity proves origin and integrity; monotonic membership history proves that an older authority configuration has not been replayed as current.

# **I109 — AUTHENTIC MEMBERSHIP BELOW THE TRUSTED MEMBERSHIP HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE**

A verifier that has observed epoch 2 must not authorize a new effect from an authentic epoch-1 membership record.

# **I110 — FRESH CURRENT-MEMBERSHIP QUORUM EVIDENCE IS REQUIRED TO RESTORE LIVE AUTHORITY AFTER ROTATION**

Historical membership remains useful evidence, but only the current membership configuration may authorize a new consequence.

## TTP membership-authority anti-replay rule

```text
RECEIVE MEMBERSHIP M + QUORUM QC
        ↓
AUTHENTICATE M
        ↓
READ TRUSTED MEMBERSHIP HIGH-WATERMARK C
        ↓
M.epoch < C.epoch?
  ├─ yes → MEMBERSHIP AUTHORITY ROLLBACK → HOLD / 0 CONSEQUENCE
  └─ no
        ↓
M.epoch == C.epoch?
  ├─ yes → REQUIRE SAME SET ID + MEMBERSHIP DIGEST
  └─ no  → REQUIRE AUTHENTIC SUCCESSOR ADVANCE BEFORE CHECKPOINT UPDATE
        ↓
VALIDATE QC AGAINST CURRENT M
        ↓
CHECK QUORUM CONSISTENCY + HEAD + AUTHORITY VIEW
        ↓
FENCED CONSEQUENCE
```

## Relationship to #036–#037

```text
#036 → is the quorum's witness membership still authorized?
#037 → is the membership record presented as current itself rolled back?
```

## Interpretation boundary

The benchmark uses deterministic HMAC identities, a single signed successor chain and a PostgreSQL membership checkpoint. It does not implement production PKI, BFT reconfiguration, membership transparency logs, distributed checkpoint witnesses, governance, synchrony or protection against rollback of the checkpoint storage itself.

Checkpoint-storage rollback for membership history and conflicting membership-authority issuers remain separate verification surfaces.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions or another external product.

## Reproducibility

Benchmark: `benchmarks/membership-authority-replay-v1.0/`  
Workflow: `.github/workflows/benchmark-membership-authority-replay.yml`  
Machine result: `reports/verified/037-membership-authority-replay/result.json`  
GitHub Actions: `31617837571`

## Verdict

**An old set-A / epoch-1 membership record remained perfectly authentic after a signed successor set-B / epoch-2 membership had already established the verifier's trusted high-watermark. An unsafe verifier that treated the replayed M1 as current accepted the old W1+W2 quorum and committed one external effect. The safe verifier compared M1 with the persisted epoch-2 membership checkpoint, returned `membership_authority_rollback_detected`, and produced zero effects. Fresh M2 plus W4+W5 and H9 restored liveness exactly once.**
