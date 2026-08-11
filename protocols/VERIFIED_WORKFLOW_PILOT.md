# RESONANCE Verified Workflow Pilot v0.1

## Principle

Sell the smallest useful verification step before building a platform.

A pilot is not a generic AI audit. It verifies **one consequential agent workflow** and returns explicit failure paths, invariants, recovery rules and evidence requirements.

## Entry criteria

Prefer one of:

- Product Signal Score 9+;
- explicit request to test or map a workflow;
- a concrete workflow + failure + impact + acceptance condition with clear owner interest.

## Input

One real, safely described agent workflow.

Minimum context:

- actor / agent;
- action;
- initiating intent or authority;
- current state;
- legal transition;
- known failure path;
- recovery behavior;
- authoritative source of truth;
- desired acceptance condition.

## Eight-coordinate review

- **State** — is execution bound to current authoritative state?
- **Causality** — can the action be tied to legitimate initiating intent?
- **Phase** — is the action legal at this workflow stage?
- **Transition** — is the state edge permitted?
- **Time** — is authority/state freshness still valid?
- **Recovery** — what happens under partial/ambiguous failure?
- **Verification** — is the postcondition independently checked?
- **Evidence** — can an independent reviewer reconstruct the material path?

## Deliverables

1. trajectory / state map;
2. explicit failure paths;
3. critical invariants;
4. recovery protocol;
5. verification requirements;
6. evidence requirements;
7. proposed trust contract;
8. prioritized gaps and recommended next step.

## Example

```text
payment attempt
→ timeout
→ unknown commit
→ authoritative reconciliation
→ invariant verification
→ retry OR stop
→ evidence bundle
```

Candidate invariant:

> One authorized payment intent must produce at most one committed payment.

## Success criteria

Success is defined per workflow before execution. A pilot is useful when it can answer:

- which trajectory is currently unsafe or unverifiable;
- which guarantee is missing;
- whether that guarantee can be added using the existing architecture;
- what evidence would demonstrate that the guarantee holds under tested failure scenarios.

## Feedback loop

Pilot evidence returns to the Demand Graph. Repeated missing capabilities may become a protocol, productized service, software/API candidate, or a new RESONANCE article. Client-confidential details are never published without explicit permission.
