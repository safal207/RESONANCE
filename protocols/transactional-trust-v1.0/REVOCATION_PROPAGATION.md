# TTP Extension — Revocation Propagation / Authority-View Currentness

## Core law

**VALIDATION AGAINST A STALE AUTHORITY VIEW ≠ CURRENT AUTHORIZATION.**

A consequential verifier may have a locally self-consistent proof registry and still be wrong about current authority because revocation, supersession or authority-generation changes have not propagated yet.

## Canonical rule

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

## I79–I82

### I79 — Validation against a stale authority view ≠ current authorization

Local consistency is not authority currentness. A stale replica can correctly validate an old state that is no longer permitted by the authoritative registry.

### I80 — Revocation propagation is part of the consequence safety boundary

Revocation is not operationally complete merely because the origin accepted it. Consequential verifiers must either receive the update or prove that their local authority view is at least as current as an authoritative monotonic generation.

### I81 — Regional authority views must prove currentness against a monotonic authoritative generation or hold

If `V_local.generation < G_now`, a local `ACTIVE` status is stale evidence. The correct disposition is hold/reconcile, not authorization.

### I82 — Split-brain authority verdicts require fail-closed reconciliation before consequence

If two verifiers disagree because authority state differs, or if currentness cannot be established, downstream consequence must not select the permissive verdict merely because one replica says `ACTIVE`.

## Minimal decision

```text
IF proof.static_bindings_valid
AND local_authority_view.generation >= authoritative_generation
AND local_rule.id == proof.rule_id
AND local_rule.digest == proof.rule_digest
AND local_rule.status == ACTIVE
AND local_rule.generation == proof.rule_generation
AND proof.scope_holds_now
AND current_execution_authority_is_valid
THEN eligible for adoption
ELSE hold / reconcile / reprove / recompute
```

## Why generation matters

A complete revocation payload may arrive later than a compact authoritative head or checkpoint. A monotonic generation lets a verifier detect that its regional registry is stale even before it knows exactly what changed.

```text
local view:
R1 / ACTIVE / generation 7

known authoritative head:
generation 8

7 < 8
→ local ACTIVE state is not current evidence
→ HOLD
```

This is analogous to fencing: freshness is not inferred from a value looking plausible; it is bound to a monotonic authority epoch.

## Relationship to prior TTP rules

```text
MODEL CURRENTNESS
      ↓
MODEL COMPATIBILITY PROOF
      ↓
COMPATIBILITY PROOF AUTHORITY
      ↓
REVOCATION PROPAGATION / AUTHORITY-VIEW CURRENTNESS
      ↓
CURRENT EXECUTION AUTHORITY
      ↓
FENCED CONSEQUENCE
```

A proof can be mathematically valid. Its rule can be revoked. And a verifier can still miss that revocation because its authority view is stale. TTP therefore treats propagation/currentness evidence as part of the proof trajectory.

## Interpretation boundary

This rule does not prescribe a universal replication or consensus mechanism. The authoritative generation may come from a signed checkpoint, quorum-backed registry, strongly consistent metadata service or another domain-specific authority. What matters is that consequential authorization cannot silently rely on a replica known or suspected to be behind current authority.

Verified by RESONANCE Report #030 and `benchmarks/revocation-propagation-v1.0/`.
