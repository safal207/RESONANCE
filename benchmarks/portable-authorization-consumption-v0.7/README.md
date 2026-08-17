# Portable Authorization Consumption Contract v0.7 (PACC)

PACC verifies the causal composition between authorization proof, current authority, single-use consumption, dispatch, observed outcome, recovery across crash windows, external-effect reconciliation, settlement/finality, and compensating reversal actions.

It is intentionally separate from FRI. FRI asks whether a primitive is trustworthy at its own boundary. PACC asks whether independently trustworthy boundaries are composed in a safe order and remain safe under concurrency, recovery, external timeout ambiguity, non-final settlement transitions, and compensation.

## Causal chain

```text
proof authenticity
  -> current authority
  -> atomic consumption
  -> dispatch binding
  -> external effect / reconciliation
  -> accepted
  -> executed
  -> settled
  -> final
  -> outcome binding
```

When execution/settlement produces a reversal condition before stable completion, compensation is a separate causal branch:

```text
executed effect
  -> reversal / settlement-failure trigger
  -> current compensation authority
  -> exact original-effect binding
  -> idempotent compensation dispatch
  -> compensation reconciliation
  -> compensation receipt
```

Normative invariants:

1. Historical proof validity is not current authority.
2. Current authority must be established before consumption.
3. Consumption must succeed atomically before consequential dispatch.
4. Dispatch must bind the exact decision and canonical action digest.
5. Outcome evidence must bind the exact dispatch and decision.
6. A later successful check cannot retroactively legitimize an earlier forbidden side effect.
7. Two workers that both observed `UNSPENT` may not both consume the same authorization.
8. Exactly one atomic consume may create the terminal consumption receipt for a single-use authorization.
9. Only the winning consume may authorize a new dispatch.
10. A retry with the same `logical_operation_id` must replay the committed result without creating another consume or dispatch.
11. A different `logical_operation_id` after consumption must fail as already consumed/conflict.
12. A durable consumption receipt survives process failure and must be reused rather than recreated.
13. A committed dispatch with a lost acknowledgement must replay from durable evidence, not emit another side effect.
14. `dispatch_state=UNKNOWN` is not equivalent to `NOT_SENT`; recovery must reconcile before another consequential effect.
15. Dispatch evidence without the consumption receipt it claims to consume is incomplete recovery evidence and must fail closed.
16. Recovered dispatch evidence must bind the exact durable consumption receipt.
17. A transport timeout is not evidence that the external side effect did not occur.
18. Recovery retry must preserve the same durable idempotency key / logical-operation identity.
19. Canonical external lookup is authoritative for reconciliation in this reference model; webhook delivery is only a notification signal.
20. An unknown external outcome must block blind resend until reconciliation can distinguish existing effect from absent effect.
21. A terminal external failure must not be reinterpreted as permission to create a new logical effect.
22. `ACCEPTED`, `EXECUTED`, `SETTLED`, and `FINAL` are distinct causal stages; none may be silently collapsed into a later stage.
23. `SETTLED` is not finality. A final verdict requires canonical finality evidence bound to the settlement receipt.
24. A status-lookup timeout after execution/settlement must reconcile state, not reissue the consequential effect.
25. Notification/webhook finality cannot override contradictory or incomplete canonical settlement state.
26. Finality evidence bound to the wrong settlement receipt must fail closed.
27. Before finality, a later canonical observation may downgrade an earlier non-final observation; such a downgrade must remain observable rather than being hidden by monotonic-status assumptions.
28. A canonical `FINAL` label without a finality reference is incomplete evidence, not a final outcome.
29. Compensation requires an explicit reversal/failure trigger; absence of a trigger does not authorize an automatic undo.
30. Compensation is a new consequential action and requires current compensation authority even if the original effect was previously authorized.
31. A compensating action must bind the exact original effect it is reversing.
32. Compensation retry must preserve a durable compensation idempotency key / logical-operation identity.
33. A committed compensation with lost acknowledgement must be reconciled from durable evidence rather than emitted again.
34. An unknown compensation outcome must block blind retry until reconciliation resolves whether the compensating effect already happened.
35. Same-operation compensation replay must return the prior compensation receipt without creating another compensation side effect.
36. Missing durable compensation identity must fail closed; recovery may not invent a fresh key and call it the same reversal.

