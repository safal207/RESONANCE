# Portable Authorization Consumption Contract v0.7 (PACC)

PACC verifies the causal composition between authorization proof, current authority, single-use consumption, dispatch, observed outcome, and recovery across crash windows.

It is intentionally separate from FRI. FRI asks whether a primitive is trustworthy at its own boundary. PACC asks whether independently trustworthy boundaries are composed in a safe order and remain safe under concurrency and recovery.

## Causal chain

```text
proof authenticity
  -> current authority
  -> atomic consumption
  -> dispatch binding
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

The executable model records side effects as well as verdicts. This makes order, concurrency, and recovery mutations observable even when a final status alone would otherwise look safe.

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
- unknown dispatch outcome must block blind retry until reconciliation.

## Deterministic concurrency model

The race fixtures intentionally avoid scheduler-dependent thread timing. Both workers can be given the same pre-read (`UNSPENT`), then the reference model deterministically interleaves their consume attempts against one authoritative state transition.

This separates two claims:

```text
both workers observed UNSPENT
!=
both workers may commit consumption
```

The baseline requires an atomic transition. `run_concurrency_mutation_campaign.py` then injects four known-bad semantics:

1. non-atomic check-then-set;
2. duplicate dispatch on idempotent replay;
3. idempotency-key / logical-operation identity omission;
4. loser dispatch after `ALREADY_CONSUMED`.

All scored mutants are required to be killed in CI.

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

The core recovery distinction is:

```text
command/reporting failure
!=
side effect did not happen
```

and:

```text
unknown effect outcome
!=
effect definitely absent
```

## Run

```bash
python benchmarks/portable-authorization-consumption-v0.7/run_composition_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_order_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_concurrency_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_concurrency_mutation_campaign.py --required-score 1.0
python benchmarks/portable-authorization-consumption-v0.7/run_crash_recovery_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_crash_recovery_mutation_campaign.py --required-score 1.0
```

`run_order_mutation_campaign.py` classifies candidates as `KILLED`, `EQUIVALENT`, `SURVIVED`, or `INVALID`. Only explicitly justified equivalence is excluded from the mutation score; unproven no-difference is `SURVIVED` and fails the gate.

The concurrency and crash-recovery campaigns are narrower: each listed mutant is a concrete unsafe semantic variant, so any `SURVIVED` mutant fails the gate.

This benchmark is a deterministic reference semantics pack. It is not a certification of any external product or adapter.
