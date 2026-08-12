# TTP Dependency-Aware Applicability Rule

Status: **Experimental extension to RESONANCE Transactional Trust Protocol v1.0**

Derived from Verified Report #025.

## Problem

A result can remain valid when unrelated state changes, and become invalid when one causal input changes.

```text
artifact D depends on:
  price
  limit

unrelated:
  theme
```

A coarse global version detects that the world changed. It does not by itself prove whether the change matters to this result.

## New invariants

### I59 — State changed does not imply relevant state changed

A transition outside the result's causal dependency set does not automatically invalidate the result.

### I60 — Applicability should bind to the state subgraph that causally justified the result

For consequential state-sensitive work, the result proof SHOULD preserve:

- a declared dependency set;
- dependency values or immutable identities used during computation;
- a stable dependency fingerprint or equivalent state-subgraph identity;
- the rule that maps those dependencies to the result.

### I61 — Global version mismatch may be a conservative signal, not proof of invalidity

A global version is a useful invalidation hint. If efficiency matters, the system MAY refine that signal by comparing the result's causal dependency subgraph.

A refined rule must not silently weaken safety when the dependency model is missing, ambiguous or unverifiable.

### I62 — Relevant dependency drift requires revalidation, recomputation or domain proof before consequence

When the current dependency identity differs from the identity that justified computation, the artifact SHOULD NOT be consequentially adopted without one of:

- revalidation against current dependencies;
- recomputation from current dependencies;
- an explicit domain invariant proving compatibility across the observed dependency transition;
- hold / escalation when applicability remains unknown.

## Canonical path

```text
DECLARE DEPENDENCY SET G
        ↓
CAPTURE DEPENDENCY VALUES
        ↓
COMPUTE FINGERPRINT F(G)
        ↓
COMPUTE ARTIFACT D
        ↓
STATE CHANGES
        ↓
OBSERVE CURRENT G'
        ↓
COMPARE F(G) TO F(G')
   ├─ equal → applicability may survive drift
   ├─ mismatch → REVALIDATE / RECOMPUTE / HOLD
   └─ dependency model unknown → CONSERVATIVE HOLD / BROADER CHECK
        ↓
CURRENT AUTHORITY ADOPTS
        ↓
CURRENT FENCE AT MUTATION BOUNDARY
        ↓
PROVE G → D → APPLICABILITY → ADOPTION → EFFECT
```

## Proof fields

A dependency-aware applicability evidence bundle SHOULD preserve:

- artifact identity/digest;
- declared dependency names/IDs;
- dependency values or immutable state identities captured at computation time;
- dependency fingerprint algorithm/version;
- captured dependency fingerprint;
- current dependency fingerprint;
- global state version before/after when available;
- observed changed fields when available;
- applicability decision and reason;
- adopter identity and authority epoch;
- final resource-side fencing result;
- final effect identity/status.

## Safety boundary

A matching fingerprint proves only that the **declared dependency representation** matches. It does not prove that:

- the dependency set is complete;
- the causal model is correct;
- omitted state cannot affect the result;
- the fingerprint algorithm captures every relevant semantic distinction.

If dependency completeness is not trusted, the implementation SHOULD fall back to broader revalidation or conservative invalidation.

## Relationship to #024–#025

```text
#024:
artifact validity must be checked against current authoritative state

#025:
that check can focus on the causal state subgraph that actually justified the result,
provided the dependency model itself is trustworthy
```

The next unresolved boundary is dependency-model completeness: **a correct fingerprint over an incomplete dependency set may still be unsafe.**
