# PACC v0.7 — ABA Lineage Integrity

This supplement extends cross-saga interference checks from state versioning to causal lineage.

A compensation may be historically valid yet unsafe to apply if the resource has left and later returned to an apparently equivalent state.

```text
value A @ lineage L1
  -> value B @ lineage L2
  -> value A @ lineage L3
```

`value A` returning does not restore `L1`. Likewise, a reused or reset version number does not restore prior ownership.

## Load-bearing distinctions

```text
same value != same causal lineage
same version number != same causal lineage
historical rollback authority != current overwrite authority
lineage ownership != current compensation authority
```

The reference evaluator therefore requires all of the following at compensation use time:

1. current lineage is observable;
2. the durable lineage witness matches the current lineage;
3. the current lineage still matches the lineage owned by the original effect;
4. the current effect binding matches the exact original effect;
5. compensation remains currently authorized;
6. replay/reconciliation semantics remain idempotent.

The ABA mutation campaign falsifies value-equality aliasing, version-equality aliasing, stale lineage witnesses, ignored effect binding, invented lineage evidence, duplicate replay, blind retry, and skipped compensation authority.

Scope: deterministic vendor-neutral reference semantics only; this does not certify an external runtime or product.
