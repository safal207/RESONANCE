# RESONANCE Verified Report #023

# Result Handoff / Stale Work Salvage

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Result Handoff / Stale Work Salvage v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource with persistent SQLite effect/fence ledger  
**GitHub Actions run:** `31580229908`  
**Evidence artifact:** `resonance-result-handoff-stale-work-v1.0`  
**Artifact ID:** `9134843992`  
**Artifact digest:** `sha256:315f2b156339a19de87380dac57c28047a950384350cdca087a4c2be27dabe38`

## Result

# **10 / 10 — Stale-work handoff protocol passes**

Verified #022 showed that a worker can be authorized when work starts and still lose commit authority before the work finishes. Report #023 asks the next practical question:

> Must useful work from that stale executor be thrown away, or can the current owner safely adopt it?

The benchmark shows that the data can be salvaged if result production and consequence authority are separated.

## Timeline

```text
T=1000
A acquires lease
owner=A / fence=1 / version=1 / expires=1060

T=1020
A is authorized and starts work

T=1070
A expires
B takes over
owner=B / fence=2 / version=2 / expires=1130

T=1080
A finishes useful result artifact D
A is stale, but D can still exist as data

T=1085
B may explicitly adopt D
```

## Unsafe: stale result auto-publishes itself

The stale producer finished artifact D and immediately published it with its old execution context. The external boundary did not enforce fencing for that call:

```text
A / fence 1 / artifact D
→ HTTP 200
→ effect #1
```

B then legitimately adopted the exact same digest and committed it under fence `2`:

```text
B / fence 2 / same artifact D
→ effect #2
```

Final remote state:

```text
effect_count = 2
status = conflict
same artifact digest = true
```

# **DATA PRODUCTION ≠ CONSEQUENCE AUTHORITY**

The artifact may be useful and correct. The stale producer still does not own publication authority.

## Safe: preserve first, adopt second

The safe path stores the result with immutable provenance:

```text
artifact_digest
producer_worker=A
producer_fence=1
producer_lease_version=1
produced_at=1080
status=PRODUCED
```

Before adoption the external effect count is exactly zero.

B then performs a conditional PostgreSQL adoption transition bound to:

```text
exact artifact digest
+ producer identity
+ producer fence
+ current owner B
+ current fence 2
+ current lease version 2
+ current lease validity
```

The artifact transitions:

```text
PRODUCED
→ ADOPTED
adopted_by=B
adopted_fence=2
```

Only after that does B commit the consequence using fence `2`.

Final remote state:

```text
effect_count = 1
status = committed
```

## Stale producer still cannot publish later

After B's adopted commit, A attempted to publish the same artifact with fence `1`.

The resource had already accepted fence `2`:

```text
presented fence = 1
highest fence = 2
→ HTTP 409
→ fenced_out
→ effect_count = 1
```

## Digest binding matters

The benchmark also altered one character in the digest before adoption.

```text
wrong digest adoption → 0 rows
exact digest adoption → 1 row
```

The correct artifact was then committed once by B.

This makes the handoff about a specific immutable result, not a vague request to “reuse A's work.”

## Control

A worker that remains current may produce, adopt and commit its own artifact normally:

```text
start_authorized = true
self-adoption rows = 1
HTTP 200
final effect_count = 1
```

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Stale result preserved as immutable data with producer epoch | PASS | 2/2 |
| Stale auto-publish + current-owner adoption duplicates same artifact | PASS | 2/2 |
| Current owner explicitly adopts stale result and commits once | PASS | 2/2 |
| Wrong digest and stale producer paths are blocked | PASS | 2/2 |
| Current owner can self-adopt valid result | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE**

# **RESULT HANDOFF MUST BIND ARTIFACT DIGEST + PRODUCER EPOCH + CURRENT ADOPTER EPOCH**

# **ADOPTION IS A NEW AUTHORITY TRANSITION, NOT A RETROACTIVE EXTENSION OF PRODUCER AUTHORITY**

# **THE CONSEQUENTIAL COMMIT MUST PRESENT THE CURRENT ADOPTER FENCING TOKEN**

## Canonical handoff path

```text
AUTHORIZE A / FENCE N
        ↓
RUN WORK
        ↓
OWNERSHIP CHANGES
        ↓
A FINISHES ARTIFACT D
        ↓
STORE D + PRODUCER PROVENANCE
        ↓
NO CONSEQUENCE YET
        ↓
CURRENT OWNER B OBSERVES D
        ↓
ADOPT D
bind digest + producer epoch + B/current epoch
        ↓
COMMIT WITH B'S FENCE N+1
        ↓
RESOURCE FENCE CHECK
        ↓
PROVE PRODUCER → ADOPTER → EFFECT
```

## Broader rule

```text
RESULT TRUST =
  artifact integrity
+ producer provenance
+ explicit current-owner adoption
+ current commit authority
+ resource-side fencing
+ evidence
```

## Interpretation boundary

This is a deterministic local benchmark. PostgreSQL represents coordination/adoption authority and a separate Dockerized HTTP service represents the consequential resource. Logical timestamps are benchmark inputs.

It does **not** claim:

- a vulnerability in PostgreSQL or another external product;
- that all stale computation is safe to reuse;
- semantic correctness of arbitrary produced artifacts;
- exactly-once execution;
- a universal distributed scheduler or work-stealing algorithm;
- production safety certification;
- arbitrary agent safety.

The benchmark verifies authority/provenance mechanics, not the truth or quality of the artifact payload itself.

## Reproducibility

- Benchmark: `benchmarks/result-handoff-stale-work-v1.0/`
- Workflow: `.github/workflows/benchmark-result-handoff-stale-work.yml`
- Machine result: `reports/verified/023-result-handoff-stale-work/result.json`
- GitHub Actions run: `31580229908`

## Verdict

**Worker A lost execution authority but still completed a useful immutable artifact. Allowing that stale producer to auto-publish caused the same artifact to create two effects once current owner B later adopted it. Preserving the artifact as data, binding adoption to the exact digest and both producer/current-owner epochs, and committing only with B's current fencing token preserved one effect.**

---

**RESONANCE Verified Report #023**  
**Score:** 10/10  
**Unsafe effects:** 2  
**Safe adopted effects:** 1  
**Wrong-digest adoption:** 0 rows  
**Stale late publish:** HTTP 409 / fenced_out  
**Vulnerability claim:** No  
**External safety certification:** No
