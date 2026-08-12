# RESONANCE Verified Report #031

# Authority Head Authenticity / Forged Freshness Watermark

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Authority Head Authenticity v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP effect resource  
**Authentication fixture:** deterministic HMAC-SHA256 (test-only)  
**GitHub Actions run:** `31605405137`  
**Benchmark head SHA:** `10e3ee2057fc5efe626e317764374a6eef006f60`  
**Evidence artifact:** `resonance-authority-head-authenticity-v1.0`  
**Artifact ID:** `9144883220`  
**Artifact digest:** `sha256:a9dd4504ae0f88f6caf5c2dc8dc896598515beed3ed4ebbbe2bdf5976b1a1d43`

## Result

# **10 / 10 — Authority head authenticity protocol passes**

Verified #030 established that regional proof-authority views must prove currentness against an authoritative generation watermark. Report #031 asks the next trust question:

> What if the claimed authoritative head itself is forged or modified in transit?

# **FRESHNESS CLAIM ≠ AUTHENTIC FRESHNESS EVIDENCE**

## Control: authentic current head

Before revocation:

```text
R1 = ACTIVE / generation 7
region-B = ACTIVE / generation 7
proof = R1 / generation 7
```

Origin emits an authenticated head statement binding:

```text
authority_namespace = resonance-proof-authority
generation = 7
rule_id = cap-equivalence-r1
rule_digest = sha256:b26ca0...
status = ACTIVE
```

The benchmark HMAC verifies and the regional view is synchronized:

```text
authority_head_authentic = true
authority_view_fresh = true
rule_active = true
rule_generation = true

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Origin advances to generation 8

The authoritative state becomes:

```text
generation = 8
R1 = REVOKED
successor = R2
```

Region B is intentionally stale:

```text
region-B:
R1 = ACTIVE / generation 7
```

The authentic generation-8 head has MAC:

```text
8f4f93434c40b01bf8ea6b79ed6b6fcc651807529b5d41e33db41232b5af53a6
```

## Forged watermark

A broken or hostile intermediary mutates the signed payload:

```text
before:
generation = 8
status = REVOKED
successor = R2

forged:
generation = 7
status = ACTIVE
successor = null
```

The attacker keeps the old generation-8 MAC instead of recomputing it.

Therefore:

```text
forged_head_authenticates = false
```

## Unsafe: trust the number, not the evidence

An unsafe verifier does not authenticate the head. It observes only:

```text
regional generation = 7
claimed head generation = 7
regional R1 = ACTIVE
proof generation = 7

→ looks fresh
```

It then produces:

```text
→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

The numeric result remains correct. The authorization path is not.

The verifier was tricked into treating a stale authority replica as current by a forged freshness claim.

## Safe: authenticate before freshness

The safe verifier receives the exact same forged head but validates:

```text
algorithm
key identity
authority namespace
canonical signed payload
MAC
```

The modified payload no longer matches its MAC:

```text
authority_head_authentic = false

→ authority_head_authentication_failed
→ adoption rows = 0
→ external effects = 0
```

Crucially, the verifier fails before using the claimed generation as a freshness fence.

## Authentic generation 8 exposes the stale replica

When the authentic head is presented:

```text
head generation = 8 / authenticated
region-B generation = 7

→ stale_authority_view
→ adoption rows = 0
→ effects = 0
```

After revocation propagates to region B:

```text
region-B = R1 / generation 8 / REVOKED

→ compatibility_proof_revoked
→ adoption rows = 0
→ effects = 0
```

## Fresh successor control

The authority advances again:

```text
R2 = ACTIVE / generation 9
region-B = R2 / generation 9
```

A fresh R2 proof plus authentic generation-9 head succeeds:

