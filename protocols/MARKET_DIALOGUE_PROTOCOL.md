# RESONANCE Market Dialogue Protocol v0.1

## Purpose

Turn a reader response into useful product evidence without turning the journal into a hard-sales funnel.

## One-response rule

Every meaningful inbound response gets:

1. **one insight** — classify the failure or missing guarantee;
2. **one compact model** — show the relevant trajectory, invariant or recovery path;
3. **one diagnostic question** — reveal the next missing fact.

Do not send a pitch before the missing capability is explicit.

## Canonical dialogue

```text
HOT QUESTION
  ↓
REAL WORKFLOW
  ↓
CONCRETE FAILURE
  ↓
BUSINESS IMPACT
  ↓
CURRENT WORKAROUND
  ↓
MISSING CAPABILITY
  ↓
MICRO-VALUE
  ↓
TRUST / ACCEPTANCE CONDITION
  ↓
PRODUCT HYPOTHESIS
  ↓
CLIENT VALIDATION
```

## Diagnostic sequence

Use at most one primary question per reply whenever possible.

### Q1 — What happens today?

Identify the actual execution path, not the intended happy path.

### Q2 — Why does it matter?

Find the operational, financial, security, compliance or trust impact.

### Q3 — What stops you solving it?

Separate missing infrastructure from missing process, telemetry, authority, state, API or evidence.

### Q4 — What proves it is solved?

Extract the invariant / acceptance condition.

### Q5 — Would this capability solve the workflow?

Validate the capability hypothesis without over-selling it.

## Example

Inbound:

> Our agent retries a supplier payment after timeout because it cannot determine whether the first request committed.

Useful response pattern:

> This looks like a recovery/state problem rather than primarily a reasoning problem. The dangerous path is `payment → timeout → unknown commit → retry`. I would start with the invariant **one authorized payment intent → at most one committed payment**, with recovery `timeout → reconcile authoritative state → verify → retry or stop → preserve evidence`. What currently prevents your system from guaranteeing that sequence?

## Product Signal gate

Do not offer a pilot until both are explicit:

> The client cannot currently ______ because ______.

> The client considers the problem solved when ______ can be proven.

Recommended pilot threshold: Product Signal Score **9+**, or an explicit request to test/build the capability.

## Safety / privacy

Never request secrets, credentials, private keys, personal data, confidential customer data, production tokens or exploit details. Ask the contributor to generalize identifiers and amounts where necessary.
