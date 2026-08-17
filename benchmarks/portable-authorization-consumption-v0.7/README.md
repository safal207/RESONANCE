# Portable Authorization Consumption Contract v0.7 (PACC)

PACC verifies the causal composition between authorization proof, current authority, single-use consumption, dispatch, observed outcome, recovery across crash windows, and external-effect reconciliation.

It is intentionally separate from FRI. FRI asks whether a primitive is trustworthy at its own boundary. PACC asks whether independently trustworthy boundaries are composed in a safe order and remain safe under concurrency, recovery, and external timeout ambiguity.

## Causal chain

```text
proof authenticity
  -> current authority
  -> atomic consumption
  -> dispatch binding
  -> external effect / reconciliation
  -> outcome binding
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

The executable model records side effects, retry attempts, lookup use, receipts, and verdicts. This makes order, concurrency, recovery, and external-boundary mutations observable even when a final status alone would otherwise look safe.

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
- unknown external outcome must remain `RECONCILE_REQUIRED` rather than cause blind resend.

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
```

`run_order_mutation_campaign.py` classifies candidates as `KILLED`, `EQUIVALENT`, `SURVIVED`, or `INVALID`. Only explicitly justified equivalence is excluded from the mutation score; unproven no-difference is `SURVIVED` and fails the gate.

The concurrency, crash-recovery, and external-effect campaigns are narrower: each listed mutant is a concrete unsafe semantic variant, so any `SURVIVED` mutant fails the gate.

This benchmark is a deterministic reference semantics pack. It is not a certification of any external product, API, wallet, or adapter.
