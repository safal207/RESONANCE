# Engineering Signal 018 — Recovery Integrity / Projection ≠ Authority ≠ Continuation

**Status:** PROPOSED / EXECUTABLE GENERATION MATRIX — 2026-08-15  
**Lineage:** Signal 014 Persistence Frontier → Signal 015 Durability Frontier → Signal 017 Authority Causality → `openai/codex#26990` recovery discussion  
**Executable contract:** `protocols/recovery-integrity-v0.1/`  
**Authority:** operational memory / routing guidance only; this signal grants no production mutation, deployment, credential, merge, financial, or external-action authority

## Signal

Crash recovery in an agentic system should not be treated as one operation.

Three different questions must remain separate:

```text
1. Does authoritative evidence still exist?
2. Can derived state be rebuilt from it?
3. Is there enough evidence to continue execution safely?
```

The compact rule is:

```text
recoverable data
≠
recoverable projection
≠
safe continuation
```

A system may be able to reconstruct a sidebar, project index, cache, or session view while still lacking enough evidence to resume an agent's execution.

> **Recovery is a state transition that requires evidence, classification, verification, and an explicit decision.**

## Public trigger

`openai/codex#26990` reports a power-loss case where several local stores remained individually readable but described incompatible state.

Publicly reported symptoms include:

- `.codex-global-state.json` collapsing from many projects/pins to a minimal state;
- hundreds of SQLite thread records remaining present;
- rollout/session files remaining locally recoverable;
- project views showing no chats despite underlying records;
- invalid config regression;
- implausible year-7026 timestamps.

A later public architecture comment proposed treating JSON/sidebar state as a rebuildable projection over authoritative durable records, with a shared generation marker and explicit `missing` / `stale` / `corrupt` classification.

A separate recovery tool discussion proposed a narrower rollout-level boundary: recover from rollout evidence without mutating global/SQLite state and fail closed when safe continuation cannot be proven.

These are complementary recovery lanes, not competing ones.

## Recovery topology

```text
                 DURABLE EVIDENCE
        SQLite / append log / rollout history
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
      Projection Recovery       Execution Recovery
             │                       │
   generation / checksum       lineage / committed edge
 missing / stale / corrupt   side effects / continuation proof
             │                       │
             ▼                       ▼
      REBUILDABLE?              FORKABLE?
             └───────────┬───────────┘
                         ▼
                 Recovery Verifier
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ALLOW_REBUILD    ALLOW_FORK         HOLD
```

## Core classification

A recovery verifier should distinguish at least:

```text
HEALTHY
MISSING
STALE
CORRUPT
UNPROVABLE
```

`STALE` is not equivalent to `CORRUPT`.

A readable stale projection may be more dangerous than an obviously corrupt file because it can silently look legitimate while omitting projects, pins, sessions, or newer generations.

## Generation invariant

Where multiple durable stores participate in one logical state, derived projections should carry a generation / commit marker that can be compared with the authoritative store.

```text
authoritative generation N
        ↓
projection generation N
        ↓
sidebar / session index generation N
```

On startup:

```text
validate schema/checksum
        ↓
classify missing / stale / corrupt
        ↓
compare generation with authority
        ↓
rebuild projection when permitted
        ↓
verify reconstructed state
        ↓
commit or hold
```

A minimal/default replacement must not silently become authoritative merely because it parses.

The reverse mismatch is also load-bearing:

```text
authority generation N
projection generation N+1
        ↓
UNPROVABLE
        ↓
HOLD
```

A verifier must not assume the projection is wrong and overwrite apparently newer evidence from an older durable source. The generation contradiction itself becomes evidence requiring reconciliation.

## Evidence-preservation invariant

Recovery code must not destroy the evidence needed to prove whether recovery was correct.

```text
broken projection
        ↓
preserve / quarantine
        ↓
rebuild candidate
        ↓
verify
        ↓
atomic commit
```

The original broken artifact remains separately addressable for diagnostics until the recovery decision is complete.

## Projection invariant

> **If authoritative thread records survive, loss of a disposable projection may increase startup cost but must not redefine whether the underlying record exists.**

This is intentionally narrower than saying every UI feature is reconstructable from every durable source.

Pins, user ordering, or local presentation preferences may require their own durable authority. The contract therefore records which fields are authoritative, derivable, or unavailable rather than inventing missing user intent.

## Continuation invariant

Reconstructing state is not permission to continue execution.

Before an agent is resumed or forked, a separate proof may need to establish:

- session / rollout identity;
- causal lineage;
- last committed action;
- pending or ambiguous action;
- external side effects;
- current authority state;
- replay/idempotency boundary;
- whether the proposed continuation could duplicate an already committed effect.

Therefore:

```text
ALLOW_REBUILD
does not imply
ALLOW_FORK
```

and:

```text
recoverable bytes
does not imply
safe continuation
```

