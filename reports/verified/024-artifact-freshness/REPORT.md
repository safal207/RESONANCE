# RESONANCE Verified Report #024

# Artifact Freshness / Stale-but-Valid Result

**Protocol:** RESONANCE Transactional Trust Protocol v1.0  
**Benchmark:** Artifact Freshness / Stale-but-Valid Result v1.0  
**Database:** PostgreSQL 17.6  
**External boundary:** Dockerized HTTP resource with persistent SQLite effect state  
**GitHub Actions run:** `31581764996`  
**Evidence artifact:** `resonance-artifact-freshness-v1.0`  
**Artifact ID:** `9135437374`  
**Artifact digest:** `sha256:f6a689be4f4c44e59cdb40d6c62459146f6eb10a18a2bc66cc87eb5baf89e8c4`

## Result

# **10 / 10 — Artifact applicability protocol passes**

Verified #023 established that a stale executor can produce useful data and that the current owner can explicitly adopt its consequence. Report #024 asks the next question:

> What if the artifact is perfectly intact and provenance-valid, but the world changed after its inputs were captured?

The benchmark demonstrates a separate trust dimension: **current applicability**.

# **INTEGRITY + PROVENANCE ≠ CURRENT APPLICABILITY**

## Timeline

```text
state v100 / value 10
        ↓
Worker A captures input snapshot
        ↓
AUTHORIZED START
        ↓
A computes artifact D100
output = 20
        ↓
authoritative state advances
v100 → v101 / value 20
        ↓
Worker B becomes current owner / fence 2
        ↓
A finishes D100
integrity_valid = true
        ↓
B considers adoption
```

At the adoption point, the artifact is cryptographically/self-consistently intact for the input it actually used. It is simply no longer a valid answer for the current state.

## Unsafe: correct artifact, wrong world

Artifact D100 preserved:

```text
producer = worker-A
producer_fence = 1
input_state_version = 100
input_snapshot_digest = sha256:a7f43d9c...
artifact_digest = sha256:24d74ba7...
integrity_valid = true
output_value = 20
```

Current authoritative state had already become:

```text
state_version = 101
state_value = 20
snapshot_digest = sha256:b0cae5f0...
current_expected_output = 40
```

Worker B was legitimately current:

```text
owner = worker-B
fence = 2
lease_version = 2
```

The unsafe adoption checked current ownership and artifact identity, but not applicability to current state. PostgreSQL updated one adoption row and B committed the artifact through the protected HTTP boundary:

```text
B / fence 2
artifact input = v100
artifact output = 20
current state = v101
current expected output = 40

→ HTTP 200 / applied
→ effect_count = 1
→ committed_output = 20
```

Nothing was corrupted. The consequence was stale.

## Safe: bind adoption to the input state that justified computation

The safe adoption compares, inside the adoption transaction:

```text
artifact.input_state_version
+ artifact.input_snapshot_digest

against

current authoritative state version
+ current authoritative snapshot digest
```

For D100:

```text
artifact version = 100
current version  = 101

→ applicability_conflict
→ adoption updated_rows = 0
→ external effects = 0
```

The system then recomputed against current state v101:

```text
input_state_version = 101
input_snapshot_digest = sha256:b0cae5f0...
output_value = 40
artifact_digest = sha256:f5fd67c9...
```

B adopted the fresh artifact under its current execution epoch and committed exactly once:

```text
fresh adoption rows = 1
HTTP 200 / applied
final effect_count = 1
final output = 40
```

## Why version alone is not sufficient

The benchmark deliberately includes a broken state-version discipline:

```text
version = 100 / value = 10
        ↓
content changes
        ↓
version = 100 / value = 11
```

The version number stayed the same, but the snapshot digest changed:

```text
original = sha256:a7f43d9c...
mutated  = sha256:c7a08713...
```

Applicability-aware adoption returned:

```text
updated_rows = 0
reason = applicability_conflict
external effects = 0
```

This demonstrates why a strong binding may require both a logical version and immutable snapshot identity (or an equivalent domain-specific state identity).

## Control

When state remained unchanged, adoption succeeded normally:

```text
state version = 100
artifact input version = 100
snapshot digest matches
adoption rows = 1
HTTP 200 / applied
effect_count = 1
output = 20
```

The protocol therefore does not reject old-looking artifacts merely because time passed. It rejects artifacts whose applicability precondition no longer matches the current authoritative state.

## Scorecard