The executable model records side effects, retry attempts, lookup use, receipts, settlement stage, finality verdicts, compensation authority, compensation bindings, and compensating side effects. This makes order, concurrency, recovery, external-boundary, finality, and compensation mutations observable even when a coarse success status alone would otherwise look safe.

## Required negative controls

- revoked authority must not consume;
- already-consumed authorization must not dispatch;
- dispatch without a consumption receipt is invalid;
- mismatched decision/action binding blocks dispatch completion;
- outcome without dispatch/decision binding is incomplete;
- valid proof must not be interpreted as present authority or spendability;
- stale `UNSPENT` reads must not turn check-then-set into two successful consumptions;
- an idempotent replay must not emit a duplicate dispatch;
- omitting logical-operation identity must be detected by replay controls;
- a losing concurrent consume must never dispatch;
- crash after durable consume must not produce a second consumption;
- acknowledgement failure after committed dispatch must not be interpreted as "nothing happened";
- missing consumption evidence must not be guessed from downstream dispatch evidence;
- unknown dispatch outcome must block blind retry until reconciliation;
- timeout must not trigger resend before canonical external lookup;
- retry after canonical not-found must preserve the original idempotency key;
- webhook success must not override contradictory canonical lookup state;
- unknown external outcome must remain `RECONCILE_REQUIRED` rather than cause blind resend;
- `ACCEPTED` must not be treated as `FINAL`;
- `EXECUTED` must not be treated as `SETTLED`;
- `SETTLED` must not be treated as `FINAL`;
- status timeout during settlement/finality must not create a second external effect;
- settlement receipt mismatch must block finality;
- a pre-finality downgrade must not be hidden by a stale higher status;
- a final label without finality evidence must fail closed;
- no reversal/failure trigger must mean no automatic compensation;
- compensation without current authority must block;
- compensation targeting the wrong original effect must block;
- compensation retry must not change idempotency identity;
- acknowledgement loss after committed compensation must not duplicate the reversal;
- unknown compensation outcome must require reconciliation;
- same-operation compensation replay must not emit a second reversal;
- missing compensation idempotency identity must fail closed.

## Deterministic concurrency model

The race fixtures intentionally avoid scheduler-dependent thread timing. Both workers can be given the same pre-read (`UNSPENT`), then the reference model deterministically interleaves their consume attempts against one authoritative state transition.

```text
both workers observed UNSPENT
!=
both workers may commit consumption
```

The baseline requires an atomic transition. `run_concurrency_mutation_campaign.py` injects four known-bad semantics:

1. non-atomic check-then-set;
2. duplicate dispatch on idempotent replay;
3. idempotency-key / logical-operation identity omission;
4. loser dispatch after `ALREADY_CONSUMED`.

## Crash recovery model

Crash recovery distinguishes three dispatch states after durable consumption:

```text
dispatch definitely NOT_SENT
  -> recover the existing consumption receipt
  -> dispatch once

dispatch COMMITTED but acknowledgement lost
  -> replay the durable dispatch result
  -> no new consume or dispatch

dispatch outcome UNKNOWN
  -> RECONCILE_REQUIRED
  -> no blind redispatch
```

The recovery campaign injects four known-bad semantics:

1. re-consume after crash even though consumption is already durable;
2. duplicate dispatch after acknowledgement failure;
3. guess through a missing consumption receipt using downstream evidence;
4. blind dispatch when prior dispatch outcome is unknown.

## External exactly-once boundary

Once a consequential request leaves the local system, local transaction state alone cannot prove whether the external effect occurred. The reference model therefore separates transport outcome from external effect outcome:

```text
request sent
  -> TIMEOUT
  -> canonical lookup
      FOUND_SUCCESS -> reuse external receipt; no resend
      FOUND_FAILED  -> terminal failure; no new logical effect
      NOT_FOUND     -> retry only with the SAME idempotency key
      UNKNOWN       -> RECONCILE_REQUIRED; no blind resend
```

