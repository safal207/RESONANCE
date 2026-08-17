# Portable Authorization Consumption Contract v0.7 (PACC)

PACC verifies the causal composition between authorization proof, current authority, single-use consumption, dispatch, and observed outcome.

It is intentionally separate from FRI. FRI asks whether a primitive is trustworthy at its own boundary. PACC asks whether independently trustworthy boundaries are composed in a safe order.

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

The executable model records side effects as well as verdicts. This makes order mutations observable even when the final verdict would otherwise look safe.

## Required negative controls

- revoked authority must not consume;
- already-consumed authorization must not dispatch;
- dispatch without a consumption receipt is invalid;
- mismatched decision/action binding blocks dispatch completion;
- outcome without dispatch/decision binding is incomplete;
- valid proof must not be interpreted as present authority or spendability.

## Run

```bash
python benchmarks/portable-authorization-consumption-v0.7/run_composition_conformance.py
python benchmarks/portable-authorization-consumption-v0.7/run_order_mutation_campaign.py --required-score 1.0
```

`run_order_mutation_campaign.py` classifies candidates as `KILLED`, `EQUIVALENT`, `SURVIVED`, or `INVALID`. Only explicitly justified equivalence is excluded from the mutation score; unproven no-difference is `SURVIVED` and fails the gate.

This benchmark is a deterministic reference semantics pack. It is not a certification of any external product or adapter.