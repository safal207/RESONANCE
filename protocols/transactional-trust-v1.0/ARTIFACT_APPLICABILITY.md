# TTP Artifact Applicability / Stale-but-Valid Result Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #024.

## Problem

A result artifact can remain perfectly intact and provenance-valid after the authoritative state it was computed from has changed.

```text
capture state S / version V
        ↓
compute artifact D
        ↓
authoritative state changes to S' / V+1
        ↓
D still has valid digest and provenance
```

The artifact may still be useful, but its applicability to the current world is no longer implied.

## New invariants

### I55 — Integrity + provenance does not imply current applicability

Artifact integrity answers **what bytes/result exist**. Provenance answers **where they came from**. Neither alone answers **whether the result is still valid for the current authoritative state**.

### I56 — Adoption must bind the input state that justified computation

For state-sensitive consequential work, an adoption transition SHOULD bind one or more stable applicability coordinates such as:

- input state version;
- immutable input snapshot digest;
- database row/version precondition;
- policy/config version;
- model/tool/data version when materially relevant;
- equivalent domain-specific state identity.

### I57 — State advance after input capture is an applicability transition

A newer state does not universally invalidate every prior artifact. It does invalidate any silent assumption that a previously computed result remains applicable.

```text
state changed
≠ artifact definitely invalid

state changed
= applicability must be re-established
```

### I58 — Stale-but-valid artifact requires revalidation, recomputation, or explicit domain proof before consequence

When the artifact's applicability binding no longer matches current authoritative state, the execution path SHOULD move to one of:

```text
REVALIDATE
RECOMPUTE
PROVE COMPATIBILITY
HOLD / ESCALATE
```

Blind adoption is not sufficient merely because the current owner and artifact digest are valid.

## Canonical applicability path

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
   ├─ still applicable → ADOPT
   └─ mismatch/unknown → REVALIDATE / RECOMPUTE / HOLD
             ↓
CURRENT OWNER ADOPTS
             ↓
COMMIT WITH CURRENT FENCING AUTHORITY
             ↓
PROVE
```

## Version + snapshot identity

Version identifiers are useful but can be insufficient if version discipline is buggy or incomplete. Verified #024 deliberately changed state content while leaving the logical version unchanged. The snapshot digest changed and the applicability-aware adoption rejected the artifact.

A production design may use a different equivalent, but the applicability identity SHOULD be strong enough to distinguish materially different input states.

## Proof fields

A TTP proof bundle for state-sensitive artifact adoption SHOULD preserve:

- artifact digest / immutable content identity;
- producer identity and producer execution epoch;
- input state version;
- input snapshot digest or equivalent input identity;
- artifact production time;
- current authoritative state version;
- current authoritative snapshot identity;
- applicability comparison result;
- compatibility/revalidation evidence when strict equality is not required;
- adopter identity / current fencing token;
- final committed artifact/effect identity;
- recovery/recompute/hold decision.

## Relationship to result handoff

```text
#023 RESULT HANDOFF:
Can current authority safely adopt useful work from a stale producer?

#024 ARTIFACT APPLICABILITY:
Is that exact work still valid for the current authoritative state?
```

These are independent dimensions. A current owner can legally adopt an artifact that is semantically stale unless applicability is checked separately.

## Interpretation boundary

This extension does not mandate strict version equality for every domain. Some results remain valid across state changes. A system may use semantic compatibility rules, dependency graphs, validity intervals or domain-specific invariants instead. The protocol requirement is that applicability be explicit, verifiable and preserved in evidence.