| Check | Result | Score |
|---|---:|---:|
| Artifact integrity/provenance remained valid after state advance | PASS | 2/2 |
| Blind current-owner adoption committed stale output 20 while current expected output was 40 | PASS | 2/2 |
| State-version and same-version snapshot-digest mismatch were rejected | PASS | 2/2 |
| Recompute on v101 adopted and committed current output 40 once | PASS | 2/2 |
| Unchanged-state control succeeded normally | PASS | 2/2 |
| **Total** |  | **10/10** |

## New invariants

# **I55 — INTEGRITY + PROVENANCE DOES NOT IMPLY CURRENT APPLICABILITY**

A valid digest and known producer prove what artifact exists and where it came from. They do not prove that the artifact is still valid for the current authoritative state.

# **I56 — ADOPTION MUST BIND THE INPUT STATE THAT JUSTIFIED COMPUTATION**

For state-sensitive consequential work, adoption SHOULD preserve and compare a state version, snapshot digest, precondition token, or equivalent domain-specific input identity.

# **I57 — STATE ADVANCE AFTER INPUT CAPTURE IS AN APPLICABILITY TRANSITION**

A state change does not automatically make every artifact unusable, but it invalidates any assumption of applicability that has not been re-proved.

# **I58 — STALE-BUT-VALID ARTIFACT REQUIRES REVALIDATION, RECOMPUTATION, OR EXPLICIT DOMAIN PROOF BEFORE CONSEQUENCE**

The safe action after applicability mismatch is not blind commit. It is one of:

- revalidate the result against the current state;
- recompute from the current state;
- prove through domain-specific invariants that the result remains applicable across the observed state transition;
- otherwise hold/escalate.

## TTP artifact-applicability rule

```text
CAPTURE INPUT STATE S / VERSION V / SNAPSHOT H
             ↓
COMPUTE ARTIFACT D
             ↓
VERIFY D INTEGRITY + PRODUCER PROVENANCE
             ↓
OBSERVE CURRENT AUTHORITATIVE STATE S'
             ↓
COMPARE APPLICABILITY BINDING
   ├─ V/H still applicable → ADOPT
   └─ mismatch / unknown   → REVALIDATE / RECOMPUTE / HOLD
             ↓
CURRENT OWNER ADOPTS
             ↓
COMMIT WITH CURRENT FENCE
             ↓
PROVE INPUT → ARTIFACT → APPLICABILITY → ADOPTION → EFFECT
```

## Relationship to #022–#024

```text
#022 → start authority may expire before commit
#023 → useful stale work may survive as inert data and be adopted by current authority
#024 → even correctly adopted data must still be applicable to current authoritative state
```

The broader rule becomes:

```text
SAFE ARTIFACT CONSEQUENCE =
  artifact integrity
+ producer provenance
+ input-state identity
+ current applicability proof
+ current-owner adoption
+ current fencing authority
+ end-to-end evidence
```

## Interpretation boundary

This is a deterministic local protocol benchmark using PostgreSQL state/ownership/adoption records and a separate Dockerized HTTP resource. The computation is intentionally simple (`output = 2 × state_value`) so the stale applicability error is observable.

It does **not** claim:

- that every state-version change invalidates every artifact;
- a universal freshness TTL;
- exactly-once execution;
- production safety certification;
- a vulnerability in PostgreSQL or another external product;
- arbitrary agent safety.

A production system may use semantic compatibility rules instead of strict version equality, but those rules should be explicit, testable and evidenced.

## Reproducibility

Benchmark: `benchmarks/artifact-freshness-v1.0/`  
Workflow: `.github/workflows/benchmark-artifact-freshness.yml`  
Machine-readable result: `reports/verified/024-artifact-freshness/result.json`  
GitHub Actions: `31581764996`

## Verdict

**Worker A produced an integrity-valid artifact against state v100 with output 20. By adoption time the authoritative state was v101 and required output 40. Current owner B could still blindly adopt and commit the stale result because integrity, provenance and authority were all valid while applicability was not. Binding adoption to the input state version and snapshot digest rejected the stale artifact with zero rows; recomputation on v101 then committed the correct output exactly once.**

---

**RESONANCE Verified Report #024**  
**Score:** 10/10  
**Unsafe committed output:** 20 against current expected 40  
**Safe stale-adoption rows:** 0  
**Safe recomputed output:** 40 / one effect  
**Vulnerability claim:** No  
**External safety certification:** No
