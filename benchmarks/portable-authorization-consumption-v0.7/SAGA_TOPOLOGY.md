# PACC v0.7 — Multi-Step Saga Topology

This layer extends single-effect compensation into a dependency graph.

## Core rule

For a committed causal path:

```text
A -> B -> C(fails before effect)
```

compensation proceeds in reverse causal order:

```text
compensate(B) -> compensate(A)
```

A step whose effect never committed is not compensated.

```text
failed step != committed effect != compensation candidate
```

## Reverse dependency layers

The executable reference model derives compensation as reverse dependency antichains rather than as one arbitrary total order.

For a parallel join:

```text
    B --\
A ------> D(fails)
    C --/
```

with committed effects `A`, `B`, and `C`, the compensation layers are:

```text
{B, C} -> {A}
```

`B` and `C` are independent siblings: either sibling may compensate first, or they may compensate concurrently, because neither is causally reachable from the other. `A` is different: it cannot compensate until both downstream branches are closed or reconciled.

This makes the distinction explicit:

```text
parallel sibling reorder == causally equivalent
upstream-before-downstream reorder != causally equivalent
```

## Barriers

Reverse traversal stops before upstream effects when a downstream layer is unresolved.

Examples:

- `UNKNOWN` compensation outcome -> `RECONCILE_COMPENSATION_REQUIRED`;
- irreversible committed effect -> `PARTIALLY_COMPENSATED_MANUAL_INTERVENTION`;
- missing current compensation authority -> `BLOCK_COMPENSATION_NOT_AUTHORIZED`;
- compensation receipt bound to the wrong original effect -> `BLOCK_COMPENSATION_BINDING`;
- missing durable compensation idempotency identity -> fail closed.

A downstream uncertainty is not permission to continue undoing upstream history:

```text
downstream compensation unresolved
!=
upstream compensation authorized to proceed
```

## Required controls

The baseline pack covers:

1. `A -> B -> C(fail)` -> `B`, then `A`;
2. `B` fails before its effect commits -> compensate only `A`;
3. successful saga with no failure/reversal trigger -> no compensation;
4. irreversible `A` -> compensate downstream reversible steps, then require manual intervention;
5. parallel `B || C` -> same reverse antichain before `A`;
6. unknown downstream compensation -> reconcile before upstream compensation;
7. already-compensated saga replay -> replay receipts, no duplicate effects;
8. wrong compensation binding -> block and stop upstream;
9. missing current compensation authority -> block and stop upstream.

## Mutation campaign

The fail-closed campaign injects eight unsafe semantics:

1. forward compensation order (`A` before `B`);
2. compensate a failed step whose effect never committed;
3. pretend an irreversible step can be automatically undone;
4. compensate a shared ancestor before all parallel downstream branches close;
5. continue upstream after an `UNKNOWN` downstream compensation outcome;
6. emit duplicate compensations during saga replay;
7. ignore compensation-to-original-effect binding;
8. skip current compensation authority.

A ninth candidate is an explicit equivalence control: swapping `B` and `C` within the same reverse antichain is `EQUIVALENT` only after reachability proves neither depends on the other. It is excluded from mutation score.

```text
no observed difference != equivalence
```

Equivalence requires a causal basis.

## Run

```bash
python benchmarks/portable-authorization-consumption-v0.7/run_saga_topology_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_saga_topology_mutation_campaign.py --required-score 1.0
```

The GitHub Actions gate runs both commands as part of `.github/workflows/pacc-composition-integrity.yml` and uploads their machine-readable JSON evidence with the rest of the PACC evidence pack.

This is deterministic reference semantics, not certification of an external saga engine, payment rail, workflow system, or distributed transaction implementation.
