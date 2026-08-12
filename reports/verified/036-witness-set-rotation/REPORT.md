# RESONANCE Verified Report #036

# Witness-Set Rotation / Membership Epoch Confusion

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Witness-Set Rotation / Membership Epoch Confusion v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head, membership authority and six witness identities (test-only)  
**GitHub Actions run:** `31617000939`  
**Job:** `94182207065`  
**Benchmark head SHA:** `d13b424e775e098fbbafa4461ea0f572f8fd7774`  
**Evidence artifact:** `resonance-witness-set-rotation-v1.0`  
**Artifact ID:** `9149649881`  
**Artifact digest:** `sha256:827ead873af366a27a19958413887356079c5afc0d22bdfe9fff6f9ea6e6c459`

## Result

# **10 / 10 — Witness-set rotation protocol passes**

Verified #035 showed that a locally valid witness quorum can still conflict with another quorum in another view. Report #036 asks the next question:

> What if the quorum itself is internally consistent and non-conflicting, but the witness membership that created it has already been rotated out of authority?

# **VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY**

## Membership rotation

Historical membership record `M1`:

```text
set-A / epoch 1
members = W1, W2, W3
threshold = 2
issued_for_generation = 7
membership signature = valid
```

Current membership record `M2`:

```text
set-B / epoch 2
members = W4, W5, W6
threshold = 2
issued_for_generation = 9
successor_of_set_id = set-A
membership signature = valid
```

The historical record remains authentic. Rotation changes authority, not history.

## Historical QC remains cryptographically valid

`QC-old-epoch1` contains:

```text
W1 + W2
set_id = set-A
set_epoch = 1
membership_digest = digest(M1)
round = 60
head = H7 / generation 7
```

Every witness statement authenticates, both signers belong to M1, threshold `2-of-3` is satisfied, and the certificate binds the same head and generation.

```text
QC-old valid under M1 = true
```

That is expected. The certificate was valid when set-A had authority.

## Unsafe: validate only against bundled historical membership

A verifier checks QC-old against M1, H7 and a generation-7 regional authority replica:

```text
historical membership authentic = true
QC-old valid = true
H7 authentic = true
regional replica = R1 / generation 7 / ACTIVE

→ historical_membership_quorum_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

No signature is forged. No threshold is miscounted. The verifier simply fails to ask whether set-A is still the current witness authority.

## Safe: resolve current witness-set authority

The same certificate is compared with current membership `M2`:

```text
certificate set_id = set-A
certificate set_epoch = 1
certificate membership_digest = digest(M1)

current set_id = set-B
current set_epoch = 2
current membership_digest = digest(M2)
```

The historical certificate remains valid as historical evidence, but it no longer matches current membership authority:

```text
same_current_set = false
→ witness_set_authority_conflict
→ adoption rows = 0
→ external effects = 0
```

The membership mismatch dominates otherwise-valid head and replica checks.

## Fresh current-set recovery

A new certificate is issued by the current set:

```text
QC-current-epoch2
W4 + W5
set-B / epoch 2
membership_digest = digest(M2)
round = 61
head = H9 / generation 9
```

With current regional authority R2/generation 9:

```text
current membership matches = true
certificate valid = true
H9 authentic = true

→ current_membership_quorum_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

Rotation therefore invalidates live authority of the old set without erasing its historical evidence.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Historical set-A quorum remains cryptographically valid after rotation | PASS | 2/2 |
| Unsafe verifier accepts old-membership quorum and commits one effect | PASS | 2/2 |
| Current membership authority exposes epoch/digest mismatch | PASS | 2/2 |
| Safe verifier rejects old-membership quorum with zero effects | PASS | 2/2 |
| Fresh current set-B quorum succeeds exactly once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I103 — VALID QUORUM FOR AN OLD MEMBERSHIP ≠ CURRENT QUORUM AUTHORITY**

A quorum can remain cryptographically and historically valid after the membership that formed it has lost current authority.

# **I104 — QUORUM CERTIFICATE MUST BIND WITNESS-SET IDENTITY, SET EPOCH, MEMBERSHIP DIGEST, THRESHOLD POLICY, ROUND, HEAD IDENTITY, AND DISTINCT SIGNERS**

Without an exact membership binding, the verifier cannot determine which authority configuration authorized the certificate.

# **I105 — ADOPTION MUST RESOLVE CURRENT WITNESS-SET AUTHORITY AND REJECT SUPERSEDED MEMBERSHIP BEFORE CONSEQUENCE**

Valid signatures from a superseded set must not authorize a new consequence merely because they still verify cryptographically.

# **I106 — MEMBERSHIP ROTATION REQUIRES FRESH CURRENT-SET QUORUM EVIDENCE; OLD MEMBERS REMAIN HISTORICAL EVIDENCE, NOT LIVE AUTHORITY**

Rotation preserves auditability while moving execution authority forward.

## TTP witness-set currentness rule

```text
RECEIVE QUORUM CERTIFICATE QC
        ↓
AUTHENTICATE MEMBER STATEMENTS
        ↓
BIND QC TO SET ID + SET EPOCH + MEMBERSHIP DIGEST + THRESHOLD
        ↓
RESOLVE CURRENT AUTHENTICATED MEMBERSHIP M_now
        ↓
QC membership == M_now?
  ├─ no → WITNESS-SET AUTHORITY CONFLICT → HOLD / 0 CONSEQUENCE
  └─ yes
        ↓
CHECK QUORUM CONSISTENCY + HEAD + AUTHORITY VIEW
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE MEMBERSHIP CURRENTNESS → QC → HEAD → EFFECT
```

## Relationship to #034–#036

```text
#034 → can one witness fork its history?
#035 → can two valid local majorities disagree?
#036 → can a valid majority from a superseded membership regain live authority?
```

## Interpretation boundary

The benchmark uses deterministic HMAC identities and two explicitly supplied membership records. It does not implement production PKI, membership governance, dynamic BFT reconfiguration, key revocation, distributed membership propagation, consensus liveness, or protection against stale/replayed membership-authority views.

A later benchmark should separately test a verifier that receives an authentic but stale membership-authority record after rotation.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/witness-set-rotation-v1.0/`  
Workflow: `.github/workflows/benchmark-witness-set-rotation.yml`  
Machine result: `reports/verified/036-witness-set-rotation/result.json`  
GitHub Actions: `31617000939`

## Verdict

**A historical set-A / epoch-1 quorum signed by W1+W2 remained fully authentic and valid under its original membership after rotation. An unsafe verifier that validated only against that bundled historical membership accepted H7 and committed one external effect. Resolving current authenticated membership M2 / set-B / epoch-2 instead produced `witness_set_authority_conflict` and zero effects. A fresh W4+W5 quorum bound to M2 and H9 restored liveness exactly once.**
