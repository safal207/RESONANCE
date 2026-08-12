# RESONANCE Verified Report #034

# Witness Rollback / Equivocation

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Witness Rollback / Equivocation v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head + two witness identities (test-only)  
**GitHub Actions run:** `31615206797`  
**Job:** `94176189614`  
**Benchmark head SHA:** `6021d88d946e1e91b54a8c64b4bd8c1ed2f48668`  
**Evidence artifact:** `resonance-witness-equivocation-v1.0`  
**Artifact ID:** `9148905171`  
**Artifact digest:** `sha256:05b958a9d258fbdc8dfd5c0d5680782ce01f12ee66c486b315299471913b0036`

## Result

# **10 / 10 — Witness consistency protocol passes**

Verified #033 used an independently authenticated witness to recover verifier history after local checkpoint rollback. Report #034 attacks that witness assumption:

> What if the witness is independent from verifier storage, but the witness itself signs two incompatible histories for different verifiers?

# **INDEPENDENT WITNESS ≠ CONSISTENT WITNESS**

## Common history

`witness-A` first signs a legitimate generation-7 checkpoint:

```text
WA42
witness_id = witness-A
witness_seq = 42
generation = 7
head_digest = digest(H7)
MAC = valid
```

Before any conflicting evidence exists, H7 + WA42 + the generation-7 R1 replica succeeds:

```text
→ witness_authorized_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

## The fork

At the next witness sequence, `witness-A` signs two different children of the same parent:

```text
WA43-good
witness_id = witness-A
witness_seq = 43
previous_statement_digest = digest(WA42)
generation = 9
head_digest = digest(H9)
MAC = valid

digest =
sha256:eff4494cb8544511685c81777d685b80fac39d25ffb64a926d215907e23223c4
```

and:

```text
WA43-fork
witness_id = witness-A
witness_seq = 43
previous_statement_digest = digest(WA42)
generation = 7
head_digest = digest(H7)
MAC = valid

digest =
sha256:06b885e6193a56a0c18bcd569b8c8d80a15271a6596e1c88a2daf3ebc4843c2e
```

Both statements authenticate successfully under the same witness identity.

They cannot both be a single linear witness history.

## Unsafe: isolated verifier

Verifier B sees only `WA43-fork`.

Its local world is internally consistent:

```text
local checkpoint = 7
H7 authentic = true
WA43-fork authentic = true
WA43-fork binds H7
regional replica = R1 / generation 7 / ACTIVE
```

The isolated verifier concludes:

```text
→ witness_authorized_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

No MAC failed. No local comparison failed. The verifier simply did not possess the other branch.

The failure is **witness equivocation hidden by view isolation**.

## Safe: gossip / cross-view consistency

The two signed witness-A statements are compared before consequence:

```text
same witness_id = true
same witness_seq = 43
same parent = true
both authentic = true
statement digests differ = true

→ witness_equivocation_detected
→ adoption rows = 0
→ external effects = 0
→ quarantine witness-A
```

The contradiction itself becomes evidence.

The verifier does not guess which branch is honest.

## Recovery from a non-conflicting witness

A second identity, `witness-B`, independently authenticates H9:

```text
WB11
witness_id = witness-B
witness_seq = 11
generation = 9
head_digest = digest(H9)
MAC = valid
```

After witness-A is quarantined, verifier B reconstructs its checkpoint:

```text
checkpoint:
7 → 9

reason:
checkpoint_reconstructed_from_independent_witness
```

The old H7 is now rejected:

```text
H7 generation = 7
trusted checkpoint = 9

7 < 9
→ authority_head_rollback_detected
```

After the regional replica synchronizes to R2/generation 9, H9 + WB11 succeeds exactly once:

```text
→ witness_authorized_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Baseline witness statement authorizes generation 7 before conflict exists | PASS | 2/2 |
| Same witness signs two authentic conflicting children at one sequence and parent | PASS | 2/2 |
| Isolated verifier accepts authentic fork and commits one effect | PASS | 2/2 |
| Gossip detects equivocation, quarantines witness, and blocks consequence | PASS | 2/2 |
| Independent witness reconstructs generation 9; H7 rejects; H9 succeeds once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I95 — INDEPENDENT WITNESS ≠ CONSISTENT WITNESS**

A witness can be outside the verifier's storage failure domain and still present inconsistent authenticated histories.

# **I96 — AUTHENTIC WITNESS STATEMENT ≠ UNIQUE WITNESS HISTORY**

Signature or MAC validity proves statement origin and integrity, not that the witness issued only one statement for that logical history position.

# **I97 — SAME WITNESS SEQUENCE + SAME PARENT + DIFFERENT AUTHENTIC CONTENT = EQUIVOCATION EVIDENCE**

A verifier that obtains such a pair must not choose the more permissive branch. The fork itself is a trust conflict.

# **I98 — EQUIVOCATING WITNESS MUST BE QUARANTINED; RECONSTRUCT TRUST FROM NON-CONFLICTING INDEPENDENT EVIDENCE BEFORE CONSEQUENCE**

Recovery must not let the conflicted witness remain the sole authority for choosing which branch survives.

## TTP witness-consistency rule

```text
RECEIVE WITNESS STATEMENT W
        ↓
AUTHENTICATE W
        ↓
BIND witness_id + sequence + parent + head_digest
        ↓
GOSSIP / CROSS-CHECK WITNESS VIEW
        ↓
conflicting authentic statement
for same witness sequence + parent?
  ├─ yes → WITNESS EQUIVOCATION → HOLD
  │          ↓
  │      QUARANTINE WITNESS
  │          ↓
  │      RESOLVE NON-CONFLICTING INDEPENDENT EVIDENCE
  │          ↓
  │      RECONSTRUCT TRUST CHECKPOINT
  └─ no
        ↓
VERIFY WITNESS → HEAD → LOCAL CHECKPOINT
        ↓
VERIFY AUTHORITY VIEW / RULE / PROOF
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE WITNESS CONSISTENCY → CHECKPOINT → HEAD → EFFECT
```

## Relationship to #032–#034

```text
#032 → can an authentic old authority head be replayed?
#033 → can the verifier's own checkpoint memory be restored backward?
#034 → can the independent witness itself fork the history used for recovery?
```

The trust recursion now includes witness-history consistency:

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
+ witness-history consistency / equivocation evidence
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The benchmark uses deterministic HMAC-SHA256 keys as test identities. It is not production PKI or key-management guidance.

Gossip/cross-checking is modeled by explicitly presenting the two authenticated witness-A statements to one verifier. The benchmark does not implement a production transparency log, Byzantine consensus, distributed gossip network, or quorum protocol.

`witness-B` is intentionally non-conflicting in this fixture. The benchmark does not prove that one replacement witness is sufficient in production, nor does it solve quorum corruption, correlated compromise, first-contact trust, witness-set rotation, or conflicting majorities.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/witness-equivocation-v1.0/`  
Workflow: `.github/workflows/benchmark-witness-equivocation.yml`  
Machine result: `reports/verified/034-witness-equivocation/result.json`  
GitHub Actions: `31615206797`

## Verdict

**The same independent witness authenticated two different children of the same witness sequence and parent: one bound generation 9/H9 and the other generation 7/H7. Both MACs were valid. An isolated verifier shown only the generation-7 fork accepted it and committed one external effect. Cross-view comparison converted the two individually valid statements into `witness_equivocation_detected`, blocked consequence with zero effects, quarantined witness-A, reconstructed the checkpoint to generation 9 from non-conflicting witness-B, rejected H7 as rollback, and still allowed the fresh H9 path exactly once.**
