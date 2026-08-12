# RESONANCE Verified Report #030

# Revocation Propagation / Stale Proof Registry Split-Brain

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Revocation Propagation v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**GitHub Actions run:** `31603943840`  
**Evidence artifact:** `resonance-revocation-propagation-v1.0`  
**Artifact ID:** `9144285482`  
**Artifact digest:** `sha256:fab0b5b45d82cfad8cdce00913e6e9a269e2c6b4cc139a3be366cea2ced52a9a`

## Result

# **10 / 10 — Revocation propagation protocol passes**

Verified #029 established that a compatibility proof can remain internally valid after its rule authority is revoked. Report #030 asks the distributed-systems question that follows immediately:

> What happens when revocation is authoritative at the origin but has not yet reached every verifier replica?

# **VALIDATION AGAINST A STALE AUTHORITY VIEW ≠ CURRENT AUTHORIZATION**

## Topology

```text
                 authoritative origin
                 R1 / generation 8 / REVOKED
                         │
              ┌──────────┴──────────┐
              │                     │
       region-A replica      region-B replica
       gen 8 / REVOKED       gen 7 / ACTIVE
              │                     │
           REJECT                 ACCEPT ❌
```

The same proof, artifact, model bindings and semantic compatibility predicate are presented to both regional verifiers.

The only difference is authority-view freshness.

## Synchronized control

Before revocation, origin and region B are synchronized:

```text
origin head = 7
region-B = R1 / ACTIVE / generation 7
proof = R1 / generation 7
```

The verifier requires its regional view to meet the authoritative generation watermark:

```text
authority_view_fresh = true
rule_active = true
rule_generation = true

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

A regional authority view is usable when its currentness is itself established.

## Split-brain after revocation

The origin advances:

```text
origin head: 7 → 8
R1: ACTIVE → REVOKED
successor: R2
```

Revocation reaches region A but not region B:

```text
region-A:
R1 / generation 8 / REVOKED

region-B:
R1 / generation 7 / ACTIVE
```

Both inspect the exact same historical proof issued under R1 generation 7.

### Region A

```text
rule_active = false
rule_generation = false

→ compatibility_proof_revoked
→ REJECT
```

### Region B — unsafe replica-only decision

```text
rule_active = true
rule_generation = true
static proof bindings = valid
predicate = true

→ regional_proof_authorized
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
```

The result remains numerically correct at `30`. The consequence is nevertheless unauthorized by current origin authority.

The distributed failure is therefore not semantic drift. It is **authority split-brain**.

## Safe: authoritative generation watermark

A safer verifier does not need the complete revocation payload before refusing stale authority. It only needs evidence that a newer authoritative generation exists.

Region B still has:

```text
replica generation = 7
status = ACTIVE
```

But authoritative head is:

```text
generation = 8
```

The safe decision becomes:

```text
authority_view_fresh = false

→ stale_authority_view
→ adoption rows = 0
→ external effects = 0
```

This converts replication delay into **HOLD**, not stale authorization.

## Propagation restores convergence

After generation 8 propagates to region B:

```text
region-B:
R1 / generation 8 / REVOKED
```

The same proof now returns:

```text
compatibility_proof_revoked
→ adoption rows = 0
→ effects = 0
```

Regional verdicts converge only after authority propagation catches up.

## Fresh successor after propagation

The authority then advances to active successor R2:

```text
origin head = 9
R2 = ACTIVE / generation 9
region-B syncs generation 9
```

A fresh R2 proof binds the same model transition and current compatible state:

```text
authority_view_fresh = true
rule_active = true
rule_generation = true

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

The historical artifact can survive the revocation event, but only through fresh proof authority and a current regional authority view.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Synchronized active regional replica authorizes current proof | PASS | 2/2 |
| Same proof gets split-brain verdicts; stale region commits after origin revocation | PASS | 2/2 |
| Authoritative generation watermark blocks stale replica before effect | PASS | 2/2 |
| Revocation propagation converges stale regional verifier to reject | PASS | 2/2 |
| Fresh successor proof succeeds after generation 9 propagation | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I79 — VALIDATION AGAINST A STALE AUTHORITY VIEW ≠ CURRENT AUTHORIZATION**

A verifier can be internally consistent with its local replica and still be wrong about current authority.

# **I80 — REVOCATION PROPAGATION IS PART OF THE CONSEQUENCE SAFETY BOUNDARY**

Publishing a revocation at the origin is insufficient if consequential verifiers can continue authorizing from stale replicas.

# **I81 — REGIONAL AUTHORITY VIEWS MUST PROVE CURRENTNESS AGAINST A MONOTONIC AUTHORITATIVE GENERATION OR HOLD**

If a verifier knows that a newer authority generation exists but has not received it, stale local `ACTIVE` state must not authorize consequence.

# **I82 — SPLIT-BRAIN AUTHORITY VERDICTS REQUIRE FAIL-CLOSED RECONCILIATION BEFORE CONSEQUENCE**

When verifier authority views disagree or currentness is unknown, the safe state is hold/reconcile rather than choose the permissive view.

## TTP revocation-propagation rule

```text
PROOF P
  ↓
READ REGIONAL AUTHORITY VIEW V_local
  ↓
RESOLVE / VERIFY AUTHORITATIVE GENERATION G_now
  ↓
V_local.generation >= G_now ?
  ├─ no → STALE AUTHORITY VIEW → HOLD
  └─ yes
       ↓
   CHECK RULE STATUS / DIGEST / GENERATION
       ↓
   ACTIVE + CURRENT?
     ├─ no → REJECT / REPROVE
     └─ yes
          ↓
      EVALUATE PROOF SCOPE NOW
          ↓
      CURRENT OWNER ADOPTS
          ↓
      FENCED COMMIT
          ↓
PROVE ORIGIN → PROPAGATION → VIEW CURRENTNESS → PROOF → EFFECT
```

## Relationship to #028–#030

```text
#028 → can two model versions be compatibly reused for this scope?
#029 → is the compatibility proof still authorized now?
#030 → is the verifier's view of that proof authority itself current?
```

The broader trust chain now includes distributed authority propagation:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ authority-view currentness / propagation evidence
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

This benchmark models an authoritative origin, two regional authority replicas and a monotonic generation watermark in PostgreSQL. It does not define a universal consensus protocol, guarantee bounded real-world replication latency, or certify external distributed systems.

The unsafe path deliberately uses a semantically correct artifact to isolate stale authority-view authorization from result correctness.

This is not production safety certification or a vulnerability claim against PostgreSQL or another external product.

## Reproducibility

Benchmark: `benchmarks/revocation-propagation-v1.0/`  
Workflow: `.github/workflows/benchmark-revocation-propagation.yml`  
Machine result: `reports/verified/030-revocation-propagation/result.json`  
GitHub Actions: `31603943840`

## Verdict

**After R1 was revoked at authoritative generation 8, region A had already converged to REVOKED while region B still reported ACTIVE at generation 7. The exact same proof was rejected by region A and accepted by region B, whose stale replica then authorized an HTTP effect. Requiring the regional view to meet the authoritative generation watermark converted the same lag into `stale_authority_view` with zero effects. Once revocation propagated, region B converged to rejection, and a fresh active R2 proof at generation 9 safely re-authorized the historical artifact.**
