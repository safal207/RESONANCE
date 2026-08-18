# PACC Partial Distributed Commit / Coordinator Recovery

This layer verifies recovery after a multi-resource transition crossed only part of its consequential boundary before a crash or coordinator loss.

Core distinction:

```text
joint preconditions valid != all participant effects occurred
coordinator intent != participant commit
coordinator COMMITTED marker != contradictory participant evidence disappears
participant A committed != participant B committed
UNKNOWN participant outcome != NOT_COMMITTED
recovery != replaying every participant write
```

## Reference recovery model

For one logical distributed operation over participants `A` and `B`, recovery requires durable identity and direct participant evidence:

- `operation_id`
- `idempotency_key`
- `commit_set_ref`
- per-participant commit state
- per-participant receipt binding to the exact operation, commit set, and expected effect
- current recovery policy and authority
- current joint-world validity before a complete-forward write

The deterministic states are:

```text
A COMMITTED + B COMMITTED
  -> recover/repair coordinator completion from receipts

A COMMITTED + B NOT_COMMITTED
  -> COMPLETE_FORWARD only after current-world revalidation and current completion authority
  -> or COMPENSATE_PARTIAL only with current compensation authority

A COMMITTED + B UNKNOWN
  -> RECONCILE_PARTICIPANT_REQUIRED
  -> no blind completion
  -> no blind compensation
```

A committed participant is never re-written merely because the coordinator restarted. Already recovered operations replay the durable recovery outcome without another participant side effect.

## Evidence precedence

Direct participant evidence remains load-bearing. A coordinator marker is not allowed to erase a contradictory participant record.

```text
coordinator = COMMITTED
B = NOT_COMMITTED
-----------------
BLOCK_COORDINATOR_EVIDENCE_CONFLICT
```

Likewise, a receipt from another logical operation, commit set, or effect cannot be used to reconstruct the current transition.

## Irreversibility

If the recovery policy is compensation and an already committed participant is marked irreversible, automatic rollback stops at a manual-recovery barrier.

```text
need to restore atomicity != ability to undo every committed effect
```

## Mutation campaign

The campaign attempts to survive by:

- trusting the coordinator marker over participant evidence;
- treating `UNKNOWN` as `NOT_COMMITTED`;
- skipping verify-at-use revalidation before a missing participant write;
- rewriting an already committed participant;
- ignoring participant receipt binding;
- inventing a lost distributed-operation identity;
- compensating without current authority;
- automatically compensating an irreversible participant;
- duplicating a participant write on recovery replay.

CI requires mutation score `1.0` with zero survivors.

Scope remains deterministic reference semantics. Passing this pack does not certify an external database, transaction coordinator, consensus protocol, payment rail, or product as providing atomic distributed commits.