## RecoveryIntegrityRecord

The first contract version records:

```text
recovery_id
source_case_ref

authority:
  source_ref
  generation
  integrity

projection:
  source_ref
  generation
  state

rollout:
  source_ref
  integrity
  continuation_proof

last_committed_action_ref
pending_action_ref
external_side_effect_state

decision:
  rebuild_projection
  execution_continuation

evidence_refs
verifier
pre_recovery_snapshot_ref
post_recovery_snapshot_ref
observed_outcome
```

The key decision split is:

```text
projection decision:
  ALLOW_REBUILD | NO_REBUILD | HOLD

execution decision:
  ALLOW_FORK | NO_CONTINUATION | HOLD
```

## First public fixture — `openai/codex#26990`

The sanitized fixture intentionally makes only claims supported by the public issue and comments.

It classifies the global/UI projection as `STALE`, because the public report describes a readable minimal state that conflicts with surviving SQLite/session evidence.

It permits a projection-rebuild decision in principle because authoritative thread evidence is reported as surviving.

It does **not** claim that execution continuation is proven. The public report is insufficient to establish the exact last committed agent action, pending effects, or safe continuation edge.

Expected result:

```text
projection: STALE
projection decision: ALLOW_REBUILD
execution continuation: HOLD
```

This is the important separation.

## Executable Generation-N matrix

Recovery Integrity v0.1 now includes a deterministic crash-state simulator independent of the Codex fixture.

Canonical cases:

```text
healthy          authority=42 projection=42 → HEALTHY    → NO_REBUILD    / HOLD
stale            authority=42 projection=41 → STALE      → ALLOW_REBUILD / HOLD
corrupt          authority=42 projection=42 + bad digest → CORRUPT → ALLOW_REBUILD / HOLD
split-generation authority=41 projection=42 → UNPROVABLE → HOLD          / HOLD
```

The simulator feeds each generated `RecoveryIntegrityRecord` back through the same semantic validator. The regression suite additionally forces invalid decisions and verifies rejection.

Load-bearing negative controls:

```text
projection generation > authority generation
+ ALLOW_REBUILD
→ REJECT
```

and:

```text
STALE + ALLOW_REBUILD
+ ALLOW_FORK
+ continuation NOT_PROVEN
+ side effects UNKNOWN
+ current authority NOT_PROVEN
→ REJECT ALLOW_FORK
```

This is executable evidence for the decision boundary, not evidence that a vendor implements generation markers today.

## Failure taxonomy additions

Signal 018 adds these working engineering names:

36. **Projection / Authority Conflation** — a derived cache or UI projection becomes a second authority;
37. **Readable / Current Conflation** — parseable state is treated as current state;
38. **Missing / Stale / Corrupt Collapse** — distinct recovery states are all mapped to default initialization;
39. **Recovery / Continuation Conflation** — successful state reconstruction is treated as permission to resume execution;
40. **Evidence-Destructive Repair** — recovery overwrites or deletes the only artifact needed to diagnose or verify the failure;
41. **Generation-Split Acceptance** — stores from incompatible logical generations are accepted because each is locally valid;
42. **Recovered-Authority Resurrection** — a recovered session silently regains mutation authority without revalidating current authority;
43. **Committed-Effect / Retry Ambiguity** — recovery cannot determine whether a pre-crash side effect committed, but still permits replay.

These names are working engineering taxonomy, not an external standard.

## Agent routing rule

For crash, restart, power-loss, corrupted-cache, stale-index, or session-resume tasks:

```text
identify durable evidence
        ↓
classify each store
        ↓
resolve authority vs projection
        ↓
compare generation / causal predecessor
        ↓
preserve disputed artifacts
        ↓
evaluate projection rebuild
        ↓
evaluate execution continuation separately
        ↓
verify candidate recovery
        ↓
commit rebuild / fork / hold
        ↓
record observed outcome separately
```

If the current authority cannot be established, Signal 017's current-owner gate still dominates execution permission.

## Scope boundary

Recovery Integrity v0.1 does not claim:

- that SQLite is always authoritative;
- that rollouts are always sufficient to continue execution;
- that every UI preference is derivable;
- distributed consensus or Byzantine recovery;
- production crash safety for Codex or another vendor;
- adoption or endorsement by OpenAI or Codex Rescue;
- that the public fixture proves a vendor implementation defect beyond the issue's reported evidence.

It defines a falsifiable recovery contract, tests one sanitized public case against that contract, and provides an implementation-independent Generation-N simulation matrix.

## Core rule

```text
authority survives
        ↓
projection may be rebuildable

but

projection rebuilt
        ⇏
execution continuation safe
```

Or more compactly:

> **Recover what can be reconstructed. Continue only what can be proven safe.**

---

Signal 018 is operational memory and routing guidance. Native durable stores remain the evidence layer; recovery verification and execution authorization remain separate.
