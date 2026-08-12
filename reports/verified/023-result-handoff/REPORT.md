# RESONANCE Verified Report #023

# Result Handoff / Stale Work Salvage

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Result Handoff / Stale Work Salvage v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource with persistent SQLite effect state  
**GitHub Actions run:** `31555333762`  
**Evidence artifact:** `resonance-result-handoff-v1.0`  
**Artifact ID:** `9125787638`  
**Artifact digest:** `sha256:c1f43812e27e29f8ae9dd2152884071bba4c807d8cc3cb94a0731c679cd38af9`

## Result

# **10 / 10 — Result-handoff adoption protocol passes**

Verified #022 established that a worker can be valid at start and stale at commit. Report #023 asks a different question:

> If the stale worker nevertheless finished useful computation, must that work be discarded — or can the current owner safely adopt it?

The benchmark shows that useful output can be preserved if **artifact production**, **artifact adoption**, and **consequential commit** are treated as separate transitions.

## Timeline

```text
Worker A / fence 1
      ↓
AUTHORIZED START
      ↓
compute begins
      ↓
lease expires
      ↓
Worker B takeover / fence 2
      ↓
A finishes immutable artifact digest D
```

The artifact remains potentially useful. What A lost is the right to publish its consequence.

## Unsafe: stale artifact auto-publishes

A produced:

```text
state = READY
producer = worker-A
producer_fence = 1
artifact_digest = be61d2051f582c57e0a96bfa4a90bcc85266e2cc3164a373cd621f709e20a993
```

The unsafe path treated READY as implicit publish authority. A's stale producer epoch auto-published the result and created external effect #1.

B then explicitly adopted the same digest as current owner / fence 2 and published it normally:

```text
A / fence 1 / digest D → effect #1
B / fence 2 / digest D → effect #2

final:
effect_count = 2
status = conflict
```

The output was identical. The consequence happened twice because data possession was confused with current execution authority.

# **READY ARTIFACT IS DATA, NOT COMMIT AUTHORITY**

## Safe: explicit adoption by the current owner

The safe path preserves A's artifact as inert data:

```text
artifact state = READY
remote effect_count before adoption = 0
```

B then adopts the exact artifact with one current-owner transaction that binds:

```text
artifact_id
+ exact artifact_digest D
+ state READY
+ adopter = worker-B
+ adopter_fence = 2
+ adopter_version = 2
+ lease still current
```

The adoption affected one row and changed the artifact to:

```text
state = ADOPTED
adopted_by = worker-B
adopted_fence = 2
adopted_version = 2
```

Only then did B publish the consequence, using B's current fencing token:

```text
B / fence 2 / digest D
→ HTTP 200 / applied
→ effect_count = 1
```

A then attempted to publish the same artifact using stale producer token `1`:

```text
presented_fence = 1
highest_fence = 2
→ HTTP 409 / fenced_out
→ effect_count = 1
```

The work survived. The stale authority did not.

## Digest binding

A separate negative test asked B to adopt the artifact under an incorrect digest.

```text
wrong digest
→ adoption updated_rows = 0
→ artifact remains READY
→ external effects = 0
```

Adoption is therefore tied to the exact immutable result, not merely to an artifact ID or stale producer claim.

## Control

A current owner finishing before lease loss can adopt its own READY artifact and commit normally:

```text
current A / fence 1
→ adoption updated_rows = 1
→ HTTP 200 / applied
→ effect_count = 1
```

The protocol does not require handoff when authority never changed.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| A was valid at start and artifact survived takeover as READY data | PASS | 2/2 |
| Implicit stale publish + current publish duplicated one artifact consequence | PASS | 2/2 |
| Explicit adoption bound exact digest to current B epoch | PASS | 2/2 |
| Current B committed once and stale A was fenced | PASS | 2/2 |
| Wrong digest was rejected; current-owner control still worked | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **STALE EXECUTOR MAY PRODUCE DATA; ONLY CURRENT AUTHORITY MAY ADOPT THE CONSEQUENCE**

# **RESULT ADOPTION MUST BIND THE EXACT ARTIFACT DIGEST AND PRODUCER EPOCH TO THE CURRENT OWNER EPOCH**

# **READY ARTIFACT IS DATA, NOT COMMIT AUTHORITY**

# **THE CONSEQUENTIAL COMMIT MUST PRESENT THE ADOPTER'S CURRENT FENCING TOKEN, NOT THE PRODUCER'S STALE TOKEN**

## TTP handoff rule

```text
PRODUCER A / FENCE N
        ↓
COMPUTE
        ↓
OWNERSHIP CHANGES
        ↓
A FINISHES ARTIFACT D
        ↓
READY DATA
        ↓
CURRENT OWNER B / FENCE N+1
        ↓
VERIFY DIGEST + PRODUCER EPOCH + CURRENT OWNER EPOCH
        ↓
ADOPT D
        ↓
COMMIT WITH B'S CURRENT FENCE
        ↓
RESOURCE FENCE CHECK
        ↓
PROVE PRODUCER → ADOPTER → EFFECT
```

## Relationship to #020–#023

```text
#020 → stale worker cannot act after takeover
#021 → stale heartbeat cannot resurrect old ownership
#022 → start authority cannot silently survive to final commit
#023 → stale work may be salvaged as data, but current authority must explicitly adopt its consequence
```

The broader rule becomes:

```text
SAFE RESULT HANDOFF =
  immutable artifact identity
+ producer provenance / epoch
+ explicit current-owner adoption
+ adopter fencing token at commit
+ end-to-end proof
```

## Interpretation boundary

This is a deterministic local protocol benchmark. PostgreSQL is the ownership/adoption authority and a separate Dockerized HTTP service is the protected resource boundary. It does not prescribe a universal distributed scheduler, artifact store, workflow engine or exactly-once protocol.

It does **not** claim a vulnerability in PostgreSQL or another external product, production safety certification, arbitrary distributed mutual exclusion, or arbitrary agent safety.

## Reproducibility

Benchmark: `benchmarks/result-handoff-v1.0/`  
Workflow: `.github/workflows/benchmark-result-handoff.yml`  
Machine-readable result: `reports/verified/023-result-handoff/result.json`  
GitHub Actions: `https://github.com/safal207/RESONANCE/actions/runs/31555333762`

## Verdict

**Worker A lost execution authority but still produced a useful immutable result. Auto-publishing that stale result duplicated the consequence when current owner B later published the same digest. Keeping the artifact inert as READY data, then explicitly adopting the exact digest under B's current ownership epoch and committing with B's fencing token preserved one effect while stale A was rejected with HTTP 409.**

---

**RESONANCE Verified Report #023**  
**Score:** 10/10  
**Unsafe effects:** 2  
**Safe adopted effects:** 1  
**Wrong-digest effects:** 0  
**Vulnerability claim:** No  
**External safety certification:** No
