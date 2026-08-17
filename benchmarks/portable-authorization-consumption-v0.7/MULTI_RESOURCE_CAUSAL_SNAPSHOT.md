# PACC v0.7 — Multi-Resource Causal Snapshot Integrity

This layer extends PACC from single-resource lineage integrity to joint causal state.

Core rule:

```text
each resource individually valid != joint causal snapshot valid
```

A consequential action over resources `A` and `B` may proceed only when the verifier can establish one durable causal snapshot that binds both resources at the same decision boundary.

## Why per-resource freshness is insufficient

A system can observe:

```text
read A from snapshot S1
read B from snapshot S2
```

and find that each value still looks current when checked independently. That does not prove that `{A, B}` ever existed as one coherent causal state. Treating two individually fresh reads as a joint snapshot creates write-skew and mixed-snapshot authority.

## Load-bearing distinctions

```text
A valid now + B valid now != {A,B} jointly valid
same versions != same causal snapshot
same values != same causal snapshot
per-resource witness != joint snapshot witness
causally incomparable != safely mergeable
aggregate snapshot metadata != permission to ignore contradictory resource evidence
vector says EXACT != direct resource versions proved equal
joint snapshot validity != current action authority
unknown prior joint write != safe retry
```

## Reference semantics

The deterministic reference evaluator requires:

1. a durable joint snapshot witness;
2. the same `snapshot_ref` across all resource witnesses;
3. exact version continuity at use time;
4. exact lineage/effect continuity at use time;
5. a non-incomparable causal frontier;
6. direct resource evidence to remain load-bearing even when aggregate/vector metadata claims `EXACT`;
7. current authority for the new joint consequential action;
8. idempotent replay for already committed logical operations;
9. reconciliation before retry when the prior joint outcome is unknown.

The current pack models two resources (`A`, `B`) because two are sufficient to falsify write-skew semantics. The contract generalizes to larger resource sets.

## Falsification campaign

The mutation campaign attempts to survive by:

- validating resources independently;
- ignoring A version drift;
- ignoring B lineage drift;
- accepting incomparable causal clocks;
- inventing a missing joint snapshot;
- accepting mixed snapshot identities;
- skipping current joint-action authority;
- duplicating a committed replay;
- retrying an unknown joint write without reconciliation.

`PACC-SNAP-11` is a deliberate discriminator for evidence precedence: aggregate/vector metadata claims `EXACT`, while direct A-version evidence shows `7 -> 8`. The safe result remains `REVALIDATE_JOINT_SNAPSHOT`; a coarse summary cannot erase contradictory lower-level evidence.

The CI gate requires mutation score `1.0` with zero survivors.

Scope remains deterministic reference semantics. Passing this pack does not certify an external database, transaction manager, runtime, API, or product.