```text
authority_head_authentic = true
authority_view_fresh = true
rule_active = true
rule_generation = true

→ adoption rows = 1
→ HTTP 200
→ effect_count = 1
→ output = 30
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Authentic current head authorizes synchronized active replica | PASS | 2/2 |
| Unauthenticated forged head makes stale replica look fresh and commit | PASS | 2/2 |
| Authenticated verifier rejects forged head with zero effects | PASS | 2/2 |
| Authentic generation-8 head exposes stale view, then propagation converges to revoked | PASS | 2/2 |
| Fresh successor proof with authentic generation-9 head succeeds | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I83 — FRESHNESS CLAIM ≠ AUTHENTIC FRESHNESS EVIDENCE**

A claimed generation number cannot safely fence consequence until its authority and integrity are established.

# **I84 — AUTHORITY HEAD IDENTITY, DOMAIN, GENERATION, AND CONTENT MUST BE AUTHENTICATED BEFORE THEY CAN FENCE A CONSEQUENCE**

A valid authentication envelope must bind the exact authority namespace and head contents, not merely a detached number.

# **I85 — UNAUTHENTICATED OR TAMPERED AUTHORITY HEAD → HOLD BEFORE REGIONAL FRESHNESS EVALUATION**

Do not evaluate `replica_generation >= claimed_head_generation` using an untrusted head claim.

# **I86 — AUTHENTIC HEAD EVIDENCE CAN FENCE A STALE REPLICA, BUT AUTHENTIC OLD-HEAD REPLAY REQUIRES AN ADDITIONAL MONOTONICITY MECHANISM**

Authenticity establishes who produced a statement and whether it was modified. It does not by itself prove that an authentic historical head is the newest head ever issued.

## TTP authority-head rule

```text
RECEIVE AUTHORITY HEAD H
        ↓
AUTHENTICATE
- trusted key / signer
- authority namespace
- canonical payload
- integrity / signature
        ↓
 authentic?
 ├─ no → HOLD / REJECT HEAD
 └─ yes
      ↓
   EXTRACT GENERATION G
      ↓
   COMPARE REGIONAL VIEW >= G
      ├─ no → STALE AUTHORITY VIEW → HOLD
      └─ yes
           ↓
       CHECK RULE STATUS / DIGEST / GENERATION
           ↓
       CHECK PROOF + SCOPE
           ↓
       CURRENT OWNER ADOPTS
           ↓
       FENCED COMMIT
           ↓
PROVE HEAD AUTHENTICITY → VIEW CURRENTNESS → PROOF AUTHORITY → EFFECT
```

## Relationship to #029–#031

```text
#029 → is the compatibility proof still authorized?
#030 → is the verifier's authority view current?
#031 → is the freshness evidence used to prove that currentness authentic?
```

The trust chain now becomes:

```text
CAUSAL APPLICABILITY =
  model identity/currentness/completeness
+ scoped compatibility proof when needed
+ proof-authority currentness
+ authority-view currentness
+ authenticated authority-head evidence
+ dependency/state evidence
+ current execution authority
+ fenced consequence
+ end-to-end proof
```

## Interpretation boundary

The benchmark uses deterministic HMAC-SHA256 with a fixed test key to isolate head authentication and payload binding. It is not a production PKI, key-management architecture, or external security certification.

The benchmark deliberately does **not** solve replay of an older but still authentic signed head. That requires a separate monotonicity, witness, checkpoint, transparency, or equivalent currentness mechanism.

This is not a vulnerability claim against PostgreSQL, HMAC, GitHub Actions, or another external product.

## Reproducibility

Benchmark: `benchmarks/authority-head-authenticity-v1.0/`  
Workflow: `.github/workflows/benchmark-authority-head-authenticity.yml`  
Machine result: `reports/verified/031-authority-head-authenticity/result.json`  
GitHub Actions: `31605405137`

## Verdict

**After the authority advanced to signed generation 8 and revoked R1, a stale region remained at ACTIVE generation 7. Mutating the signed head payload back to generation 7 made the replica appear fresh to an unauthenticated verifier, which adopted the proof and committed an HTTP effect. The authenticated verifier rejected the exact same forged head with zero effects. The authentic generation-8 head then correctly fenced the stale replica, propagation converged R1 to revoked, and a fresh authenticated generation-9 R2 path succeeded.**
