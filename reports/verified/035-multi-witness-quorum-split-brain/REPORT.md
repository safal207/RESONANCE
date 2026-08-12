# RESONANCE Verified Report #035

# Multi-Witness Quorum Split-Brain / Conflicting Majorities

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Multi-Witness Quorum Split-Brain v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head + three witness identities (test-only)  
**GitHub Actions run:** `31616232956`  
**Job:** `94179611299`  
**Benchmark head SHA:** `74076e8aab3aed95f3d52ecec8b8efd4f9504b9a`  
**Evidence artifact:** `resonance-multi-witness-quorum-split-brain-v1.0`  
**Artifact ID:** `9149326423`  
**Artifact digest:** `sha256:4b41a442c86b03438df17fd8663a85d1609d2f33390ed73c6d73f3053660ceda`

## Result

# **10 / 10 — Multi-witness quorum consistency protocol passes**

Verified #034 showed that one independent witness can equivocate. Report #035 asks the next question:

> What if a verifier no longer trusts one witness, but instead trusts a local `2-of-3` majority?

# **LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM**

## Witness topology

Witness set:

```text
set_id = set-A
set_epoch = 1
members = W1, W2, W3
threshold = 2-of-3
logical round = 50
```

Authority heads:

```text
H7 → generation 7 / R1 ACTIVE
head digest = sha256:419197879e94b1cbb382321292c4b2ab8b824f1f8f71f6a02e4b305657e6f6ec

H9 → generation 9 / R2 ACTIVE
head digest = sha256:8db327c9d436be787862eaba7f2eec29c788e1fd6c9fcc2e74cb7b1486f9722e
```

## Two locally valid quorums

At the same witness-set epoch and logical round:

```text
QC-A → H9
  W1 signs H9
  W2 signs H9

QC-B → H7
  W2 signs H7
  W3 signs H7
```

Every individual statement authenticates.

Both certificates independently satisfy:

```text
2 distinct authentic members
same set-A / epoch 1
same round 50
same head inside each certificate
same generation inside each certificate
threshold = 2

→ QC-A valid = true
→ QC-B valid = true
```

Yet:

```text
QC-A.head_digest != QC-B.head_digest
```

Two local majorities therefore authorize incompatible histories.

## Unsafe: isolated local quorum

Verifier B sees only `QC-B`, H7, and a generation-7 R1 regional replica.

All local checks pass:

```text
H7 authentic = true
QC-B valid = true
QC-B signers = W2 + W3
QC-B binds H7
regional replica = R1 / generation 7 / ACTIVE

→ local_quorum_authorized_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

The threshold count is correct. The view is incomplete.

## Quorum intersection exposes the conflict

Cross-view comparison reveals:

```text
QC-A signers = {W1, W2}
QC-B signers = {W2, W3}
intersection = {W2}
```

The overlapping witness `W2` authenticated both H9 and H7 for the same set epoch and logical round.

That converts two independently valid certificates into explicit global conflict evidence:

```text
same witness-set identity = true
same witness-set epoch = 1
same logical round = 50
both certificates locally valid = true
head digests differ = true
intersection = W2
W2 signed both incompatible heads = true

→ conflicting_quorum_certificates
```

## Safe: hold before consequence

The verifier does not choose the larger generation, the older generation, or the branch with the more convenient regional replica.

It holds:

```text
conflicting_quorum_certificates
→ adoption rows = 0
→ external effects = 0
```

The contradiction is the evidence.

## Quarantine and recovery

`W2` is quarantined because its two authentic statements prove equivocation at the quorum intersection.

Re-evaluating the old certificates:

```text
QC-A active non-quarantined signers = {W1}
1 < threshold 2
→ invalid

QC-B active non-quarantined signers = {W3}
1 < threshold 2
→ invalid
```

At fresh round `51`, the remaining non-conflicting witnesses agree on H9:

```text
QC-R51 → H9
W1 + W3
threshold = 2-of-3
W2 quarantined

→ certificate valid
→ local_quorum_authorized_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

