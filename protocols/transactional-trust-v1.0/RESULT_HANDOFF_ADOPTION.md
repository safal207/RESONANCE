# TTP Result Handoff / Stale Work Adoption Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #023.

## Problem

A worker can lose execution authority while still completing useful computation.

```text
A / fence N starts work
       ↓
ownership changes
       ↓
B / fence N+1 becomes current owner
       ↓
A finishes result artifact D
```

The result may still be useful, but A no longer owns the right to publish the consequence.

## New invariants

### I51 — Stale executor may produce data; only current authority may adopt the consequence

Producing an artifact and authorizing a consequential mutation are separate transitions.

```text
artifact produced
≠ effect authorized
```

### I52 — Result handoff must bind artifact digest + producer epoch + current adopter epoch

A safe adoption transition SHOULD bind:

- immutable artifact digest;
- producer identity;
- producer fencing token / execution epoch;
- producer lease version when relevant;
- current adopter identity;
- current adopter fencing token;
- current adopter lease/version validity.

### I53 — Adoption is a new authority transition, not a retroactive extension of producer authority

The current owner does not make the stale producer current again. Instead it creates a new transition:

```text
PRODUCED by stale epoch N
        ↓
ADOPTED by current epoch N+1
```

The adoption record becomes part of the causal evidence for the final effect.

### I54 — Consequential commit must present the current adopter fencing token

The protected resource SHOULD enforce the adopter's current fencing token at the mutation boundary.

A valid adoption record must not let the stale producer publish using its older token.

## Canonical handoff path

```text
AUTHORIZE PRODUCER A / FENCE N
          ↓
RUN WORK
          ↓
OWNERSHIP CHANGES
          ↓
A FINISHES ARTIFACT D
          ↓
STORE D + DIGEST + PRODUCER PROVENANCE
          ↓
NO EXTERNAL EFFECT
          ↓
CURRENT OWNER B OBSERVES D
          ↓
ADOPT D
compare digest + producer epoch + B/current epoch
   ├─ mismatch → REJECT / RECOMPUTE / REVIEW
   └─ match    → ADOPTED
          ↓
COMMIT WITH B / FENCE N+1
          ↓
RESOURCE FENCE CHECK
   ├─ stale → FENCED_OUT
   └─ current → COMMIT
          ↓
PROVE PRODUCER → ADOPTION → EFFECT
```

## Proof fields

A TTP proof bundle for stale-work salvage SHOULD preserve:

- artifact digest / content identity;
- producer worker identity;
- producer fencing token;
- producer lease/version state;
- artifact production time;
- artifact status before adoption;
- adopter identity;
- adopter fencing token and lease version;
- adoption precondition and result;
- adoption identifier/version;
- fencing token presented to the protected resource;
- final effect identity/count/status;
- rejection evidence for digest/epoch mismatch when applicable.

## Relationship to #022–#023

```text
#022:
old worker may finish computation but must re-prove commit authority

#023:
when old worker no longer has commit authority,
its immutable result may be transferred as data to the current owner
through explicit adoption
```

## Interpretation boundary

This rule governs authority/provenance mechanics. It does not prove that a stale artifact is semantically correct, fresh enough for business use, safe to reuse, or equivalent to recomputation. Artifact-level validation may require additional domain-specific invariants before adoption.