Webhook/event delivery is intentionally modeled as notification rather than canonical authority. A webhook may trigger lookup, but it does not replace lookup in this reference semantics.

The external-effect mutation campaign injects four known-bad semantics:

1. generate a new idempotency key on retry;
2. treat timeout as proof that no external effect happened;
3. blindly resend while external outcome is unknown;
4. treat webhook notification as canonical external state.

Core distinctions:

```text
transport failure
!=
external effect failure
```

```text
notification received
!=
canonical state established
```

```text
retry request
!=
new logical operation
```

## Settlement and finality model

A successful external effect can still be non-final. The reference model therefore keeps four stages distinct:

```text
ACCEPTED
  -> EXECUTED
  -> SETTLED
  -> FINAL
```

The important separation is:

```text
accepted != executed
executed != settled
settled != final
```

Before `FINAL`, a later canonical observation may move backward. A prior `SETTLED` observation followed by canonical `EXECUTED` is recorded as `NON_FINAL_DOWNGRADE_OBSERVED`; it is not silently ignored and it does not authorize a new effect.

Canonical `FINAL` additionally requires:

```text
settlement_receipt == expected_settlement_receipt
and
finality_ref is present
```

The settlement/finality mutation campaign injects six known-bad semantics:

1. treat `ACCEPTED` as `FINAL`;
2. treat `EXECUTED` as `SETTLED`;
3. trust notification/webhook finality instead of canonical state;
4. reissue the external effect after a settlement-status timeout;
5. ignore settlement-receipt binding;
6. ignore a pre-finality downgrade and keep the stale higher state.

Core distinctions:

```text
successful submission
!=
final outcome
```

```text
settlement observation
!=
finality proof
```

```text
prior non-final success
!=
monotonic guarantee
```

## Compensation and reversal model

Compensation is not retroactive cancellation of the original causal history. The original effect remains an observed fact; compensation is a second consequential effect intended to counter or reverse it.

```text
original effect happened
  -> reversal / settlement-failure trigger
  -> current compensation authorization
  -> bind original_effect_ref
  -> canonical compensation lookup
      FOUND_SUCCESS -> replay receipt; no new compensation
      NOT_FOUND     -> emit once with SAME compensation key
      UNKNOWN       -> RECONCILE_COMPENSATION_REQUIRED
```

This creates another important separation:

```text
original effect invalidated/reversed
!=
original effect never happened
```

and:

```text
need to compensate
!=
authority to compensate
```

The compensation mutation campaign injects eight known-bad semantics:

1. compensate without a reversal/failure trigger;
2. skip current compensation authority;
3. ignore binding to the exact original effect;
4. generate a new compensation idempotency key on retry;
5. duplicate compensation after acknowledgement timeout;
6. blindly compensate again while compensation outcome is unknown;
7. emit a duplicate compensation on same-operation replay;
8. invent a compensation identity when durable idempotency evidence is missing.

Core distinctions:

```text
compensation requested
!=
compensation authorized
```

```text
compensation transport failure
!=
compensation effect failure
```

```text
reversal intent
!=
reversal receipt
```

## Run

```bash
python benchmarks/portable-authorization-consumption-v0.7/run_composition_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_order_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_concurrency_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_concurrency_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_crash_recovery_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_crash_recovery_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_external_effect_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_external_effect_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_settlement_finality_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_settlement_finality_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_compensation_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_compensation_mutation_campaign.py --required-score 1.0
```

`run_order_mutation_campaign.py` classifies candidates as `KILLED`, `EQUIVALENT`, `SURVIVED`, or `INVALID`. Only explicitly justified equivalence is excluded from the mutation score; unproven no-difference is `SURVIVED` and fails the gate.

The concurrency, crash-recovery, external-effect, settlement/finality, and compensation campaigns are narrower: each listed mutant is a concrete unsafe semantic variant, so any `SURVIVED` mutant fails the gate.

This benchmark is a deterministic reference semantics pack. It is not a certification of any external product, API, wallet, ledger, chain, payment rail, or adapter.