Conflict handling therefore removes the disputed round-50 certificates without permanently freezing the system.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Two incompatible local 2-of-3 quorum certificates each validate independently | PASS | 2/2 |
| Isolated verifier accepts local H7 quorum and commits one effect | PASS | 2/2 |
| Cross-view comparison detects conflicting quorum certificates and W2 equivocation | PASS | 2/2 |
| Global conflict guard blocks consequence with zero effects | PASS | 2/2 |
| Quarantine invalidates both old QCs; fresh W1+W3 H9 quorum succeeds once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I99 — LOCAL QUORUM ≠ GLOBALLY CONSISTENT QUORUM**

A threshold certificate proves that enough identities supported one statement inside one observed view. It does not prove that another locally valid threshold certificate for the same logical decision does not exist elsewhere.

# **I100 — QUORUM CERTIFICATE MUST BIND WITNESS-SET IDENTITY, SET EPOCH, LOGICAL ROUND, HEAD IDENTITY, AND DISTINCT SIGNERS**

Without this binding, two certificates cannot be compared as claims about the same trust decision.

# **I101 — CONFLICTING LOCALLY VALID QUORUM CERTIFICATES FOR THE SAME SET EPOCH AND ROUND REQUIRE INTERSECTION / EQUIVOCATION CHECK AND HOLD BEFORE CONSEQUENCE**

The verifier must not select a permissive branch merely because that branch independently satisfies threshold.

# **I102 — EQUIVOCATING INTERSECTION MEMBERS MUST BE QUARANTINED; RESUME ONLY WITH A NON-CONFLICTING THRESHOLD CERTIFICATE THAT EXCLUDES QUARANTINED AUTHORITY**

Recovery must remove the conflicting authority contribution before quorum evidence can authorize consequence again.

## TTP quorum-consistency rule

```text
RECEIVE QUORUM CERTIFICATE QC
        ↓
AUTHENTICATE DISTINCT MEMBER STATEMENTS
        ↓
BIND SET ID + SET EPOCH + ROUND + HEAD
        ↓
CHECK THRESHOLD
        ↓
GOSSIP / CROSS-CHECK CERTIFICATE VIEW
        ↓
CONFLICTING VALID QC FOR SAME SET EPOCH + ROUND?
  ├─ yes
  │    ↓
  │  COMPUTE QUORUM INTERSECTION
  │    ↓
  │  FIND AUTHENTIC CONFLICTING SIGNATURES
  │    ↓
  │  QUARANTINE EQUIVOCATORS
  │    ↓
  │  HOLD / 0 CONSEQUENCE
  └─ no
        ↓
VERIFY HEAD + AUTHORITY VIEW + PROOF
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE QC → GLOBAL CONSISTENCY → HEAD → EFFECT
```

## Relationship to #034–#035

```text
#034 → can one independent witness fork its history?
#035 → can two locally valid witness majorities authorize incompatible histories?
```

The trust recursion now includes quorum topology:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ authority-view currentness
+ authenticated authority-head evidence
+ authority-head anti-rollback
+ checkpoint-storage rollback resistance
+ witness authenticity
+ witness-history consistency
+ quorum-certificate validity
+ cross-view quorum consistency / intersection evidence
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

This benchmark uses a deterministic 3-member / 2-of-3 witness fixture with HMAC-SHA256 test identities. It does not implement or claim a production Byzantine fault tolerant consensus algorithm.

The benchmark explicitly presents both quorum certificates to the safe verifier to model gossip/cross-view comparison. It does not prove network delivery guarantees, synchrony assumptions, consensus liveness, dynamic quorum reconfiguration, or protection against a threshold of colluding malicious witnesses.

Quarantining `W2` while allowing fresh `W1 + W3` to satisfy the unchanged 2-of-3 threshold is a benchmark recovery model, not production membership governance guidance.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/multi-witness-quorum-split-brain-v1.0/`  
Workflow: `.github/workflows/benchmark-multi-witness-quorum-split-brain.yml`  
Machine result: `reports/verified/035-multi-witness-quorum-split-brain/result.json`  
GitHub Actions: `31616232956`

## Verdict

**Two incompatible quorum certificates each independently satisfied the same 2-of-3 witness-set policy at the same epoch and logical round. An isolated verifier shown only the generation-7 certificate accepted it and committed one external effect. Cross-view comparison exposed quorum intersection at W2, whose two authentic statements bound incompatible authority heads, producing `conflicting_quorum_certificates` and zero effects. Quarantining W2 invalidated both disputed certificates, while a fresh non-conflicting W1+W3 generation-9 quorum restored liveness exactly once.**
