# RESONANCE Verified Report #033

# Checkpoint Storage Rollback / Restored Verifier State

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Checkpoint Storage Rollback v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixtures:** deterministic HMAC-SHA256 authority head + independent checkpoint witness (test-only)  
**GitHub Actions run:** `31613901719`  
**Job:** `94171789427`  
**Benchmark head SHA:** `87a6016e4f09748eab2586c00dc4309bf5f65cc4`  
**Evidence artifact:** `resonance-checkpoint-storage-rollback-v1.0`  
**Artifact ID:** `9148374663`  
**Artifact digest:** `sha256:2e2c598472898952094c0f14e0238d436ed019c0f5fed457fb190fa12ea9771b`

## Result

# **10 / 10 — Checkpoint rollback resistance protocol passes**

Verified #032 established that an authentic authority head below a verifier's monotonic high-watermark must fail closed. Report #033 attacks the high-watermark itself:

> What if the verifier really reached generation 9, but its supposedly durable checkpoint storage is restored from an older snapshot containing generation 7?

# **DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT**

## Baseline

Before later history exists, generation 7 is legitimate:

```text
H7 authentic = true
local checkpoint = 7
region-B = R1 / generation 7 / ACTIVE

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

At this point the benchmark captures a backup snapshot `S7` of the verifier-local checkpoint row.

## Trust history advances

The verifier then observes authentic H9:

```text
local checkpoint:
7 → 9

H9 digest:
sha256:8c85ea75094f2dd5dbb0195f25d400856750dbdd3e54b15e14a13a2ae320c131
```

An independent witness also authenticates generation 9:

```text
witness = witness-A
witness generation = 9
witness head_digest = digest(H9)
witness MAC = valid
```

The local verifier and external witness therefore agree that authority history has reached at least generation 9.

## Storage restore

The benchmark explicitly restores the verifier-local checkpoint from `S7`:

```text
before restore: local checkpoint = 9
restored snapshot: checkpoint = 7
after restore: local checkpoint = 7

external witness W9 remains = 9
```

The database row is durable. It is simply durable state from the past.

## Unsafe: local-only anti-rollback

The attacker now replays untouched authentic H7 while region B is also on generation 7.

The local-only verifier sees:

```text
H7 authentic = true
H7 generation = 7
local checkpoint = 7
regional generation = 7

7 >= 7
→ proof_authorized_with_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

Every local anti-rollback check passes because the memory used by that check was itself rolled back.

The failure is not head forgery and not loss of durability. It is **rollback of trusted verifier history**.

## Safe: witness-aware storage guard

Before using the restored local checkpoint to authorize consequence, the verifier compares it with independently authenticated witness W9:

```text
local checkpoint = 7
witness W9 authentic = true
witness generation = 9
witness head_digest == digest(H9)

7 < 9
→ checkpoint_storage_rollback_detected
→ adoption rows = 0
→ external effects = 0
```

The verifier does not choose between H7 and H9 yet. It first declares its own local trust state unfit for consequence.

## Reconstruction

The trusted witness statement is then used to reconstruct the verifier checkpoint:

```text
local checkpoint:
7 → 9

reason:
checkpoint_reconstructed_from_witness
```

Replaying the same authentic H7 after reconstruction now returns:

```text
H7 authentic = true
H7 generation = 7
local checkpoint = 9

7 < 9
→ authority_head_rollback_detected
→ adoption rows = 0
→ effects = 0
```

This separates two different failures:

```text
checkpoint storage rollback
        ↓ reconstruct verifier history
old authority head replay
        ↓ reject head below restored history
```

## Fresh H9 control

After region B synchronizes to R2/generation 9:

