# TTP Result Handoff / Stale Work Salvage Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #023.

## Problem

A worker can lose execution authority while still producing useful work.

```text
A / fence N starts valid work
      ↓
lease loss / takeover
      ↓
B / fence N+1 becomes current owner
      ↓
A finishes artifact D
```

Discarding every stale worker result wastes computation. Auto-publishing it is unsafe. TTP therefore separates artifact production from adoption and consequential commit.

## New invariants

### I51 — Stale executor may produce data; only current authority may adopt the consequence

Loss of execution authority does not make every produced byte invalid. It does remove the stale worker's right to cause the final external transition.

### I52 — READY artifact is data, not commit authority

A READY artifact SHOULD be inert until a current authority explicitly adopts it.

```text
READY
≠ APPROVED
≠ AUTHORIZED TO COMMIT
```

### I53 — Result adoption must bind exact artifact identity and authority epochs

A safe adoption SHOULD bind at least:

- immutable artifact digest;
- artifact identifier;
- producer identity;
- producer fencing token / version;
- current adopter identity;
- current adopter fencing token / version;
- current lease validity;
- adoption state transition.

A digest mismatch or stale adopter epoch must not silently fall back to implicit acceptance.

### I54 — Consequential commit must use the adopter's current fencing token

The external resource SHOULD evaluate the current adopter epoch. The producer's stale token must not regain authority merely because its result was useful.

## Canonical path

```text
PRODUCE D under A / fence N
          ↓
OWNERSHIP CHANGES
          ↓
D remains READY / inert
          ↓
B / fence N+1 verifies digest + provenance
          ↓
EXPLICIT ADOPTION
          ↓
COMMIT presents B / fence N+1
          ↓
RESOURCE FENCE CHECK
          ↓
PROVE producer → adopter → effect
```

## Proof fields

A handoff proof SHOULD preserve:

- artifact ID and cryptographic digest;
- producer identity, fence and version;
- artifact READY timestamp/state;
- current owner observed at adoption;
- adopter identity, fence and version;
- adoption precondition/result;
- fencing token used at the external commit;
- final effect identity/count/status;
- any stale producer commit attempt and rejection.

## Relationship to #022

#022 says work completion does not preserve commit authority after mid-flight lease loss. #023 adds that the completed work need not be discarded: it may cross the ownership boundary as inert, immutable data and be explicitly adopted by the current owner.

## Interpretation boundary

This rule is synthesized from a deterministic PostgreSQL + local HTTP benchmark. It is not a universal artifact-transfer protocol, exactly-once guarantee, consensus algorithm or production safety certification.
