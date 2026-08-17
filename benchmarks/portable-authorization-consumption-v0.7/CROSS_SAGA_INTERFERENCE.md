# Cross-Saga Interference and Stale Rollback

A compensation that was valid for an earlier world-state is not automatically valid against the current world-state.

```text
Saga 1 writes resource v7
  -> later Saga 2 legitimately writes v8
  -> Saga 1 requests compensation
  -> old compensation authority does not imply authority to overwrite v8
```

The reference model requires both current-state checks before a new compensating side effect:

```text
state_witness_version == current_resource_version
expected_resource_version == current_resource_version
current_effect_ref == original_effect_ref
```

If the verify-at-use witness is stale, the verdict is `REVALIDATE_CURRENT_STATE`. If the resource has advanced since the original effect, the verdict is `BLOCK_STALE_COMPENSATION`. If version matches but the current effect identity does not bind the original effect, the verdict is `BLOCK_CURRENT_EFFECT_BINDING`.

Compensation authority remains independent from state compatibility: a current-state match does not create reversal authority. Idempotency and reconciliation also remain load-bearing: committed compensation replays its receipt, unknown compensation outcome blocks another write, and missing durable compensation identity fails closed.

Core distinctions:

```text
authority to compensate
!=
authority to overwrite the current world
```

```text
historically correct rollback target
!=
current rollback target
```

```text
same resource
!=
same resource version/effect ownership
```

The mutation campaign falsifies eight unsafe semantics: blind overwrite of intervening state, stale-witness use, effect-binding omission, compensation-authority omission, duplicate committed compensation, blind retry on unknown outcome, invented current-state witness, and invented compensation identity.

Scope: deterministic reference semantics only; this does not certify any external product, database, payment rail, ledger, or orchestration engine.
