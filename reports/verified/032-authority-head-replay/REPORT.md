# RESONANCE Verified Report #032

# Authentic Head Replay / Authority Rollback

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Authority Head Replay v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixture:** deterministic HMAC-SHA256 (test-only)  
**GitHub Actions run:** `31610109195`  
**Job:** `94158970954`  
**Benchmark head SHA:** `22ab35b452a346299ed23630d4204e9b610130cb`  
**Evidence artifact:** `resonance-authority-head-replay-v1.0`  
**Artifact ID:** `9146858780`  
**Artifact digest:** `sha256:7ad4f44a363e0c58609fd797bc2ec29060630f02619d8a4d4541b315317fc57d`

## Result

# **10 / 10 — Authority head anti-rollback protocol passes**

Verified #031 established that a claimed authority head must be authenticated before its generation can be used as freshness evidence. Report #032 asks the next question:

> What if the attacker does not forge anything, but simply replays an older head that is still perfectly authentic?

# **AUTHENTIC HEAD ≠ LATEST HEAD**

## Two authentic heads

The authority history contains two valid authenticated statements:

```text
H7:
generation = 7
R1 = ACTIVE
MAC = valid

H9:
generation = 9
R2 = ACTIVE
MAC = valid
```

No bytes in H7 are modified. Its authentication envelope remains valid forever under the benchmark key unless another currentness mechanism says otherwise.

## Control: H7 before later history is known

With no later trusted checkpoint yet recorded:

```text
trusted high-watermark = 0
region-B = R1 / generation 7 / ACTIVE
H7 = authentic / generation 7
```

The control succeeds:

```text
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

Old does not mean invalid when it is actually current.

## Authority history advances

The verifier later observes authentic H9 and persists:

```text
max_authenticated_generation_seen = 9
```

This is a monotonic trusted checkpoint. Region B is then intentionally returned to the older R1/generation-7 view for the replay experiment.

## Unsafe: authentication-only verifier

The attacker replays H7.

```text
H7 authentication = valid
region-B generation = 7
H7 generation = 7
R1 = ACTIVE
proof generation = 7
```

An authentication-only verifier concludes:

```text
7 >= 7
→ view appears fresh
→ proof_authorized_with_current_head
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

This occurs even though the same verifier has already seen generation 9.

The failure is not forged integrity. It is **authority rollback**.

## Safe: monotonic anti-rollback checkpoint

The safe verifier authenticates H7 first, then compares it to trusted history:

```text
H7 authentic = true
H7 generation = 7
trusted high-watermark = 9

7 < 9
→ authority_head_rollback_detected
→ adoption rows = 0
→ external effects = 0
```

Authentication establishes origin and integrity. The monotonic checkpoint establishes that a lower authentic generation is no longer current enough to authorize consequence.

## Restart durability

The PostgreSQL connection is closed and reopened to model verifier restart. The checkpoint remains:

```text
max_authenticated_generation_seen = 9
```

Replayed authentic H7 still returns:

```text
authority_head_rollback_detected
→ adoption rows = 0
→ effects = 0
```

Anti-rollback state that disappears on restart is not anti-rollback state.

## Fresh H9 control

Region B synchronizes to R2/generation 9 and receives authentic H9:

```text
H9 authentic = true
H9 generation = 9
trusted high-watermark = 9
region-B = R2 / generation 9 / ACTIVE
```

The current path succeeds exactly once:

```text
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Authentic generation-7 control succeeds before later history is known | PASS | 2/2 |
| Authentic old H7 replay fools authentication-only verifier after generation 9 exists | PASS | 2/2 |
| Monotonic checkpoint rejects authentic H7 rollback with zero effects | PASS | 2/2 |
| Durable checkpoint survives verifier restart and still rejects H7 | PASS | 2/2 |
| Fresh authentic H9 with synchronized R2 succeeds exactly once | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I87 — AUTHENTIC HEAD ≠ LATEST HEAD**

Cryptographic authenticity proves who issued a head and that its bytes were not modified. It does not prove that no newer authentic head has been issued.

# **I88 — CURRENTNESS MUST BIND TO MONOTONIC ANTI-ROLLBACK STATE OR AN EQUIVALENT TRUSTED CHECKPOINT**

A verifier that has observed generation `G` must not later authorize consequence from an authenticated generation `< G` without an explicit rollback/recovery protocol.

# **I89 — AN AUTHENTIC HEAD BELOW THE TRUSTED HIGH-WATERMARK MUST FAIL CLOSED BEFORE CONSEQUENCE**

Head authentication and head monotonicity are separate checks. Both must pass before the head can fence authority-view currentness.

# **I90 — ANTI-ROLLBACK STATE MUST SURVIVE VERIFIER RESTART OR BE RECONSTRUCTED FROM TRUSTED WITNESS/CHECKPOINT EVIDENCE**

Restarting a verifier must not erase the history needed to recognize an authentic rollback.

## TTP anti-rollback rule

```text
RECEIVE AUTHORITY HEAD H
        ↓
AUTHENTICATE H
        ↓
READ TRUSTED MONOTONIC CHECKPOINT G*
        ↓
H.generation >= G* ?
  ├─ no → AUTHORITY HEAD ROLLBACK → HOLD
  └─ yes
       ↓
   ADVANCE CHECKPOINT MONOTONICALLY
       ↓
   COMPARE REGIONAL AUTHORITY VIEW
       ↓
   CHECK RULE / PROOF / SCOPE
       ↓
   CURRENT OWNER ADOPTS
       ↓
   FENCED COMMIT
       ↓
PROVE AUTHENTICITY → ANTI-ROLLBACK → VIEW CURRENTNESS → PROOF → EFFECT
```

## Relationship to #030–#032

```text
#030 → is the verifier's authority view current?
#031 → is the evidence used to establish that currentness authentic?
#032 → is that authentic evidence the latest non-rolled-back evidence known to the verifier?
```

The trust chain now includes history explicitly:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ authority-view currentness
+ authenticated authority-head evidence
+ monotonic anti-rollback checkpoint
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The benchmark uses deterministic HMAC-SHA256 with a fixed test key. It is not production PKI or key-management guidance.

The anti-rollback mechanism is a verifier-local durable PostgreSQL high-watermark. Production systems may instead use authenticated transparency checkpoints, independent witnesses, quorum/consensus, secure hardware monotonic state, or another mechanism.

This benchmark does not solve first-contact/bootstrap trust for a verifier that has never observed a later generation, and it does not prove that a single local database is rollback-resistant against storage restore or malicious tampering.

This is not production safety certification or a vulnerability claim against PostgreSQL, HMAC, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/authority-head-replay-v1.0/`  
Workflow: `.github/workflows/benchmark-authority-head-replay.yml`  
Machine result: `reports/verified/032-authority-head-replay/result.json`  
GitHub Actions: `31610109195`

## Verdict

**After the verifier had already observed authentic generation 9, replaying the untouched authentic generation-7 head still passed HMAC and fooled an authentication-only verifier into committing one HTTP effect. Binding currentness to a durable monotonic checkpoint converted the same authentic replay into `authority_head_rollback_detected` with zero effects, survived verifier restart, and still allowed the authentic current generation-9/R2 path to succeed exactly once.**
