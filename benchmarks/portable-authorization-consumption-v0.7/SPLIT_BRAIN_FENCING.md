# PACC Coordinator Failover / Split-Brain Fencing

This layer verifies that recovery ownership can move between coordinators without allowing a stale coordinator to keep producing consequential participant effects.

Core distinctions:

```text
coordinator alive != coordinator current
same coordinator identity != same recovery session
recovery authority != fencing authority
fencing authority != current-world validity
pre-takeover check != authority at use
late acknowledgement != permission to regress current recovery state
```

## Recovery epoch and fencing token

Every consequential recovery action carries a durable recovery epoch and fencing token bound to:

- `operation_id`
- `commit_set_ref`
- `coordinator_id`
- recovery `epoch`

The token is checked at consequential use against the current recovery owner.

```text
coord-A owns epoch 7 / fence-7-A
        ↓ takeover
coord-B owns epoch 8 / fence-8-B
        ↓
coord-A may still be running
but any new participant mutation from epoch 7 is fenced
```

A process being alive or holding an old in-memory decision does not preserve recovery ownership.

## Independent boundaries remain independent

A current fencing token does not bypass other PACC boundaries:

- recovery authority must still be current;
- `UNKNOWN` participant outcomes still require reconciliation;
- a stale joint world still requires verify-at-use revalidation;
- an already committed recovery replays idempotently;
- late acknowledgements from older epochs cannot regress coordinator state.

## Fail-closed rules

```text
old epoch -> BLOCK_STALE_RECOVERY_EPOCH
wrong token -> BLOCK_FENCING_TOKEN_MISMATCH
wrong coordinator -> BLOCK_STALE_COORDINATOR
missing fence evidence -> BLOCK_FENCING_EVIDENCE_MISSING
wrong fence binding -> BLOCK_FENCING_BINDING
revoked recovery authority -> BLOCK_RECOVERY_NOT_AUTHORIZED
UNKNOWN participant -> RECONCILE_PARTICIPANT_REQUIRED
stale joint world -> REVALIDATE_DISTRIBUTED_TRANSITION
late stale ack -> IGNORE_STALE_COORDINATOR_ACK
```

## Mutation campaign

The campaign attempts to survive by ignoring epoch, token, coordinator identity, fence binding, current authority, participant uncertainty, replay idempotency, stale acknowledgements, or current-world revalidation, and by inventing missing fencing evidence.

CI requires mutation score `1.0` with zero survivors.

Scope remains deterministic portable reference semantics. Passing this pack does not certify a consensus implementation, distributed lock service, lease manager, database, queue, or transaction coordinator as split-brain safe.