```text
H9 authentic = true
local checkpoint = 9
region-B = R2 / generation 9 / ACTIVE

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

Recovery does not permanently freeze the verifier. Current authority still succeeds exactly once.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Generation-7 checkpoint control succeeds before later history | PASS | 2/2 |
| Local checkpoint advances to 9, restores to 7, while authenticated witness remains at 9 | PASS | 2/2 |
| Local-only verifier accepts authentic H7 after restored checkpoint and commits one effect | PASS | 2/2 |
| Witness guard detects storage rollback, blocks effects, reconstructs 9, then rejects H7 | PASS | 2/2 |
| Fresh authentic H9 succeeds exactly once after reconstruction | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I91 — DURABLE CHECKPOINT ≠ ROLLBACK-RESISTANT CHECKPOINT**

Persistence across normal restart does not prove that storage recovery, snapshot restore, replica rewind, or administrative recovery cannot move trusted history backward.

# **I92 — VERIFIER STATE RECOVERY MUST NOT MOVE TRUST HISTORY BACKWARD**

After recovery, restored trust state must be reconciled against a monotonic trusted reference before it can authorize consequence.

# **I93 — A LOCAL CHECKPOINT BELOW AN AUTHENTICATED INDEPENDENT HIGH-WATERMARK IS STORAGE-ROLLBACK EVIDENCE**

The local checkpoint is not merely stale data; it is evidence that the verifier's own trust history has regressed relative to an authenticated external observation.

# **I94 — AFTER CHECKPOINT ROLLBACK, RECONSTRUCT TRUST STATE FROM INDEPENDENT EVIDENCE BEFORE AUTHORIZING CONSEQUENCE**

Fail closed first. Reconstruct or reconcile the trusted high-watermark. Only then resume ordinary authority-head currentness checks.

## TTP checkpoint rollback-resistance rule

```text
RECOVER / START VERIFIER
        ↓
READ LOCAL CHECKPOINT G_local
        ↓
RESOLVE AUTHENTICATED INDEPENDENT CHECKPOINT G_ext
        ↓
G_local >= G_ext ?
  ├─ no → CHECKPOINT STORAGE ROLLBACK → HOLD
  │          ↓
  │      RECONSTRUCT / RECONCILE TRUST HISTORY
  │          ↓
  │      persist monotonic checkpoint
  └─ yes
        ↓
RECEIVE + AUTHENTICATE AUTHORITY HEAD H
        ↓
H.generation >= trusted checkpoint ?
  ├─ no → AUTHORITY HEAD ROLLBACK → HOLD
  └─ yes → continue authority/proof checks
        ↓
CURRENT OWNER ADOPTS
        ↓
FENCED COMMIT
        ↓
PROVE STORAGE CURRENTNESS → HEAD CURRENTNESS → PROOF → EFFECT
```

## Relationship to #031–#033

```text
#031 → is authority-head freshness evidence authentic?
#032 → is authentic head evidence non-rolled-back relative to verifier history?
#033 → is verifier history itself non-rolled-back relative to independent history?
```

The trust chain now includes a second-order memory check:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ authority-view currentness
+ authenticated authority-head evidence
+ monotonic head anti-rollback
+ checkpoint-storage rollback resistance / reconstruction evidence
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The benchmark models restore by explicitly replacing the verifier-local PostgreSQL checkpoint row with a previously captured generation-7 snapshot. It does not test PostgreSQL backup tooling or claim a PostgreSQL vulnerability.

The independent witness is a deterministic HMAC-SHA256 fixture using a separate benchmark key. It is not production PKI, a transparency log, secure hardware, consensus, or a production witness network.

The benchmark assumes W9 itself remains authentic, available, and outside the restored verifier-state domain. Witness rollback, witness equivocation, quorum disagreement, first-contact/bootstrap trust, malicious storage, and restoration of both verifier and witness state are separate verification surfaces.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, Docker, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/checkpoint-storage-rollback-v1.0/`  
Workflow: `.github/workflows/benchmark-checkpoint-storage-rollback.yml`  
Machine result: `reports/verified/033-checkpoint-storage-rollback/result.json`  
GitHub Actions: `31613901719`

## Verdict

**The verifier first advanced its durable local authority checkpoint from generation 7 to generation 9, then an explicit state restore moved that checkpoint back to 7. With its own trust memory rolled back, a local-only anti-rollback verifier accepted untouched authentic H7 and committed one external effect. Comparing restored local state with independently authenticated witness W9 detected `checkpoint_storage_rollback_detected` before consequence, reconstructed the checkpoint to 9, converted the same H7 into `authority_head_rollback_detected` with zero effects, and still allowed fresh H9/R2 to succeed exactly once.**
